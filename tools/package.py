#!/usr/bin/env python3
"""Local package repository tool for the backend monorepo.

Implements doc/local_repository_spec.md: a file-based PEP 503 Simple
Repository used as the local artifact store (the Maven .m2 equivalent).

Repository location: <project root>/.repository by default,
override with the BACKEND_REPOSITORY environment variable.

Commands:
    build       clean build artifacts and run `uv build`
    publish     build, verify and copy artifacts into the local repository
    install     install an artifact from the local repository into a
                temporary venv and verify import / entry points
    list        show packages and versions stored in the repository
    clean       remove build artifacts of a package project, or remove
                non-official versions from the repository
    reindex     regenerate all Simple Repository index.html files
    index-url   print the repository URL and uv configuration snippet

Examples:
    python3 tools/package.py build framework
    python3 tools/package.py publish framework
    python3 tools/package.py install serviceframework==1.0.0
    python3 tools/package.py list
    python3 tools/package.py clean framework
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_SUFFIXES = (".whl", ".tar.gz", ".zip")
ENTRY_POINT_GROUP = "backend.services"
UV = shutil.which("uv")


def fail(message: str, hints: list[str] | None = None) -> None:
    print(f"error: {message}", file=sys.stderr)
    for hint in hints or []:
        print(f"  {hint}", file=sys.stderr)
    sys.exit(1)


def run(command: list[str], cwd: Path | None = None) -> None:
    try:
        subprocess.run(command, cwd=cwd, check=True)
    except FileNotFoundError:
        fail(f"command not found: {command[0]}")
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


def repository_root() -> Path:
    env = os.environ.get("BACKEND_REPOSITORY")
    path = Path(env).expanduser() if env else PROJECT_ROOT / ".repository"
    return path.resolve()


def simple_root() -> Path:
    return repository_root() / "simple"


def ensure_repository() -> None:
    simple_root().mkdir(parents=True, exist_ok=True)


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


_PRE_RELEASE_ORDER = {"dev": 0, "a": 1, "b": 2, "rc": 3}


def version_key(version: str) -> tuple[tuple[int, ...], tuple[int, int]]:
    base = version.strip().lower().split("+")[0]
    match = re.match(r"^(\d+(?:\.\d+)*)", base)
    numbers = tuple(int(part) for part in match.group(1).split(".")) if match else (0,)
    rest = base[match.end() :] if match else base
    tag_match = re.match(r"^\.?(dev|a|b|rc)(\d*)$", rest)
    if tag_match:
        tag = (_PRE_RELEASE_ORDER[tag_match.group(1)], int(tag_match.group(2) or 0))
    elif not rest:
        tag = (4, 0)
    else:
        tag = (-1, 0)
    return numbers, tag


def is_official(version: str) -> bool:
    return version_key(version)[1][0] == 4


@dataclass
class WheelInfo:
    path: Path
    name: str = ""
    version: str = ""
    requires_python: str = ""
    import_packages: list[str] = field(default_factory=list)
    entry_point_groups: list[str] = field(default_factory=list)


def inspect_wheel(path: Path) -> WheelInfo:
    info = WheelInfo(path=path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        metadata_entry = next(
            (n for n in names if re.match(r"^[^/]+\.dist-info/METADATA$", n)), None
        )
        if metadata_entry is None:
            fail(f"no .dist-info/METADATA found inside {path}")
        dist_dir = metadata_entry[: -len("METADATA")]
        metadata: dict[str, str] = {}
        for line in archive.read(dist_dir + "METADATA").decode("utf-8", "replace").splitlines():
            if not line.strip():
                break
            if line[0] in " \t":
                continue
            key, separator, value = line.partition(":")
            if separator:
                metadata[key.strip()] = value.strip()
        info.name = metadata.get("Name", "")
        info.version = metadata.get("Version", "")
        info.requires_python = metadata.get("Requires-Python", "")
        top_level = dist_dir + "top_level.txt"
        if top_level in names:
            info.import_packages = archive.read(top_level).decode("utf-8", "replace").split()
        else:
            top_dirs = {n.split("/", 1)[0] for n in names if n and not n.startswith(dist_dir)}
            info.import_packages = sorted(d for d in top_dirs if f"{d}/__init__.py" in names)
        entry_points = dist_dir + "entry_points.txt"
        if entry_points in names:
            for line in archive.read(entry_points).decode("utf-8", "replace").splitlines():
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    info.entry_point_groups.append(stripped[1:-1])
    if not info.name or not info.version:
        fail(f"cannot read Name/Version metadata from {path}")
    return info


def check_wheel_filename(info: WheelInfo) -> None:
    parts = info.path.name[: -len(".whl")].split("-")
    if len(parts) < 5:
        fail(f"malformed wheel filename: {info.path.name}")
    file_name, file_version = parts[0], parts[1]
    if normalize(file_name) != normalize(info.name) or file_version != info.version:
        fail(
            f"wheel filename does not match its metadata: {info.path.name} "
            f"(metadata: {info.name} {info.version})"
        )


def write_index_html(path: Path, title: str, links: list[tuple[str, str]]) -> None:
    body = "\n".join(
        f'<a href="{html.escape(href)}">{html.escape(text)}</a>' for href, text in links
    )
    path.write_text(
        "<!DOCTYPE html>\n<html>\n"
        f'<head><meta charset="utf-8"><title>{html.escape(title)}</title></head>\n'
        f"<body>\n{body}\n</body>\n</html>\n",
        encoding="utf-8",
    )


def package_dirs() -> list[Path]:
    root = simple_root()
    if not root.is_dir():
        return []
    return sorted(
        (entry for entry in root.iterdir() if entry.is_dir() and not entry.name.startswith(".")),
        key=lambda entry: entry.name,
    )


def regenerate_package_index(package_dir: Path) -> None:
    files = sorted(
        (
            entry
            for entry in package_dir.iterdir()
            if entry.is_file() and entry.name.endswith(ARTIFACT_SUFFIXES)
        ),
        key=lambda entry: entry.name,
    )
    write_index_html(
        package_dir / "index.html", package_dir.name, [(entry.name, entry.name) for entry in files]
    )


def regenerate_root_index() -> None:
    write_index_html(
        simple_root() / "index.html",
        "backend local repository",
        [(f"{entry.name}/", entry.name) for entry in package_dirs()],
    )


def artifact_version(path: Path) -> str | None:
    name = path.name
    for suffix in ARTIFACT_SUFFIXES:
        if name.endswith(suffix):
            stem = name[: -len(suffix)]
            parts = stem.split("-")
            return parts[1] if len(parts) >= 2 else None
    return None


def wheel_versions(package_dir: Path) -> dict[str, Path]:
    versions: dict[str, Path] = {}
    for entry in sorted(package_dir.iterdir()):
        if entry.is_file() and entry.name.endswith(".whl"):
            version = artifact_version(entry)
            if version is not None:
                versions.setdefault(version, entry)
    return versions


def resolve_package_dir(reference: str) -> Path:
    candidate = Path(reference).expanduser()
    if not candidate.is_absolute():
        from_cwd = Path.cwd() / candidate
        from_root = PROJECT_ROOT / candidate
        candidate = from_cwd if (from_cwd / "pyproject.toml").exists() else from_root
    if not (candidate / "pyproject.toml").is_file():
        fail(
            f"{reference} is not a package project (no pyproject.toml under {candidate})",
            hints=[f"examples: framework, services/user, services/order"],
        )
    return candidate.resolve()


def clean_build_artifacts(package_dir: Path) -> list[str]:
    removed: list[str] = []
    for name in ("dist", "build"):
        target = package_dir / name
        if target.exists():
            shutil.rmtree(target)
            removed.append(name)
    for egg_info in package_dir.rglob("*.egg-info"):
        if egg_info.is_dir():
            shutil.rmtree(egg_info)
            removed.append(str(egg_info.relative_to(package_dir)))
    return removed


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


ENTRY_POINT_CHECK_SCRIPT = """
from importlib.metadata import entry_points

group = {group!r}
eps = sorted(entry_points(group=group), key=lambda ep: ep.name)
assert eps, f"no {{group}} entry points installed"
for ep in eps:
    plugin = ep.load()
    print(f"entry point {{ep.name}} -> {{plugin}}")
"""


def verify_installation(
    info: WheelInfo, venv_path: Path | None = None, keep: bool = False
) -> Path:
    temp_dir: str | None = None
    if venv_path is None:
        temp_dir = tempfile.mkdtemp(prefix="backend-package-verify-")
        venv_path = Path(temp_dir) / "venv"
    venv_path = venv_path.expanduser().absolute()
    try:
        run([UV, "venv", str(venv_path)])
        python = venv_python(venv_path)
        run(
            [
                UV,
                "pip",
                "install",
                "--python",
                str(python),
                "--index",
                simple_root().as_uri(),
                f"{info.name}=={info.version}",
            ]
        )
        for import_package in info.import_packages:
            run([str(python), "-c", f"import {import_package}; print('import {import_package}: ok')"])
        if ENTRY_POINT_GROUP in info.entry_point_groups:
            script = ENTRY_POINT_CHECK_SCRIPT.format(group=ENTRY_POINT_GROUP)
            run([str(python), "-c", script])
        print(f"install verification passed: {info.name}=={info.version}")
        return venv_path
    finally:
        if temp_dir and not keep:
            shutil.rmtree(temp_dir, ignore_errors=True)


def build_package(package_dir: Path, clean: bool = True) -> list[Path]:
    if clean:
        clean_build_artifacts(package_dir)
    if UV is None:
        fail("uv is not installed or not on PATH")
    run([UV, "build"], cwd=package_dir)
    dist = package_dir / "dist"
    wheels = sorted(dist.glob("*.whl"))
    if not wheels:
        fail(f"uv build produced no wheel in {dist}")
    return wheels


def cmd_build(args: argparse.Namespace) -> None:
    package_dir = resolve_package_dir(args.package)
    wheels = build_package(package_dir, clean=not args.no_clean)
    for wheel in wheels:
        info = inspect_wheel(wheel)
        print(f"built {info.name} {info.version}: {wheel}")


def cmd_publish(args: argparse.Namespace) -> None:
    package_dir = resolve_package_dir(args.package)
    wheels = (
        sorted((package_dir / "dist").glob("*.whl"))
        if args.no_build
        else build_package(package_dir)
    )
    infos = [inspect_wheel(wheel) for wheel in wheels]
    for info in infos:
        check_wheel_filename(info)
    names = {normalize(info.name) for info in infos}
    versions = {info.version for info in infos}
    if len(names) > 1 or len(versions) > 1:
        fail(f"dist/ contains artifacts of multiple name/version combinations: {names} {versions}")
    info = infos[0]
    if not info.requires_python:
        print("warning: wheel does not declare Requires-Python", file=sys.stderr)
    target_dir = simple_root() / normalize(info.name)
    target_dir.mkdir(parents=True, exist_ok=True)
    artifacts = list(wheels)
    if args.with_sdist:
        artifacts += sorted(
            entry
            for entry in (package_dir / "dist").glob("*.tar.gz")
            if artifact_version(entry) == info.version
        )
    for source in artifacts:
        destination = target_dir / source.name
        if destination.exists():
            if sha256(source) == sha256(destination):
                print(f"already published (identical content): {destination.name}")
                continue
            if is_official(info.version) and not args.force:
                fail(
                    f"{destination.name} already exists with different content; "
                    "published versions are immutable - bump the version "
                    "(or use --force to break the rule deliberately)"
                )
            print(f"warning: replacing non-official artifact {destination.name}")
        shutil.copy2(source, destination)
        print(f"published {destination}")
    regenerate_package_index(target_dir)
    regenerate_root_index()
    print(f"repository: {repository_root()}")
    if args.verify:
        verify_installation(info, venv_path=args.venv, keep=args.keep_venv)
    else:
        print(
            "verify with: "
            f"python3 tools/package.py install {info.name}=={info.version}"
        )


def cmd_install(args: argparse.Namespace) -> None:
    requirement = args.requirement.strip()
    name, _, version = requirement.partition("==")
    name = name.strip()
    version = version.strip() or None
    if not name:
        fail("requirement must look like <package-name>[==<version>]")
    target_dir = simple_root() / normalize(name)
    if not target_dir.is_dir():
        available = ", ".join(entry.name for entry in package_dirs()) or "<empty>"
        fail(f"package '{normalize(name)}' not found in local repository", hints=[f"available: {available}"])
    versions = wheel_versions(target_dir)
    if not versions:
        fail(f"no wheels for {normalize(name)} in local repository")
    if version is None:
        version = max(versions, key=version_key)
        print(f"latest {name} in local repository: {version}")
    elif version not in versions:
        ordered = sorted(versions, key=version_key)
        fail(f"{name}=={version} not in local repository", hints=[f"available: {', '.join(ordered)}"])
    info = inspect_wheel(versions[version])
    venv = Path(args.venv).expanduser() if args.venv else None
    verify_installation(info, venv_path=venv, keep=args.keep_venv)


def cmd_list(_: argparse.Namespace) -> None:
    print(f"repository: {repository_root()}")
    dirs = package_dirs()
    if not dirs:
        print("no packages published")
        return
    for package in dirs:
        versions = wheel_versions(package)
        ordered = sorted(versions, key=version_key) or ["<no wheels>"]
        sdist_count = sum(1 for entry in package.iterdir() if entry.name.endswith(".tar.gz"))
        suffix = f" (+{sdist_count} sdist)" if sdist_count else ""
        print(f"{package.name}: {', '.join(ordered)}{suffix}")


def cmd_clean(args: argparse.Namespace) -> None:
    if not args.repository:
        if not args.package:
            fail("clean needs a package project path (e.g. framework) or --repository")
        package_dir = resolve_package_dir(args.package)
        removed = clean_build_artifacts(package_dir)
        print(f"cleaned {package_dir}: {', '.join(removed) if removed else 'nothing to remove'}")
        return
    root = simple_root()
    removed = 0
    if args.all:
        for package in package_dirs():
            shutil.rmtree(package)
            print(f"removed {package}")
            removed += 1
        regenerate_root_index()
        print(f"cleaned all artifacts from {root} ({removed} packages removed)")
        return
    for package in package_dirs():
        for entry in sorted(package.iterdir()):
            if not entry.is_file() or not entry.name.endswith(ARTIFACT_SUFFIXES):
                continue
            version = artifact_version(entry)
            if version is None or not is_official(version):
                entry.unlink()
                print(f"removed {entry}")
                removed += 1
        regenerate_package_index(package)
    regenerate_root_index()
    print(f"cleaned non-official (dev/pre-release) artifacts from {root} ({removed} removed)")


def cmd_reindex(_: argparse.Namespace) -> None:
    ensure_repository()
    for package in package_dirs():
        regenerate_package_index(package)
        print(f"index updated: {package / 'index.html'}")
    regenerate_root_index()
    print(f"index updated: {simple_root() / 'index.html'}")


def cmd_index_url(_: argparse.Namespace) -> None:
    url = simple_root().as_uri()
    print(url)
    print()
    print("pyproject.toml (consuming project, path relative to its pyproject.toml):")
    print()
    print("  [[tool.uv.index]]")
    print('  name = "backend-local"')
    if repository_root() == (PROJECT_ROOT / ".repository").resolve():
        print('  url = "../../.repository/simple"')
    else:
        print(f'  url = "{url}"')
    print()
    print("or via environment variable:")
    print(f'  export UV_INDEX="{url}"')


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="package.py",
        description="Build and publish packages into the local PEP 503 artifact repository.",
        epilog="Repository location: $BACKEND_REPOSITORY or <project root>/.repository",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="clean and build a package project (uv build)")
    p_build.add_argument("package", help="package project path, e.g. framework, services/user")
    p_build.add_argument("--no-clean", action="store_true", help="skip removing dist/build first")
    p_build.set_defaults(func=cmd_build)

    p_publish = sub.add_parser("publish", help="build and publish artifacts to the local repository")
    p_publish.add_argument("package", help="package project path")
    p_publish.add_argument("--no-build", action="store_true", help="publish existing dist/ as-is")
    p_publish.add_argument("--with-sdist", action="store_true", help="also publish the .tar.gz")
    p_publish.add_argument("--verify", action="store_true", help="run install verification after publishing")
    p_publish.add_argument("--venv", help="verification venv path (default: temporary)")
    p_publish.add_argument("--keep-venv", action="store_true", help="keep the verification venv")
    p_publish.add_argument(
        "--force",
        action="store_true",
        help="allow replacing an already published official version (violates immutability)",
    )
    p_publish.set_defaults(func=cmd_publish)

    p_install = sub.add_parser(
        "install", help="install an artifact from the local repository and verify it"
    )
    p_install.add_argument("requirement", help="e.g. serviceframework==1.0.0 (version optional)")
    p_install.add_argument("--venv", help="target venv path (default: temporary)")
    p_install.add_argument("--keep-venv", action="store_true", help="keep the verification venv")
    p_install.set_defaults(func=cmd_install)

    p_list = sub.add_parser("list", help="list packages and versions in the local repository")
    p_list.set_defaults(func=cmd_list)

    p_clean = sub.add_parser("clean", help="clean build artifacts of a project, or the repository")
    p_clean.add_argument("package", nargs="?", help="package project path")
    p_clean.add_argument(
        "--repository", action="store_true", help="clean the local repository instead"
    )
    p_clean.add_argument(
        "--all", action="store_true", help="with --repository: remove official versions too"
    )
    p_clean.set_defaults(func=cmd_clean)

    p_reindex = sub.add_parser("reindex", help="regenerate all index.html files")
    p_reindex.set_defaults(func=cmd_reindex)

    p_url = sub.add_parser("index-url", help="print repository URL and uv configuration")
    p_url.set_defaults(func=cmd_index_url)

    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    if UV is None:
        fail("uv is not installed or not on PATH")
    args = parse_args(argv)
    ensure_repository()
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
