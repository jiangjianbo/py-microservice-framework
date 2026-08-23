# Python 后端制品构建与本地制品库技术规范

**版本：V1.0**\
**适用范围：** Python 3.12+ 后端项目、Logical Microservice Runtime
及其独立 Service 工程\
**规范范围：** 本规范仅规定 Python Package
的工程结构、构建、版本、发布、本地制品库存储、依赖引用及相关命令。Logical
Microservice Runtime、Service Registry、Transport、Interceptor
等运行时架构不在本规范重复定义。

------------------------------------------------------------------------

## 1. 设计目标

本规范采用"独立 Python Package + 本地文件制品库"的方式管理
Framework、Common 和 Logical Service。

核心原则：

1.  每个 Framework、Common、Service 都是独立 Python Package，拥有独立
    `pyproject.toml`、版本号、依赖声明和构建产物。
2.  Package 构建产物统一使用
    Wheel（`.whl`）作为主要发布制品；需要源码分发时可同时生成 Source
    Distribution（`.tar.gz`）。
3.  本机使用文件系统目录作为 Local Package
    Repository，不部署后台制品库服务。
4.  Local Repository 采用 PEP 503 Simple Repository
    目录规范，保证未来可以平滑迁移到 Nexus、Artifactory、devpi 等真正的
    Package Repository。
5.  业务工程通过 Package Name + Version
    引用制品，不直接依赖其他工程的源码目录。
6.  开发联调可以使用本地 Path / Editable
    Dependency；版本验证、独立构建和发布验证必须使用 Local Repository
    中的 Wheel。
7.  包管理、虚拟环境、依赖解析、构建统一使用 `uv`。
8.  禁止通过 `sys.path`、相对目录导入等方式模拟跨工程依赖。

------------------------------------------------------------------------

## 2. 工程与 Package 的关系

推荐的源码工程结构如下：

``` text
backend/
├── framework/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   └── serviceframework/
│   └── tests/
│
├── common/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   └── backend_common/
│   └── tests/
│
├── services/
│   ├── user/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── src/
│   │   │   └── user_service/
│   │   └── tests/
│   │
│   ├── order/
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── order_service/
│   │   └── tests/
│   │
│   └── ai/
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/
│       │   └── ai_service/
│       └── tests/
│
└── app/
    ├── pyproject.toml
    ├── README.md
    └── src/
        └── backend_app/
```

其中：

  工程                Package 示例              类型
------------------- ------------------------- ---------------------
  `framework/`        `serviceframework`        Framework Package
  `common/`           `backend-common`          Common Package
  `services/user/`    `backend-service-user`    Service Package
  `services/order/`   `backend-service-order`   Service Package
  `services/ai/`      `backend-service-ai`      Service Package
  `app/`              `backend-app`             Application Package

**工程目录名与 Package 名不要求完全一致，但必须在 `pyproject.toml`
中明确声明。**

------------------------------------------------------------------------

## 3. Python Package 标准目录

所有可发布 Package 统一使用 `src` Layout：

``` text
<package-project>/
├── pyproject.toml
├── README.md
├── LICENSE                    # 如适用
├── src/
│   └── <python_import_package>/
│       ├── __init__.py
│       └── ...
└── tests/
    └── ...
```

例如：

``` text
framework/
├── pyproject.toml
├── README.md
├── src/
│   └── serviceframework/
│       ├── __init__.py
│       ├── runtime/
│       ├── registry/
│       ├── proxy/
│       └── ...
└── tests/
```

`src` Layout 是强制规范。禁止把源码直接放在工程根目录：

``` text
framework/
├── serviceframework/
└── pyproject.toml
```

这样做是为了避免测试和开发环境错误地从当前源码目录导入，而无法验证实际安装后的
Package。

------------------------------------------------------------------------

## 4. `pyproject.toml` 基本规范

一个可发布 Package 至少包含：

``` toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "serviceframework"
version = "1.0.0"
description = "Logical Microservice Runtime"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "litestar>=2,<3",
    "pydantic>=2,<3",
]

[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-asyncio>=1",
]

[tool.hatch.build.targets.wheel]
packages = ["src/serviceframework"]
```

实际项目可根据构建后端需要调整，但必须保持标准 PEP 621 项目元数据。

------------------------------------------------------------------------

## 5. Package 命名规范

Package 名称使用小写字母、数字和连字符：

``` text
serviceframework
backend-common
backend-security
backend-service-user
backend-service-order
backend-service-ai
```

Python Import Package 使用下划线：

``` text
serviceframework
backend_common
user_service
order_service
ai_service
```

即：

``` text
Package Name:
backend-service-order

Python Import:
order_service
```

二者允许不同，但必须保持稳定，不得随意修改。

------------------------------------------------------------------------

## 6. 版本规范

统一采用 Semantic Versioning：

``` text
MAJOR.MINOR.PATCH
```

例如：

``` text
1.0.0
1.0.1
1.1.0
2.0.0
```

版本升级规则：

  变更           示例                 版本
-------------- -------------------- -------
  Bug Fix        修复内部 Bug         PATCH
  向后兼容功能   增加 API             MINOR
  不兼容 API     删除/修改 Contract   MAJOR

开发版本可以使用：

``` text
1.2.0.dev1
1.2.0.dev2
```

预发布版本可以使用：

``` text
1.2.0a1
1.2.0b1
1.2.0rc1
```

正式版本不得使用 `SNAPSHOT` 这种 Maven 风格版本号。

------------------------------------------------------------------------

## 7. Service Package 的 Entry Point

Logical Service Package 除了普通 Package Metadata 外，需要通过 Python
Entry Points 声明 Service Plugin。

例如：

``` toml
[project.entry-points."backend.services"]
user = "user_service.service:UserServicePlugin"
```

Order：

``` toml
[project.entry-points."backend.services"]
order = "order_service.service:OrderServicePlugin"
```

AI：

``` toml
[project.entry-points."backend.services"]
ai = "ai_service.service:AIServicePlugin"
```

该配置属于 Service Package 的发布元数据，因此必须随 Wheel 一起发布。

------------------------------------------------------------------------

# 8. 本地制品库定位

本项目不部署专门的 Package Repository Server。

每个开发机、构建机可以拥有独立的 Local Repository：

``` text
当前工程根目录/.repository
```

推荐通过环境变量允许自定义：

``` bash
export BACKEND_REPOSITORY="$HOME/.backend/repository"
```

默认目录：

``` text
当前工程根目录/.repository
```

该目录属于**本机制定义的本地制品库**，不是 `uv` 自身的下载缓存。

二者必须区分：

``` text
当前工程根目录/.repository/
    公司/项目自己的 Package 制品

~/.cache/uv/
    uv 的下载与构建缓存
```

不得将 `uv cache` 当作正式 Package Repository。

------------------------------------------------------------------------

# 9. Local Repository 目录结构

Local Repository 采用 PEP 503 Simple Repository 结构：

``` text
当前工程根目录/.repository
└── simple/
    ├── serviceframework/
    │   ├── index.html
    │   ├── serviceframework-1.0.0-py3-none-any.whl
    │   └── serviceframework-1.1.0-py3-none-any.whl
    │
    ├── backend-common/
    │   ├── index.html
    │   └── backend_common-1.0.0-py3-none-any.whl
    │
    ├── backend-service-user/
    │   ├── index.html
    │   └── backend_service_user-1.0.0-py3-none-any.whl
    │
    └── backend-service-order/
        ├── index.html
        └── backend_service_order-1.0.0-py3-none-any.whl
```

Package Index 的名称必须采用 normalized project name。

例如：

``` text
backend-service-order
```

对应：

``` text
simple/backend-service-order/
```

------------------------------------------------------------------------

# 10. 为什么采用 Simple Repository

本地 Repository 不自定义协议和目录格式，而采用 Python Package Index 的
Simple Repository 规范。

这样当前可以：

``` text
文件系统
    ↓
file://
    ↓
uv
```

未来可以无缝替换成：

``` text
Nexus
Artifactory
devpi
Pulp
其他兼容 PyPI Simple API 的 Repository
```

业务工程中的依赖：

``` toml
dependencies = [
    "serviceframework>=1.0.0",
]
```

无需修改。

变化的只是 Package Index 地址。

------------------------------------------------------------------------

# 11. Wheel 是主要制品

标准构建命令：

``` bash
uv build
```

通常生成：

``` text
dist/
├── serviceframework-1.0.0-py3-none-any.whl
└── serviceframework-1.0.0.tar.gz
```

其中：

``` text
.whl
```

是主要安装和发布制品。

``` text
.tar.gz
```

是 Source Distribution，可作为源码分发或兼容性制品。

内部服务部署原则上优先使用 Wheel。

------------------------------------------------------------------------

# 12. 构建 Package

进入 Package 工程：

``` bash
cd framework
```

创建/同步开发环境：

``` bash
uv sync
```

执行测试：

``` bash
uv run pytest
```

构建：

``` bash
uv build
```

生成：

``` text
dist/
├── serviceframework-1.0.0-py3-none-any.whl
└── serviceframework-1.0.0.tar.gz
```

------------------------------------------------------------------------

# 13. 构建前清理

推荐：

``` bash
rm -rf dist build *.egg-info
uv build
```

如果工程使用标准 `src` Layout，通常只需要清理：

``` text
dist/
build/
*.egg-info/
```

禁止提交这些构建目录到 Git。

`.gitignore` 至少包含：

``` gitignore
.venv/
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

------------------------------------------------------------------------

# 14. 发布到 Local Repository

发布过程不通过 HTTP Server。

推荐实现一个统一脚本或命令：

``` bash
backend package publish
```

其逻辑：

``` text
uv build
    ↓
检查 Wheel
    ↓
读取 Package Name / Version
    ↓
复制 Wheel 到 Local Repository
    ↓
更新 Simple Index
    ↓
完成
```

例如：

``` text
framework/dist/serviceframework-1.0.0-py3-none-any.whl
```

发布后：

``` text
当前工程根目录/.repositorysimple/serviceframework/
└── serviceframework-1.0.0-py3-none-any.whl
```

------------------------------------------------------------------------

# 15. 推荐的发布脚本

第一阶段可以使用简单 Python 脚本实现，不需要额外服务。

例如：

``` text
tools/
└── package.py
```

提供：

``` bash
python tools/package.py build framework
python tools/package.py publish framework
python tools/package.py install serviceframework==1.0.0
python tools/package.py list
python tools/package.py clean
```

后续可以将其封装为：

``` bash
backend package build
backend package publish
backend package install
backend package list
backend package clean
```

------------------------------------------------------------------------

# 16. Local Repository Index

Simple Repository 的最小形式可以直接使用目录中的 Wheel。

如果需要严格遵循 Simple Repository，则每个 Package 目录提供：

``` text
index.html
```

例如：

``` html
<a href="serviceframework-1.0.0-py3-none-any.whl">
    serviceframework-1.0.0-py3-none-any.whl
</a>
```

多个版本：

``` html
<a href="serviceframework-1.0.0-py3-none-any.whl">
    serviceframework-1.0.0-py3-none-any.whl
</a>

<a href="serviceframework-1.1.0-py3-none-any.whl">
    serviceframework-1.1.0-py3-none-any.whl
</a>
```

根目录：

``` text
simple/
```

可以提供 Package 列表：

``` html
<a href="serviceframework/">serviceframework</a>
<a href="backend-common/">backend-common</a>
<a href="backend-service-user/">backend-service-user</a>
```

建议由发布工具自动生成，不允许人工维护。

------------------------------------------------------------------------

# 17. 配置 uv 使用 Local Repository

推荐在项目级 `pyproject.toml` 中配置：

``` toml
[[tool.uv.index]]
name = "backend-local"
url = "file://./.repository/simple"
```

Windows 示例：

``` toml
[[tool.uv.index]]
name = "backend-local"
url = "file://./.repository/simple"
```

不建议把具体用户名写入项目 Git。

因此生产规范中更推荐通过开发机配置或环境变量生成该配置。

------------------------------------------------------------------------

# 18. 本地开发的两种依赖模式

必须明确区分：

### 模式 A：Editable / Path Dependency

适用于 Framework 与 Service 联合开发：

``` text
framework/
    ↑
    │ editable
service-order/
```

例如：

``` toml
[tool.uv.sources]
serviceframework = { path = "../../framework", editable = true }
```

特点：

``` text
修改 framework
    ↓
service-order 立即看到修改
```

适合快速开发和调试。

### 模式 B：Local Repository Dependency

用于验证独立 Package：

``` text
framework
    ↓
uv build
    ↓
Local Repository
    ↓
service-order
    ↓
uv sync
```

特点：

``` text
完全模拟真实独立 Package
```

适合：

-   发布验证
-   CI
-   集成测试
-   版本验证
-   模拟生产环境

------------------------------------------------------------------------

# 19. 不允许使用源码目录作为正式依赖

以下方式禁止作为正式构建方式：

``` python
import sys
sys.path.append("../../framework")
```

或者：

``` bash
PYTHONPATH=../../framework
```

或者业务代码：

``` python
from ../../framework import ...
```

原因是这些方式绕过了 Package Metadata、依赖解析和版本控制。

正式环境必须：

``` text
Package
    ↓
Wheel
    ↓
Package Repository
    ↓
uv
    ↓
Virtual Environment
```

------------------------------------------------------------------------

# 20. Package 依赖声明

Service 必须在自己的 `pyproject.toml` 中声明运行时依赖。

例如：

``` toml
[project]
name = "backend-service-order"
version = "1.0.0"
requires-python = ">=3.12"

dependencies = [
    "serviceframework>=1.0.0,<2.0.0",
    "backend-common>=1.0.0,<2.0.0",
    "sqlalchemy>=2.0,<3.0",
]
```

禁止依赖由上层 Application"偷偷提供"。

例如：

``` text
service-order
    ↓
实际 import sqlalchemy
    ↓
但 pyproject.toml 没有声明 sqlalchemy
```

这种做法禁止。

------------------------------------------------------------------------

# 21. 依赖版本约束

内部 Package 推荐：

``` text
Major 固定兼容边界
Minor / Patch 允许升级
```

例如：

``` toml
"serviceframework>=1.2.0,<2.0.0"
```

而不是：

``` toml
"serviceframework"
```

也不建议大量使用：

``` toml
"serviceframework==1.2.3"
```

除非是最终应用或需要严格锁定版本的部署工程。

最终 Application 应使用 Lock File 锁定完整依赖树。

------------------------------------------------------------------------

# 22. Lock File

使用：

``` bash
uv lock
```

生成：

``` text
uv.lock
```

`uv.lock` 应提交到 Git。

因此：

``` text
pyproject.toml
    = 声明允许的依赖范围

uv.lock
    = 当前环境实际锁定的依赖版本
```

开发环境：

``` bash
uv sync
```

CI：

``` bash
uv sync --locked
```

生产构建同样应使用：

``` bash
uv sync --locked
```

以避免构建时重新解析出不同依赖版本。

------------------------------------------------------------------------

# 23. 本地制品库中的版本策略

Local Repository 允许同时保存多个版本：

``` text
simple/serviceframework/
├── serviceframework-1.0.0-py3-none-any.whl
├── serviceframework-1.1.0-py3-none-any.whl
└── serviceframework-2.0.0-py3-none-any.whl
```

正式版本禁止覆盖。

例如：

``` text
serviceframework-1.0.0.whl
```

发布后不得重新替换成另一个内容不同的 `1.0.0`。

即：

> **同一个 Package Version 必须是不可变制品。**

如果代码发生变化，必须增加版本：

``` text
1.0.0 → 1.0.1
```

------------------------------------------------------------------------

# 24. 本地 Repository 的缓存清理

Local Repository 与 uv Cache 分开管理。

清理 uv Cache：

``` bash
uv cache clean
```

清理本地内部制品：

``` bash
backend package clean
```

但正式版本不得随意删除。

推荐：

``` text
开发版本：
可以清理

正式版本：
默认保留

过期版本：
通过明确的保留策略清理
```

------------------------------------------------------------------------

# 25. 本地 Repository 推荐完整结构

最终建议：

``` text
~/.backend/
├── repository/
│   └── simple/
│       ├── serviceframework/
│       │   ├── index.html
│       │   ├── serviceframework-1.0.0-py3-none-any.whl
│       │   └── serviceframework-1.1.0-py3-none-any.whl
│       │
│       ├── backend-common/
│       │   ├── index.html
│       │   └── backend_common-1.0.0-py3-none-any.whl
│       │
│       ├── backend-service-user/
│       │   ├── index.html
│       │   └── backend_service_user-1.0.0-py3-none-any.whl
│       │
│       └── backend-service-order/
│           ├── index.html
│           └── backend_service_order-1.0.0-py3-none-any.whl
│
└── cache/
    └── # 可选的项目自有缓存
```

`repository/` 是制品库。

`cache/` 不是 Package Repository，可选。

------------------------------------------------------------------------

# 26. 推荐命令规范

开发者最常用命令统一为：

``` bash
# 创建/同步开发环境
uv sync

# 运行测试
uv run pytest

# 构建 Package
uv build

# 更新锁文件
uv lock

# 按锁文件同步
uv sync --locked
```

项目工具进一步封装：

``` bash
# 构建指定 Package
backend package build framework

# 发布到本地制品库
backend package publish framework

# 发布 Service
backend package publish services/order

# 查看本地制品
backend package list

# 安装/验证某个制品
backend package install serviceframework==1.0.0

# 清理构建产物
backend package clean framework
```

------------------------------------------------------------------------

# 27. 标准发布流程

Framework：

``` text
修改代码
   ↓
uv run pytest
   ↓
修改 version
   ↓
uv build
   ↓
检查 Wheel
   ↓
发布到 ~/.backend/repository
   ↓
更新/验证 index
   ↓
完成
```

Service：

``` text
修改代码
   ↓
uv run pytest
   ↓
uv build
   ↓
检查 Entry Point
   ↓
发布 Wheel
   ↓
Application uv lock
   ↓
uv sync --locked
   ↓
Runtime 发现 Service
```

------------------------------------------------------------------------

# 28. 发布前检查

发布工具至少检查：

``` text
[ ] Package Name 正确
[ ] Version 正确
[ ] requires-python 正确
[ ] dependencies 完整
[ ] Wheel 可以生成
[ ] Wheel 可以安装
[ ] Package 可以 import
[ ] Service Entry Point 正确
[ ] 版本未重复
[ ] dist 中无旧制品
```

Service Package 额外检查：

``` text
[ ] backend.services Entry Point 存在
[ ] Plugin 可以加载
[ ] Service Metadata 正确
```

------------------------------------------------------------------------

# 29. 独立 Package 安装验证

发布后不能只验证"Wheel 文件存在"。

必须建立临时环境验证：

``` bash
uv venv /tmp/backend-package-test
```

然后从 Local Repository 安装：

``` bash
uv pip install \
    --index "file:///Users/<user>/.backend/repository/simple" \
    serviceframework==1.0.0
```

再执行：

``` bash
python -c "import serviceframework"
```

Service：

``` bash
python -c "import order_service"
```

Entry Point：

``` bash
python -c "
from importlib.metadata import entry_points
eps = entry_points(group='backend.services')
print(eps)
"
```

只有通过安装验证，才认为 Package 发布成功。

------------------------------------------------------------------------

# 30. CI 构建规则

CI 不应该依赖开发者本机的源码目录。

标准流程：

``` text
Git
 ↓
Checkout
 ↓
uv sync --locked
 ↓
pytest
 ↓
uv build
 ↓
Package Validation
 ↓
Publish Artifact
```

CI 可以把最终 Wheel 作为 CI Artifact 保存。

如果以后接入企业制品库，只需要将：

``` text
Local File Repository
```

替换成：

``` text
Nexus / Artifactory / devpi
```

而 Package 工程本身不需要修改。

------------------------------------------------------------------------

# 31. Monorepo 下的开发方式

虽然各 Package 在同一个 Git Repository 中，但必须保持 Package 边界：

``` text
backend/
├── framework/
├── common/
├── services/
│   ├── user/
│   ├── order/
│   └── ai/
└── app/
```

不能因为处于 Monorepo 就直接跨目录 import。

例如：

``` text
order_service
    ❌ ../../user/src/user_service

order_service
    ✓ backend-service-user Package
```

这样可以保证：

``` text
Monorepo
    ≠
Monolithic Package
```

------------------------------------------------------------------------

# 32. 开发模式与正式模式

推荐定义两种工作模式。

### 快速开发模式

``` text
Service
  ↓
Editable Path Dependency
  ↓
Framework Source
```

适合：

``` text
Framework 与 Service 同时开发
```

### Package 验证模式

``` text
Framework Source
  ↓
Wheel
  ↓
Local Repository
  ↓
Service
```

适合：

``` text
版本验证
独立测试
CI
发布验证
生产模拟
```

正式发布前必须执行一次 Package 验证模式。

------------------------------------------------------------------------

# 33. 从本地 Repository 向企业 Repository 迁移

当前：

``` text
uv
 ↓
file:///.../.backend/repository/simple
```

未来：

``` text
uv
 ↓
https://nexus.example.com/repository/pypi/simple/
```

或者：

``` text
uv
 ↓
https://artifactory.example.com/artifactory/api/pypi/python/simple/
```

Service 的：

``` toml
[project]
dependencies = [
    "serviceframework>=1.0.0,<2.0.0"
]
```

保持不变。

因此 Local Repository 是一种**开发期基础设施形态**，不是 Runtime
的一部分。

------------------------------------------------------------------------

# 34. 规范总结

本项目 Python Package 制品体系最终确定为：

``` mermaid
flowchart TD
    A["Independent Package Project"]
    B["pyproject.toml"]
    C["uv build"]
    D["Wheel"]
    E["Local File Repository"]
    F["uv Dependency Resolution"]
    G["uv.lock"]
    H["Virtual Environment"]
    I["Application / Service"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
```

核心规则可以归纳为：

  项目              规范
----------------- ---------------------------------
  Python            3.12+
  包管理            uv
  Package 元数据    pyproject.toml
  源码布局          src Layout
  主要制品          Wheel
  辅助制品          sdist
  版本              Semantic Versioning
  本地制品库        `当前工程根目录/.repository`
  Repository 格式   PEP 503 Simple Repository
  后台服务          不需要
  Service 注册      Python Entry Points
  依赖解析          uv
  Lock              `uv.lock`
  开发联调          Editable / Path Dependency
  正式验证          Local Repository Wheel
  制品不可变        是
  CI                `uv sync --locked` + `uv build`
  未来企业制品库    Nexus / Artifactory / devpi 等

最终形成：

``` text
独立工程
   ↓
独立 Package
   ↓
独立 Version
   ↓
Wheel Artifact
   ↓
本地文件制品库
   ↓
uv Dependency Resolution
   ↓
独立 Service / Application
```

该制品体系与 Logical Microservice Runtime 解耦。Runtime 只消费已经安装的
Package 和 Entry Point，不负责 Package 构建；Package Repository
只负责保存和提供制品，不负责 Service 运行。
