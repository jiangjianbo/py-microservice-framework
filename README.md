# Python Logical Microservice Framework

一个基于Python的逻辑微服务运行时框架，支持多种通信方式和可观测性。

## 架构特点

- 逻辑微服务架构：服务在代码和依赖上独立，部署方式灵活
- 支持进程内和远程两种通信方式
- 插件化设计，易于扩展
- 内置拦截器链，支持AOP编程
- 完整的可观测性支持

## 核心模块

### 已完成模块 (P1-P10)

1. **P1: Service Contract** - 服务契约定义
2. **P2: Service Registry** - 服务注册表（内存、文件系统、本地文件存储）
3. **P3: InProcess Transport** - 进程内传输
4. **P4: Service Proxy** - 服务代理
5. **P5: Litestar Adapter** - Litestar HTTP适配器
6. **P6: Dependency Injection** - 依赖注入容器
7. **P7: Lifecycle** - 服务生命周期管理
8. **P8: Interceptor Pipeline** - 拦截器管道
9. **P9: SQLAlchemy Integration** - SQLAlchemy数据库集成
10. **P10: OpenTelemetry** - 分布式追踪和指标

### 进行中模块 (P11-P12)

11. **P11: gRPC Transport** - gRPC传输（依赖grpcio）
12. **P12: Remote Service Runtime** - 远程服务运行时

## 项目结构

```
py-microservice-framework/
├── framework/           # 核心框架包
│   ├── pyproject.toml   # 项目配置
│   ├── src/serviceframework/  # 源代码
│   └── tests/           # 单元测试
├── services/            # 示例服务
├── app/                 # 应用代码
├── doc/                 # 文档
└── .repository/         # 本地包仓库
```

## 技术栈

- **语言**: Python 3.12+
- **HTTP框架**: Litestar
- **插件系统**: Stevedore
- **ORM**: SQLAlchemy 2.x
- **可观测性**: OpenTelemetry
- **远程调用**: gRPC
- **包管理**: uv
- **测试**: pytest

## 使用方法

### 安装依赖

```bash
cd framework
uv sync
```

### 运行测试

```bash
uv run pytest tests/ -v
```

### 创建服务

```python
from serviceframework.contract.service import ServiceDefinition
from serviceframework.proxy.factory import ServiceProxyFactory
from serviceframework.transport.local import LocalTransportFactory

# 定义服务
service = ServiceDefinition(
    name="user-service",
    version="1.0.0",
    description="用户服务"
)

# 创建服务代理
transport_factory = LocalTransportFactory()
proxy_factory = ServiceProxyFactory()

proxy = proxy_factory.create_proxy(service, transport_factory)
```

### 启动HTTP服务

```python
from serviceframework.web.adapter import LitestarAdapter
from litestar import Litestar

adapter = LitestarAdapter()
app = adapter.create_app([service])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 开发规范

- 每个模块都遵循TDD开发模式
- 完整的单元测试覆盖
- 中文注释和文档
- 使用mock和直接引用灵活处理测试依赖

## License

MIT License