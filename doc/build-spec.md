# Python Logical Microservice Runtime 构建技术规范

**版本：V1.0**\
**状态：建议作为 Python 后端统一工程规范**\
**适用范围：Python 3.12+ 后端、逻辑微服务、AI
服务、数据安全服务及相关内部基础组件**

------------------------------------------------------------------------

## 1. 规范目标

本规范定义一套基于 **Logical Microservice（逻辑微服务）** 的 Python
后端工程、构建、依赖、制品、运行和横切能力标准。

核心思想是：

> **Service 在代码和依赖层面完全独立，在部署层面与进程解耦。**

一个 Service 从开发阶段开始就是独立 Python Package，拥有自己的
`pyproject.toml`、依赖、测试和版本。Runtime 在启动时自动发现
Service，并根据部署配置决定其采用 InProcess、独立 Process 或 Remote/gRPC
运行。

``` mermaid
flowchart TB
    Dev["Service 独立工程"] --> Build["uv build"]
    Build --> Repo["本地文件制品库"]
    Repo --> Install["uv sync / uv pip install"]
    Install --> Runtime["Logical Microservice Runtime"]

    Runtime --> Registry["Service Registry"]
    Registry --> Stevedore["Stevedore / Entry Points"]

    Runtime --> Proxy["Service Proxy"]
    Proxy --> Local["InProcess Transport"]
    Proxy --> Remote["gRPC Transport"]

    Runtime --> Cross["横切拦截 Pipeline"]
    Cross --> Auth["Authentication / Authorization"]
    Cross --> Audit["Audit"]
    Cross --> Trace["OpenTelemetry"]
    Cross --> DB["SQLAlchemy Interceptor"]
```

本规范不采用"一个 Service 必须对应一个进程"的传统微服务定义，而采用：

``` text
Logical Service ≠ Process ≠ Container ≠ Pod
```

------------------------------------------------------------------------

# 2. 技术栈基线

  ----------------------------------------------------------------------------------------------
  类别                    标准技术                用途
  ----------------------- ----------------------- ----------------------------------------------
  Python                  Python 3.12+            基础运行环境

  Dependency / Build      uv                      依赖解析、虚拟环境、构建、安装

  Project Metadata        pyproject.toml          工程和 Package 定义

  HTTP Framework          Litestar                HTTP/API Adapter

  Service Discovery       Stevedore               Entry Point 自动发现 Service

  Validation / DTO        Pydantic                配置、DTO、参数校验

  ORM                     SQLAlchemy 2.x          数据访问

  RPC                     gRPC                    Remote Service Transport

  Observability           OpenTelemetry           Trace / Metrics / 可观测性

  Package Format          Wheel                   Python 制品

  Local Repository        File-based PEP 503      本机制品存储
                          Simple Repository       

  Runtime                 自研 Logical            Service
                          Microservice Runtime    注册、生命周期、代理、Transport、Interceptor
  ----------------------------------------------------------------------------------------------

原则上不引入后台制品仓库服务。开发机本地制品采用文件系统目录保存，定位类似
Maven 的 `~/.m2/repository`。

------------------------------------------------------------------------

# 3. 总体工程模型

推荐采用 Monorepo 组织多个独立 Package：

``` text
backend/
├── framework/
├── common/
├── services/
│   ├── user/
│   ├── order/
│   ├── data/
│   └── ai/
├── app/
└── docs/
```

其中每一个以下目录都是独立 Python Package：

``` text
framework/
common/
services/user/
services/order/
services/data/
services/ai/
app/
```

它们可以：

1.  独立构建；
2.  独立测试；
3.  独立声明依赖；
4.  独立发布版本；
5.  被其他工程通过 Package 依赖；
6.  在本地以 editable dependency 联调；
7.  从本地制品库安装固定版本。

------------------------------------------------------------------------

# 4. 标准目录结构

完整推荐结构：

``` text
backend/
│
├── pyproject.toml                    # Workspace 根配置
├── uv.lock                           # Workspace 锁文件
├── README.md
│
├── framework/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   └── serviceframework/
│   │       ├── __init__.py
│   │       ├── contract/
│   │       │   ├── service.py
│   │       │   ├── context.py
│   │       │   ├── metadata.py
│   │       │   └── errors.py
│   │       ├── runtime/
│   │       │   ├── runtime.py
│   │       │   └── lifecycle.py
│   │       ├── registry/
│   │       │   ├── registry.py
│   │       │   └── stevedore_registry.py
│   │       ├── proxy/
│   │       │   ├── proxy.py
│   │       │   └── factory.py
│   │       ├── transport/
│   │       │   ├── base.py
│   │       │   ├── local.py
│   │       │   └── grpc.py
│   │       ├── interceptor/
│   │       │   ├── base.py
│   │       │   ├── authentication.py
│   │       │   ├── authorization.py
│   │       │   ├── audit.py
│   │       │   └── tracing.py
│   │       ├── web/
│   │       │   ├── application.py
│   │       │   └── adapter.py
│   │       ├── database/
│   │       │   └── interceptor.py
│   │       ├── config/
│   │       ├── observability/
│   │       └── exceptions/
│   └── tests/
│
├── common/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   └── backend_common/
│   │       ├── database/
│   │       ├── cache/
│   │       ├── security/
│   │       ├── events/
│   │       ├── models/
│   │       ├── errors/
│   │       └── utils/
│   └── tests/
│
├── services/
│   ├── user/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── src/
│   │   │   └── user_service/
│   │   │       ├── __init__.py
│   │   │       ├── service.py
│   │   │       ├── domain/
│   │   │       ├── application/
│   │   │       ├── infrastructure/
│   │   │       └── api/
│   │   └── tests/
│   │
│   ├── order/
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── order_service/
│   │   └── tests/
│   │
│   ├── data/
│   └── ai/
│
├── app/
│   ├── pyproject.toml
│   ├── src/
│   │   └── backend_app/
│   │       ├── main.py
│   │       └── config.py
│   └── tests/
│
├── proto/
│   └── *.proto
│
├── scripts/
│   ├── build.py
│   ├── publish-local.py
│   └── clean.py
│
└── docs/
    └── architecture/
```

------------------------------------------------------------------------

# 5. Package 职责边界

## 5.1 framework

`framework` 是整个后端 Runtime 的基础框架，不包含具体业务。

职责：

``` text
Service Contract
Service Registry
Service Discovery
Service Proxy
Transport
Lifecycle
DI
Interceptor
Litestar Adapter
gRPC Adapter
OpenTelemetry Integration
```

禁止依赖具体业务 Service。

------------------------------------------------------------------------

## 5.2 common

`common` 是跨 Service 的公共基础库。

允许：

``` text
database/
cache/
security/
events/
models/
errors/
utils/
```

禁止：

``` text
common/user/
common/order/
common/ai/
```

除非该内容确实是跨多个业务域共享的稳定抽象。

严格禁止：

``` text
common → concrete service
```

否则 Common 会逐渐演变成第二个 Monolith。

------------------------------------------------------------------------

## 5.3 services

每个 Service 都是独立 Package。

Service 可以依赖：

``` text
service → framework
service → common
service → external libraries
```

禁止：

``` text
service A → service B implementation
```

Service-to-Service 调用必须通过 Service Contract + Service Proxy。

------------------------------------------------------------------------

## 5.4 app

`app` 是最终应用组合工程。

职责：

``` text
加载 Runtime
加载 Service
读取部署配置
启动 Litestar
启动 Runtime Lifecycle
```

`app` 可以依赖所有需要实际运行的 Service。

------------------------------------------------------------------------

# 6. Service 内部结构

Service 内部推荐采用 DDD/分层结构：

``` text
services/order/
├── pyproject.toml
├── src/
│   └── order_service/
│       ├── service.py
│       ├── domain/
│       │   ├── entities.py
│       │   ├── value_objects.py
│       │   └── services.py
│       ├── application/
│       │   ├── commands.py
│       │   ├── queries.py
│       │   └── service.py
│       ├── infrastructure/
│       │   ├── repository.py
│       │   └── models.py
│       └── api/
│           ├── controller.py
│           └── dto.py
└── tests/
```

依赖方向：

``` mermaid
flowchart LR
    API["API"] --> APP["Application"]
    APP --> DOMAIN["Domain"]
    INFRA["Infrastructure"] --> DOMAIN
    APP --> INFRA
```

Domain 不依赖 API、Litestar、SQLAlchemy 等基础设施。

------------------------------------------------------------------------

# 7. pyproject.toml 规范

每一个 Package 必须拥有独立 `pyproject.toml`。

示例：

``` toml
[project]
name = "backend-service-order"
version = "1.0.0"
description = "Order logical microservice"
requires-python = ">=3.12"

dependencies = [
    "serviceframework>=1.0.0",
    "backend-common>=1.0.0",
    "sqlalchemy>=2.0",
    "pydantic>=2.0",
]

[project.entry-points."backend.services"]
order = "order_service.service:OrderServicePlugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Service 的 Entry Point 是 Runtime 自动发现 Service 的标准入口。

------------------------------------------------------------------------

# 8. Entry Point 规范

统一 Namespace：

``` text
backend.services
```

示例：

``` toml
[project.entry-points."backend.services"]
user = "user_service.service:UserServicePlugin"
order = "order_service.service:OrderServicePlugin"
```

Runtime 使用 Stevedore：

``` python
from stevedore.extension import ExtensionManager

manager = ExtensionManager(
    namespace="backend.services",
    invoke_on_load=True,
)

for extension in manager:
    service = extension.obj
    runtime.register(service)
```

因此：

``` text
Package 安装
    ↓
Python Entry Point
    ↓
Stevedore Discovery
    ↓
Service Registry
    ↓
Runtime
```

Service Framework 不允许硬编码：

``` python
import user_service
import order_service
```

------------------------------------------------------------------------

# 9. Service Contract

Service Contract 定义业务能力，不定义 Transport。

推荐使用 Protocol：

``` python
from dataclasses import dataclass
from typing import Protocol


@dataclass
class User:
    id: int
    name: str


class UserService(Protocol):

    async def get_user(self, user_id: int) -> User:
        ...

    async def create_user(self, name: str) -> User:
        ...
```

Contract 禁止直接依赖：

``` text
Litestar
FastAPI
gRPC
SQLAlchemy
HTTP
```

Contract 表达：

> "能够做什么"。

Transport 表达：

> "怎么调用"。

------------------------------------------------------------------------

# 10. Runtime 核心抽象

Runtime 至少包含：

``` text
ServiceRegistry
ServiceRuntime
ServiceProxy
Transport
ServiceInterceptor
LifecycleManager
```

推荐接口：

``` python
class ServiceRuntime:

    def register(self, service):
        ...

    def resolve(self, service_type):
        ...

    async def start(self):
        ...

    async def stop(self):
        ...
```

------------------------------------------------------------------------

# 11. Service Proxy

所有 Service-to-Service 调用必须经过 Proxy。

``` python
class ServiceProxy:

    def __init__(self, transport):
        self.transport = transport

    async def invoke(self, method, *args, **kwargs):
        return await self.transport.invoke(
            method,
            *args,
            **kwargs,
        )
```

业务代码只能依赖 Contract/Proxy，不允许直接获取 Remote Endpoint。

------------------------------------------------------------------------

# 12. Transport

Transport 是部署位置和业务 Service 之间的隔离层。

标准 Transport：

``` text
Transport
├── LocalTransport
└── GrpcTransport
```

接口：

``` python
class Transport(Protocol):

    async def invoke(
        self,
        method: str,
        *args,
        **kwargs,
    ):
        ...
```

Local：

``` text
ServiceProxy
    ↓
LocalTransport
    ↓
Python Method Call
```

Remote：

``` text
ServiceProxy
    ↓
GrpcTransport
    ↓
gRPC
    ↓
Remote Runtime
```

------------------------------------------------------------------------

# 13. InProcess 运行规范

开发环境默认使用：

``` yaml
runtime:
  mode: inprocess
```

Service 配置：

``` yaml
services:
  user:
    mode: inprocess

  order:
    mode: inprocess

  ai:
    mode: inprocess
```

最终：

``` text
One Process
├── Runtime
├── User Service
├── Order Service
└── AI Service
```

适合：

``` text
开发
调试
单元测试
低流量
轻量 Service
```

------------------------------------------------------------------------

# 14. Remote 运行规范

需要拆分时：

``` yaml
services:
  user:
    mode: inprocess

  order:
    mode: inprocess

  ai:
    mode: remote
    endpoint: ai-service:50051
```

Service 代码不改变。

只有：

``` text
LocalTransport
```

切换为：

``` text
GrpcTransport
```

------------------------------------------------------------------------

# 15. 依赖规则

允许：

``` text
framework → common
service → framework
service → common
app → framework
app → common
app → service
```

禁止：

``` text
common → service
framework → concrete service
service A → service B implementation
```

Service-to-Service：

``` text
Service A
    ↓
Contract
    ↓
Service Proxy
    ↓
Transport
    ↓
Service B
```

------------------------------------------------------------------------

# 16. 本地 Package Repository

本项目不要求部署后台制品仓库服务。

开发机采用文件系统目录作为本地 Python Artifact Repository，定位类似：

``` text
~/.m2/repository
```

统一目录：

``` text
~/.backend/
└── repository/
    └── simple/
```

推荐使用 PEP 503 Simple Repository 结构。

完整示例：

``` text
~/.backend/repository/
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

不需要：

``` text
Nexus
Artifactory
devpi
Pypiserver
```

后台服务。

------------------------------------------------------------------------

# 17. Local Repository 的职责

本地 Repository 只保存：

``` text
公司内部 Package
稳定版本
开发构建版本
测试版本
```

不要把它当成 uv 下载缓存。

二者概念不同：

``` text
~/.backend/repository/
    = 内部 Package Repository

uv cache
    = 第三方依赖下载缓存
```

------------------------------------------------------------------------

# 18. Package 构建

首先安装 uv：

``` bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

检查：

``` bash
uv --version
python --version
```

要求：

``` text
Python >= 3.12
```

构建 Package：

``` bash
cd framework
uv build
```

结果：

``` text
dist/
├── serviceframework-1.0.0-py3-none-any.whl
└── serviceframework-1.0.0.tar.gz
```

生产安装优先使用：

``` text
.whl
```

------------------------------------------------------------------------

# 19. 发布到本地 Repository

可以先构建：

``` bash
uv build
```

然后将 Wheel 放入：

``` text
~/.backend/repository/simple/serviceframework/
```

例如：

``` text
~/.backend/repository/simple/serviceframework/
└── serviceframework-1.0.0-py3-none-any.whl
```

如果需要标准化操作，应提供项目级脚本：

``` bash
python scripts/publish-local.py framework
```

脚本负责：

``` text
清理 dist
    ↓
uv build
    ↓
检查版本
    ↓
复制 wheel
    ↓
更新 simple index
```

------------------------------------------------------------------------

# 20. Local Repository Index

`index.html`：

``` html
<!DOCTYPE html>
<html>
<body>
<a href="../../serviceframework-1.0.0-py3-none-any.whl">
serviceframework-1.0.0-py3-none-any.whl
</a>
</body>
</html>
```

Package 名称目录统一使用规范化名称。

例如：

``` text
backend-common
```

对应：

``` text
backend-common/
```

Python distribution name 与 import package name 可以不同：

``` text
Distribution:
backend-common

Import:
backend_common
```

------------------------------------------------------------------------

# 21. uv 使用本地 Repository

在 `pyproject.toml` 中配置：

``` toml
[[tool.uv.index]]
name = "local"
url = "file:///Users/<user>/.backend/repository/simple"
```

Linux：

``` toml
[[tool.uv.index]]
name = "local"
url = "file:///home/<user>/.backend/repository/simple"
```

然后：

``` bash
uv sync
```

或者：

``` bash
uv add serviceframework==1.0.0
```

解析时从本地 Repository 获取 Package。

------------------------------------------------------------------------

# 22. 临时使用本地 Wheel

不修改工程配置时，可以直接：

``` bash
uv pip install \
    --find-links ~/.backend/repository/simple \
    serviceframework==1.0.0
```

适合：

``` text
临时测试
问题定位
本地验证
```

正式工程依赖仍建议通过 `pyproject.toml` 管理。

------------------------------------------------------------------------

# 23. 第三方依赖与内部依赖

推荐：

``` text
Internal Package
    ↓
Local Repository

External Package
    ↓
PyPI
```

例如：

``` toml
dependencies = [
    "serviceframework>=1.0.0",
    "backend-common>=1.0.0",
    "litestar>=2.0",
    "sqlalchemy>=2.0",
    "pydantic>=2.0",
]
```

解析逻辑：

``` text
serviceframework
backend-common
    ↓
Local Repository

litestar
sqlalchemy
pydantic
    ↓
PyPI / configured external index
```

如果公司未来部署 Nexus/Artifactory，只需要改变 Index 配置，工程 Package
依赖不变。

------------------------------------------------------------------------

# 24. 本地开发：Editable Dependency

在 Monorepo 内开发 Framework 和 Service 时，推荐使用 Workspace。

例如：

``` text
backend/
├── framework/
└── services/
    └── order/
```

开发期间：

``` text
order → framework
```

可以采用 editable dependency。

修改：

``` text
framework/src/serviceframework/
```

后，Order Service 立即使用最新代码，无需反复构建 Wheel。

适用于：

``` text
框架开发
Service 联调
Bug 调试
```

------------------------------------------------------------------------

# 25. 固定版本测试

为了模拟真正独立工程，必须支持：

``` text
Service Order
    ↓
serviceframework==1.2.0
    ↓
Local Repository
```

此时不使用 editable dependency。

流程：

``` bash
uv build framework
```

发布：

``` text
~/.backend/repository/simple/serviceframework/
```

然后：

``` bash
cd services/order
uv sync
```

这样可以验证：

> Service 是否真正能够脱离 Framework 源码运行。

这是发布前必须执行的测试。

------------------------------------------------------------------------

# 26. 版本规范

采用 Semantic Versioning：

``` text
MAJOR.MINOR.PATCH
```

例如：

``` text
1.0.0
1.1.0
1.1.1
2.0.0
```

规则：

  变更                    版本
  ----------------------- -------
  Bug 修复                PATCH
  向后兼容的新能力        MINOR
  不兼容 API / Contract   MAJOR

Service Contract 一旦发布，不允许在 PATCH/MINOR 版本中破坏兼容性。

------------------------------------------------------------------------

# 27. Service 版本与 Runtime 版本

Service Framework：

``` text
serviceframework 1.5.0
```

Service：

``` text
backend-service-order 2.3.0
```

二者版本独立。

例如：

``` toml
dependencies = [
    "serviceframework>=1.4,<2.0",
]
```

Service 不应该绑定：

``` text
serviceframework==1.4.0
```

除非存在严格的兼容性要求。

------------------------------------------------------------------------

# 28. Lock File

应用工程必须生成：

``` text
uv.lock
```

用于锁定完整依赖树。

典型结构：

``` text
pyproject.toml
uv.lock
```

其中：

``` text
pyproject.toml
    = 直接依赖声明

uv.lock
    = 实际解析后的完整依赖版本
```

开发、测试、CI 环境统一执行：

``` bash
uv sync --locked
```

避免不同机器解析出不同依赖版本。

------------------------------------------------------------------------

# 29. 常用命令规范

## 29.1 创建工程

``` bash
uv init
```

创建 Package：

``` bash
uv init --package service-order
```

------------------------------------------------------------------------

## 29.2 创建虚拟环境

``` bash
uv venv
```

------------------------------------------------------------------------

## 29.3 安装依赖

``` bash
uv sync
```

------------------------------------------------------------------------

## 29.4 添加依赖

``` bash
uv add litestar
uv add sqlalchemy
uv add pydantic
```

开发依赖：

``` bash
uv add --dev pytest
uv add --dev pytest-asyncio
```

------------------------------------------------------------------------

## 29.5 删除依赖

``` bash
uv remove package-name
```

------------------------------------------------------------------------

## 29.6 更新依赖

``` bash
uv lock --upgrade
```

或者：

``` bash
uv sync --upgrade
```

------------------------------------------------------------------------

## 29.7 运行程序

``` bash
uv run python -m backend_app
```

或者：

``` bash
uv run litestar run
```

------------------------------------------------------------------------

## 29.8 执行测试

``` bash
uv run pytest
```

指定测试：

``` bash
uv run pytest tests/test_user.py
```

------------------------------------------------------------------------

## 29.9 构建 Package

``` bash
uv build
```

指定 Package：

``` bash
cd framework
uv build
```

------------------------------------------------------------------------

## 29.10 检查 Package

``` bash
uv run python -m build
```

或者直接检查：

``` bash
unzip -l dist/*.whl
```

------------------------------------------------------------------------

# 30. 推荐统一命令

项目根目录建议提供：

``` bash
make build
make test
make lint
make package
make publish-local
make clean
```

或者提供统一 CLI：

``` bash
backend build
backend test
backend lint
backend package build
backend package publish
backend package list
backend package clean
backend service list
backend service inspect
backend runtime run
```

其中：

``` text
backend package publish
```

负责发布到：

``` text
~/.backend/repository/
```

而：

``` text
backend runtime run
```

负责：

``` text
发现 Service
    ↓
加载 Service
    ↓
创建 Runtime
    ↓
注册 Interceptor
    ↓
启动 Litestar
```

------------------------------------------------------------------------

# 31. Service Demo

最小 User Service：

``` text
services/user/
├── pyproject.toml
├── src/
│   └── user_service/
│       ├── service.py
│       ├── repository.py
│       └── api.py
└── tests/
```

`repository.py`：

``` python
class UserRepository:

    async def find(self, user_id: int):
        return {
            "id": user_id,
            "name": "Alice",
        }
```

`service.py`：

``` python
class UserService:

    def __init__(self, repository):
        self.repository = repository

    async def get_user(self, user_id: int):
        return await self.repository.find(user_id)
```

`api.py`：

``` python
from litestar import get


@get("/users/{user_id:int}")
async def get_user(
    user_id: int,
    service: UserService,
):
    return await service.get_user(user_id)
```

最终业务开发者主要关心：

``` text
Domain
Application
Repository
API
```

而不需要关心：

``` text
Service Discovery
HTTP Server
gRPC
Authentication
Tracing
Audit
Lifecycle
```

------------------------------------------------------------------------

# 32. 横切拦截架构

横切能力必须由 Runtime 统一管理。

禁止在业务代码中大量出现：

``` python
check_login()
check_permission()
write_audit()
start_trace()
```

统一结构：

``` mermaid
flowchart TB
    Request["HTTP Request"] --> ID["Request ID"]
    ID --> Trace["Trace Context"]
    Trace --> Auth["Authentication"]
    Auth --> Permission["Authorization"]
    Permission --> Audit["Audit"]
    Audit --> Service["Service Interceptor"]
    Service --> Proxy["Service Proxy"]
    Proxy --> Transport["Local / gRPC"]
    Transport --> Business["Business Service"]
    Business --> Repository["Repository"]
    Repository --> DBI["SQLAlchemy Interceptor"]
    DBI --> DB["Database"]
```

------------------------------------------------------------------------

# 33. Service Interceptor

统一定义：

``` python
class ServiceInterceptor:

    async def before(self, context):
        pass

    async def after(self, context, result):
        pass

    async def on_error(self, context, error):
        pass
```

标准拦截器：

``` text
AuthenticationInterceptor
AuthorizationInterceptor
AuditInterceptor
TracingInterceptor
MetricsInterceptor
ExceptionInterceptor
```

------------------------------------------------------------------------

# 34. HTTP 层横切

Litestar负责：

``` text
HTTP Authentication
HTTP Middleware
HTTP Routing
HTTP Request Context
OpenAPI
```

HTTP：

``` text
Request
 ↓
Litestar Middleware
 ↓
Authentication
 ↓
Authorization
 ↓
Service Runtime
```

业务 Service 不实现 HTTP 登录逻辑。

------------------------------------------------------------------------

# 35. gRPC 横切

Remote Service：

``` text
Client
 ↓
gRPC Client Interceptor
 ↓
Trace / Metadata / Auth
 ↓
Network
 ↓
gRPC Server Interceptor
 ↓
Authorization / Audit
 ↓
Service
```

HTTP 和 gRPC 应共享 Runtime 层的安全、审计和 Trace 抽象。

------------------------------------------------------------------------

# 36. Database 横切

SQLAlchemy 层负责：

``` text
SQL Audit
SQL Duration
Trace ID
Tenant ID
User ID
Sensitive Table Detection
Slow SQL
Exception
```

示例：

``` python
from sqlalchemy import event


@event.listens_for(engine, "before_cursor_execute")
def before_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    ...
```

数据库拦截只关注：

> "数据库实际发生了什么"。

业务授权关注：

> "用户是否允许做这个业务操作"。

二者必须分离。

------------------------------------------------------------------------

# 37. OpenTelemetry

Trace 应贯穿：

``` text
HTTP
 ↓
Service
 ↓
Service Proxy
 ↓
gRPC
 ↓
Remote Service
 ↓
SQLAlchemy
 ↓
Database
```

目标 Trace：

``` text
Trace
└── HTTP POST /orders
    ├── OrderService.create_order
    ├── UserService.get_user
    ├── gRPC client
    └── DB SELECT
```

Runtime 统一创建和传播 Trace Context。

------------------------------------------------------------------------

# 38. Service Lifecycle

标准生命周期：

``` text
DISCOVERED
    ↓
LOADED
    ↓
CONFIGURED
    ↓
INITIALIZED
    ↓
STARTED
    ↓
READY
    ↓
STOPPING
    ↓
STOPPED
```

Service 不负责自行启动：

``` text
Uvicorn
gRPC Server
Thread
Process
```

由 Runtime 统一管理。

------------------------------------------------------------------------

# 39. Runtime 配置

示例：

``` yaml
runtime:
  mode: inprocess

services:

  user:
    enabled: true
    mode: inprocess

  order:
    enabled: true
    mode: inprocess

  ai:
    enabled: true
    mode: remote
    endpoint: ai-service:50051

interceptors:
  authentication: true
  authorization: true
  audit: true
  tracing: true
  metrics: true
```

------------------------------------------------------------------------

# 40. Service 拆分原则

默认：

``` text
低流量
轻量
开发
调试
依赖简单
    ↓
InProcess
```

需要独立运行：

``` text
高流量
GPU
大模型
依赖冲突
需要独立扩容
故障隔离
资源隔离
    ↓
Remote
```

Service 代码不应因为上述变化而修改。

------------------------------------------------------------------------

# 41. 本地开发模式

推荐默认：

``` text
Monorepo
    ↓
uv workspace
    ↓
editable dependency
    ↓
InProcess Runtime
```

开发者执行：

``` bash
uv sync
uv run pytest
uv run python -m backend_app
```

即可启动完整后端。

------------------------------------------------------------------------

# 42. 独立 Package 验证模式

为了保证 Service 真正独立，发布前必须执行：

``` text
Service Source
    ↓
uv build
    ↓
Wheel
    ↓
Local Repository
    ↓
新建临时环境
    ↓
uv sync
    ↓
运行 Service
```

这一步用于防止 Service 隐式依赖 Monorepo 源代码。

------------------------------------------------------------------------

# 43. 推荐 CI/CD 流程

``` mermaid
flowchart LR
    Commit["Git Commit"] --> Test["Unit Test"]
    Test --> Build["uv build"]
    Build --> PackageTest["Package Install Test"]
    PackageTest --> Publish["Publish Artifact"]
    Publish --> Deploy["Deploy"]
```

Package Test 必须从 Wheel 安装，而不是直接从源码运行。

------------------------------------------------------------------------

# 44. Package 发布规则

发布前：

``` bash
uv run pytest
uv build
```

检查：

``` text
版本
依赖
Entry Point
Wheel 内容
Python 版本
```

然后：

``` text
dist/*.whl
    ↓
~/.backend/repository/simple/<package>/
```

同一版本禁止覆盖。

错误发布：

``` text
1.0.0 → 修改后再次覆盖
```

正确做法：

``` text
1.0.0
1.0.1
```

------------------------------------------------------------------------

# 45. 本地制品库清理

本地 Repository 应保留：

``` text
当前开发版本
最近稳定版本
被其他工程引用的版本
```

清理旧版本：

``` bash
backend package clean
```

不能简单删除所有旧版本，否则历史工程可能无法复现。

建议至少保留：

``` text
最近 N 个版本
```

具体 N 根据团队规模确定。

------------------------------------------------------------------------

# 46. 常见错误

## 46.1 把 Service 写成普通 Python Module

错误：

``` text
backend/services/order/*.py
```

由根项目直接 import。

正确：

``` text
backend-service-order
```

必须拥有：

``` text
pyproject.toml
version
dependencies
entry point
tests
```

------------------------------------------------------------------------

## 46.2 Service 直接访问另一个 Service

错误：

``` python
from user_service.service import UserService
```

正确：

``` text
UserService Contract
        ↓
Service Proxy
```

------------------------------------------------------------------------

## 46.3 Common 承载业务逻辑

错误：

``` text
common/order/
common/user/
```

正确：

``` text
业务逻辑 → Service
公共技术能力 → Common
```

------------------------------------------------------------------------

## 46.4 Service 自己处理登录

错误：

``` python
async def create_order():
    check_login()
```

正确：

``` text
Runtime Authentication
        ↓
Service
```

------------------------------------------------------------------------

## 46.5 直接把数据库 Session 传遍 Service

数据库 Session 应由 DI / Repository 管理。

Service 不应依赖：

``` text
全局 Session
```

------------------------------------------------------------------------

# 47. 架构最终模型

最终体系：

``` mermaid
flowchart TB
    Repo["Local File Package Repository<br/>~/.backend/repository"]

    FW["serviceframework"]
    Common["backend-common"]
    User["backend-service-user"]
    Order["backend-service-order"]
    AI["backend-service-ai"]

    Repo --> FW
    Repo --> Common
    Repo --> User
    Repo --> Order
    Repo --> AI

    FW --> Runtime["Logical Microservice Runtime"]
    Common --> Runtime
    User --> Runtime
    Order --> Runtime
    AI --> Runtime

    Runtime --> Registry["Service Registry<br/>Stevedore"]
    Runtime --> Proxy["Service Proxy"]
    Runtime --> Interceptor["Interceptor Pipeline"]
    Runtime --> Lifecycle["Lifecycle"]
    Runtime --> Web["Litestar"]

    Proxy --> Local["LocalTransport"]
    Proxy --> GRPC["GrpcTransport"]

    Local --> Services["Service"]
    GRPC --> Remote["Remote Service Runtime"]

    Interceptor --> Auth["Auth"]
    Interceptor --> Audit["Audit"]
    Interceptor --> Trace["OpenTelemetry"]
    Interceptor --> DB["SQLAlchemy Interceptor"]
```

------------------------------------------------------------------------

# 48. 最终标准

本项目最终形成以下标准：

``` text
工程标准
    ↓
独立 pyproject.toml
    ↓
独立 Package
    ↓
独立依赖
    ↓
独立测试
    ↓
独立版本
    ↓
独立 Wheel

运行标准
    ↓
Logical Service
    ↓
Runtime
    ↓
Service Proxy
    ↓
Local / Remote Transport

扩展标准
    ↓
Python Entry Point
    ↓
Stevedore
    ↓
Service Registry

横切标准
    ↓
HTTP Middleware
Service Interceptor
gRPC Interceptor
SQLAlchemy Interceptor
OpenTelemetry

制品标准
    ↓
uv build
    ↓
Wheel
    ↓
~/.backend/repository/simple
    ↓
uv sync
```

最终原则：

> **代码边界按照微服务划分，运行边界由 Runtime 决定；Package
> 是独立交付单元，Service 是独立业务单元，Runtime
> 是统一运行单元，Transport 是部署位置抽象，Interceptor
> 是横切能力抽象。**

这套规范的目标不是让 Python 后端"看起来像微服务"，而是让 Service
从第一天开始就具备真正的独立性，同时避免为了微服务而承担不必要的进程、容器和网络开销。
