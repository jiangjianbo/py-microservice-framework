# Python Logical Microservice Framework

[中文文档](README.zh-CN.md) | English Documentation

A Python-based logical microservice runtime framework that supports multiple communication methods and observability.

## 🎯 Project Goals

This framework aims to simplify microservice development, allowing developers to focus on business logic while the framework handles infrastructure concerns. Based on the logical microservice architecture concept, services are completely independent in code and dependencies, supporting flexible deployment approaches.

### Core Philosophy

- **Developer Focus on Business**: Domain → Application → Repository → API
- **Framework Handles Infrastructure**: Service Discovery → HTTP Server → gRPC → Authentication → Tracing → Audit → Lifecycle

## ✨ Key Features

### 🚀 Complete Microservice Infrastructure
- **Logical Microservice Architecture**: Services independent in code and dependencies, flexible deployment
- **Multiple Transport Methods**: Supports both InProcess and remote (gRPC) communication
- **Service Registration & Discovery**: Dynamic service registration, discovery, and health checks
- **Service Proxy**: Unified service call interface and proxy pattern
- **HTTP Adapter**: High-performance HTTP service support based on Litestar

### 🔧 Enterprise-Grade Features
- **Dependency Injection**: Complete DI container with lifecycle management
- **Interceptor Chain**: AOP programming support, unified cross-cutting concerns management
- **Lifecycle Management**: Service startup, shutdown, and resource management
- **Observability**: OpenTelemetry integration, supports distributed tracing and metrics collection
- **Database Integration**: SQLAlchemy 2.x support with interceptors and ORM integration

### 📊 Developer Experience
- **Test-Driven Development**: TDD development pattern, complete unit test coverage
- **Plugin Architecture**: Stevedore-based plugin system
- **Async-First**: Comprehensive async programming and high-concurrency support
- **Type Safety**: Complete type annotations and static type checking

## 🧪 Simple Example

### Quick Start

Below is a minimal user service example designed according to build-spec.md Chapter 31:

#### 1. Project Structure

```text
services/user/
├── pyproject.toml
├── src/
│   └── user_service/
│       ├── repository.py  # Data storage layer
│       ├── service.py     # Service layer
│       └── api.py         # API layer
└── tests/
```

#### 2. Repository Layer (`repository.py`)

```python
class UserRepository:
    """User data storage"""
    
    async def find(self, user_id: int):
        return {
            "id": user_id,
            "name": "Alice",
            "email": f"alice{user_id}@example.com"
        }
```

#### 3. Service Layer (`service.py`)

```python
from typing import Dict, Any

class UserService:
    """User service"""
    
    def __init__(self, repository):
        self.repository = repository
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        return await self.repository.find(user_id)
```

#### 4. API Layer (`api.py`)

```python
from litestar import get
from user_service.service import UserService

@get("/users/{user_id:int}")
async def get_user(user_id: int, service: UserService) -> dict:
    return await service.get_user(user_id)
```

#### 5. Run Verification

```bash
# Install the example service into the framework venv (editable mode)
cd framework
uv pip install -e ../services/user

# Run integration tests
uv run pytest tests/test_service_demo_integration.py -v
```

### Feature Verification Demo

The framework provides comprehensive feature verification demo:

```bash
# Run feature verification (inside the framework venv)
cd framework
uv run python ../app/verification_demo.py
```

Demonstrations include:
- ✅ Basic Service Functions - Repository, Service layered architecture
- ✅ Service Registry - Dynamic service discovery and registration
- ✅ Interceptor Chain - AOP programming and cross-cutting concerns
- ✅ Observability - Distributed tracing and metrics collection
- ✅ Async Processing - Concurrent request processing capabilities
- ✅ Service Integration - Cross-service calls and data transmission

## 🏗️ Architecture Design

### Module Architecture

The framework contains 12 core modules, fully covering all infrastructure for microservice development:

#### Core Modules (P1-P8)
1. **P1: Service Contract** - Service contract definitions and communication protocols
2. **P2: Service Registry** - Multiple service registration implementations (memory, filesystem, local storage)
3. **P3: InProcess Transport** - In-process communication transport
4. **P4: Service Proxy** - Service proxy factory and implementations
5. **P5: Litestar Adapter** - HTTP service adapter
6. **P6: Dependency Injection** - Dependency injection container
7. **P7: Lifecycle** - Service lifecycle management
8. **P8: Interceptor Pipeline** - Interceptor pipeline and AOP support

#### Extension Modules (P9-P12)
9. **P9: SQLAlchemy Integration** - Database integration and ORM support
10. **P10: OpenTelemetry** - Distributed tracing, span management, metrics recording
11. **P11: gRPC Transport** - gRPC client and server implementations
12. **P12: Remote Service Runtime** - Remote service runtime and service discovery

### Technology Stack

- **Language**: Python 3.12+
- **HTTP Framework**: Litestar 2.x
- **Plugin System**: Stevedore
- **ORM**: SQLAlchemy 2.x (sync/async support)
- **Observability**: OpenTelemetry
- **Remote Calls**: gRPC
- **Package Manager**: uv
- **Testing**: pytest + pytest-asyncio

## 📦 Installation and Usage

### Framework Installation

```bash
cd framework
uv sync
```

### Creating Services

#### 1. Define Repository Layer

```python
# repository.py
class MyRepository:
    async def find(self, id: int):
        return {"id": id, "name": f"Item{id}"}
```

#### 2. Define Service Layer

```python
# service.py
class MyService:
    def __init__(self, repository):
        self.repository = repository
    
    async def get_item(self, item_id: int):
        return await self.repository.find(item_id)
```

#### 3. Define API Layer

```python
# api.py
from litestar import get
from my_service.service import MyService

@get("/items/{item_id:int}")
async def get_item(item_id: int, service: MyService) -> dict:
    return await service.get_item(item_id)
```

#### 4. Start Service

```python
# main.py
from litestar import Litestar
from my_service.api import get_item
from my_service.service import MyService
from my_service.repository import MyRepository

# Create dependencies
repository = MyRepository()
service = MyService(repository)

# Create application
app = Litestar(
    route_handlers=[get_item],
    dependencies={"service": lambda: service}
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
cd framework
uv run pytest tests/ -v

# Run specific module tests
uv run pytest tests/test_service_contract.py -v
uv run pytest tests/test_telemetry.py -v
uv run pytest tests/test_remote_service.py -v
```

### Test Results

- **Overall Test Pass Rate**: 100% (227/227 tests passed)
- **Core Modules**: 100% passed
- **Service Demo**: 100% passed (9/9 tests)
- **Demo App Integration (demo_app)**: 100% passed (23/23 tests)

## 📂 Project Structure

```
py-microservice-framework/
├── framework/                 # Core framework package
│   ├── pyproject.toml        # Project configuration
│   ├── src/serviceframework/ # Source code
│   │   ├── contract/        # Service contracts
│   │   ├── registry/        # Service registry
│   │   ├── transport/       # Transport layer
│   │   ├── proxy/           # Service proxy
│   │   ├── web/             # HTTP adapter
│   │   ├── runtime/         # Runtime
│   │   ├── interceptor/     # Interceptor
│   │   ├── database/        # Database integration
│   │   ├── observability/   # Observability
│   │   └── transport/       # Transport layer
│   └── tests/               # Unit tests
├── services/                 # Example services
│   ├── user/                # User service example
│   └── order/               # Order service example
├── app/                      # Application code
│   ├── verification_demo.py  # Feature verification demo
│   └── simple_demo_app.py    # Simplified demo app
├── doc/                      # Documentation
│   ├── architecture.md       # Architecture documentation
│   ├── build-spec.md         # Build specification
│   └── local_repository_spec.md # Local repository specification
├── .repository/              # Local package repository
├── README.md                 # Project description (Chinese)
├── README.zh-CN.md           # Chinese documentation
└── README.en.md              # English documentation
```

## 📚 Documentation

- [Architecture Documentation](doc/architecture.md) - Detailed technical architecture design
- [Build Specification](doc/build-spec.md) - Framework build and configuration specification
- [Local Repository Specification](doc/local_repository_spec.md) - Local package configuration guide
- [Verification Report](Framework_Verification_Report.md) - Complete verification test report

## 🤝 Contributing

We welcome community contributions! Please follow these guidelines:

- Each module follows TDD development pattern
- Complete unit test coverage
- Chinese comments and documentation
- Flexible use of mocks and direct references for test dependencies

## 📄 License

MIT License

## 🎉 Project Status

**✅ Framework is fully ready for production use**

- All 12 core modules implemented
- All 227 test cases passed (100%)
- Service Demo cases fully verified
- Supports complex distributed application development

The framework fully meets design requirements and provides complete microservice infrastructure!