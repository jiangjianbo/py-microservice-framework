# 快速开始指南

欢迎使用Python逻辑微服务框架！本指南将帮助您在10分钟内快速上手框架的核心功能。

## 🚀 5分钟快速体验

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-org/py-microservice-framework.git
cd py-microservice-framework

# 检查Python版本 (需要3.12+)
python --version

# 安装uv包管理器
pip install uv
```

### 2. 安装框架

```bash
# 进入框架目录
cd framework

# 安装依赖
uv sync

# 运行测试验证安装
uv run pytest tests/ -v --tb=short
```

**预期结果**: 看到227个测试通过，框架安装成功！

### 3. 运行功能演示

```bash
# 进入框架目录，在框架虚拟环境中执行
cd framework

# 运行框架功能验证
uv run python ../app/verification_demo.py
```

**预期结果**: 看到完整的框架功能演示，包括基础服务、拦截器、可观测性等。

## 📝 创建第一个服务

### 方案一：使用框架API（推荐）

#### 1. 创建服务项目结构

```bash
mkdir -p my_service/src/my_service
cd my_service
```

#### 2. 创建Repository层

```python
# src/my_service/repository.py
from typing import Dict, Any

class MyRepository:
    """数据存储层"""
    
    async def find(self, id: int) -> Dict[str, Any]:
        return {
            "id": id,
            "name": f"Item{id}",
            "description": f"This is item {id}"
        }
    
    async def find_all(self) -> list:
        return [
            {"id": i, "name": f"Item{i}", "description": f"This is item {i}"}
            for i in range(1, 6)
        ]
```

#### 3. 创建Service层

```python
# src/my_service/service.py
from typing import Dict, Any, List

class MyService:
    """服务层"""
    
    def __init__(self, repository):
        self.repository = repository
    
    async def get_item(self, item_id: int) -> Dict[str, Any]:
        """获取单个项目"""
        return await self.repository.find(item_id)
    
    async def get_all_items(self) -> List[Dict[str, Any]]:
        """获取所有项目"""
        return await self.repository.find_all()
```

#### 4. 创建API层

```python
# src/my_service/api.py
from litestar import get
from my_service.service import MyService

@get("/items/{item_id:int}")
async def get_item(item_id: int, service: MyService) -> dict:
    """获取单个项目API"""
    return await service.get_item(item_id)

@get("/items")
async def get_all_items(service: MyService) -> list:
    """获取所有项目API"""
    return await service.get_all_items()
```

#### 5. 创建启动文件

```python
# src/my_service/main.py
from litestar import Litestar
from my_service.api import get_item, get_all_items
from my_service.service import MyService
from my_service.repository import MyRepository

# 创建依赖
repository = MyRepository()
service = MyService(repository)

# 创建应用（Litestar 的依赖提供器必须是可调用对象）
app = Litestar(
    route_handlers=[get_item, get_all_items],
    dependencies={"service": lambda: service}
)

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动服务: http://localhost:8000")
    print("📊 API文档: http://localhost:8000/schema")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 6. 创建配置文件

```toml
# pyproject.toml
[project]
name = "my-service"
version = "1.0.0"
description = "我的第一个微服务"
requires-python = ">=3.12"
dependencies = [
    "litestar>=2",
    "uvicorn>=0.30",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_service"]
```

#### 7. 运行服务

```bash
# 安装服务（可编辑模式，会同时安装声明的 litestar/uvicorn 依赖）
pip install -e .

# 运行服务
python src/my_service/main.py
```

**预期结果**: 服务启动在 `http://localhost:8000`

#### 8. 测试API

```bash
# 测试获取单个项目
curl http://localhost:8000/items/1

# 测试获取所有项目
curl http://localhost:8000/items

# 在浏览器中访问API文档
open http://localhost:8000/schema
```

### 方案二：使用框架示例服务

框架已经提供了完整的Service Demo示例：

```bash
# 安装用户服务示例到框架虚拟环境（可编辑模式）
cd framework
uv pip install -e ../services/user

# 运行集成测试
uv run pytest tests/test_service_demo_integration.py -v

# 测试结果应该显示9个测试全部通过
```

## 🔧 核心功能使用指南

### 1. 服务注册与发现

```python
from serviceframework.registry.registry import ServiceRegistry, ServiceMetadata
from serviceframework.contract.service import ServiceDefinition

# 创建服务注册表
registry = ServiceRegistry()

# 创建服务
class MyService:
    async def do_something(self):
        return {"result": "success"}

# 创建服务元数据
metadata = ServiceMetadata(
    name="my-service",
    version="1.0.0",
    description="我的服务"
)

# 注册服务
registry.register("my-service", MyService(), metadata=metadata)

# 查找服务
service = registry.get_service("my-service")
result = await service.do_something()
```

### 2. 拦截器使用

```python
from serviceframework.interceptor.base import ServiceInterceptor, InterceptorContext
from serviceframework.interceptor.pipeline import InterceptorPipeline

class LoggingInterceptor(ServiceInterceptor):
    async def before(self, context: InterceptorContext) -> None:
        # 调用前执行
        print(f"调用服务: {context.service_context.service_name}.{context.method}")

    async def after(self, context: InterceptorContext, result) -> None:
        # 调用成功后执行（按添加的逆序）
        print(f"调用完成")

    async def on_error(self, context: InterceptorContext, error: Exception) -> None:
        # 调用失败后执行
        print(f"调用失败: {error}")

# 创建拦截器管道
pipeline = InterceptorPipeline()
pipeline.add_interceptor(LoggingInterceptor())

# 使用拦截器包装服务调用
from serviceframework.contract.service import ServiceContext

service_context = ServiceContext("my-service", "do_something", "req-1")
interceptor_context = InterceptorContext(
    service_context=service_context,
    method="do_something",
    args=(),
    kwargs={}
)

async def target():
    return await service.do_something()

result = await pipeline.execute(interceptor_context, target)
```

### 3. 可观测性集成

```python
from serviceframework.observability.telemetry import TelemetryManager, TraceConfig
from serviceframework.contract.service import ServiceContext

# 创建追踪管理器
config = TraceConfig(
    service_name="my-service",
    endpoint="http://localhost:14268/api/v2/spans",
    enabled=True
)

telemetry_manager = TelemetryManager(config)

# 创建追踪Span
service_context = ServiceContext("my-service", "do_something", "req-1")
span = telemetry_manager.create_span("do_something", service_context)

await span.start()
# 执行业务逻辑
result = await service.do_something()
await span.end()

# 记录指标
telemetry_manager.record_counter("api_calls", 1, {"endpoint": "/api/do_something"})
telemetry_manager.record_histogram("response_time", 45.6, {"endpoint": "/api/do_something"})
```

### 4. 异步服务开发

框架完全支持异步编程：

```python
import asyncio
from typing import List

class AsyncUserService:
    def __init__(self, repository):
        self.repository = repository
    
    async def get_user(self, user_id: int):
        return await self.repository.find(user_id)
    
    async def get_users_batch(self, user_ids: List[int]) -> List:
        """批量获取用户（并发处理）"""
        tasks = [self.get_user(user_id) for user_id in user_ids]
        return await asyncio.gather(*tasks)

# 使用并发服务
user_service = AsyncUserService(repository)

# 批量获取用户
users = await user_service.get_users_batch([1, 2, 3, 4, 5])
# 这将并发执行5个请求，显著提高性能
```

## 🧪 测试框架

### 1. 编写单元测试

```python
# tests/test_my_service.py
import pytest
from my_service.repository import MyRepository
from my_service.service import MyService

class TestMyService:
    @pytest.mark.asyncio
    async def test_repository_find(self):
        repository = MyRepository()
        result = await repository.find(1)
        
        assert result["id"] == 1
        assert "name" in result
    
    @pytest.mark.asyncio
    async def test_service_get_item(self):
        repository = MyRepository()
        service = MyService(repository)
        
        result = await service.get_item(1)
        
        assert result["id"] == 1
        assert result["name"] == "Item1"
```

### 2. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_my_service.py -v

# 运行异步测试
pytest tests/ -v --asyncio-mode=auto
```

## 📚 深入学习资源

### 文档
- [架构文档](doc/architecture.md) - 了解框架的技术架构
- [构建规范](doc/build-spec.md) - 了解框架构建和配置规范
- [验证报告](Framework_Verification_Report.md) - 查看完整的验证结果

### 示例项目
- [用户服务](services/user/) - 完整的Service Demo示例
- [功能演示](app/verification_demo.py) - 框架功能演示

### 测试验证
```bash
# 运行Service Demo集成测试
cd framework
uv run pytest tests/test_service_demo_integration.py -v

# 运行框架核心测试
uv run pytest tests/test_service_contract.py tests/test_service_registry.py -v

# 运行可观测性测试
uv run pytest tests/test_telemetry.py -v
```

## 🎯 常见使用场景

### 1. 创建RESTful API

```python
from litestar import get, post
from my_service.service import MyService

@get("/items/{item_id:int}")
async def get_item(item_id: int, service: MyService):
    return await service.get_item(item_id)

@post("/items")
async def create_item(service: MyService, data: dict):
    return await service.create_item(data)
```

### 2. 服务间通信

```python
# 远程服务调用
from serviceframework.transport.grpc.client import GrpcClient
from serviceframework.transport.grpc.config import GrpcConfig

config = GrpcConfig(host="remote-service", port=50051)
client = GrpcClient(config)

await client.connect()
result = await client.send_request("remote-service", request)
```

### 3. 数据库集成

```python
from serviceframework.database.interceptor import DatabaseInterceptor, DatabaseConfig

# 配置数据库
config = DatabaseConfig(url="postgresql://user:pass@localhost/db")
interceptor = DatabaseInterceptor(config)

# 设置引擎和模型
interceptor.setup_engine()
interceptor.setup_model(Base)

# 使用数据库会话
session = interceptor.create_session()
users = session.query(User).all()
session.close()
```

## 🚨 故障排除

### 常见问题

#### 1. 依赖安装失败
```bash
# 使用uv安装
cd framework
uv sync

# 或使用pip安装
pip install -e .
```

#### 2. 导入错误
```bash
# 依赖必须以包方式安装，禁止使用 PYTHONPATH/sys.path 指向源码目录
# （参见 doc/local_repository_spec.md 第19节）
cd framework
uv sync

# 示例服务以可编辑模式安装到框架虚拟环境
uv pip install -e ../services/user
```

#### 3. 测试失败
```bash
# 检查Python版本
python --version  # 需要Python 3.12+

# 更新依赖
cd framework
uv sync --upgrade

# 清理缓存后重新测试
pip cache purge
pytest tests/ -v
```

## 🎉 下一步

恭喜！您已经成功入门Python逻辑微服务框架。

### 推荐的学习路径
1. **掌握基础**: 完成本指南的所有示例
2. **深入架构**: 阅读[架构文档](doc/architecture.md)
3. **实践项目**: 创建自己的微服务应用
4. **扩展功能**: 学习拦截器、可观测性等高级特性
5. **生产部署**: 了解服务注册、监控和运维

### 获取帮助
- 查看框架文档
- 运行示例项目
- 查看单元测试了解更多用法

**祝您使用愉快！** 🚀