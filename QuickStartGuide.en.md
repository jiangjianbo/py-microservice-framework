# Quick Start Guide

Welcome to Python Logical Microservice Framework! This guide will help you get started with the framework's core features in 10 minutes.

## 🚀 5-Minute Quick Experience

### 1. Environment Setup

```bash
# Clone project
git clone https://github.com/your-org/py-microservice-framework.git
cd py-microservice-framework

# Check Python version (requires 3.12+)
python --version

# Install uv package manager
pip install uv
```

### 2. Install Framework

```bash
# Enter framework directory
cd framework

# Install dependencies
uv sync

# Run tests to verify installation
uv run pytest tests/ -v --tb=short
```

**Expected Result**: 227 tests pass, framework successfully installed!

### 3. Run Feature Demo

```bash
# Enter framework directory, run inside the framework venv
cd framework

# Run framework feature verification
uv run python ../app/verification_demo.py
```

**Expected Result**: See complete framework feature demonstrations including basic services, interceptors, observability, etc.

## 📝 Creating Your First Service

### Option 1: Using Framework API (Recommended)

#### 1. Create Service Project Structure

```bash
mkdir -p my_service/src/my_service
cd my_service
```

#### 2. Create Repository Layer

```python
# src/my_service/repository.py
from typing import Dict, Any

class MyRepository:
    """Data storage layer"""
    
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

#### 3. Create Service Layer

```python
# src/my_service/service.py
from typing import Dict, Any, List

class MyService:
    """Service layer"""
    
    def __init__(self, repository):
        self.repository = repository
    
    async def get_item(self, item_id: int) -> Dict[str, Any]:
        """Get single item"""
        return await self.repository.find(item_id)
    
    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items"""
        return await self.repository.find_all()
```

#### 4. Create API Layer

```python
# src/my_service/api.py
from litestar import get
from my_service.service import MyService

@get("/items/{item_id:int}")
async def get_item(item_id: int, service: MyService) -> dict:
    """Get single item API"""
    return await service.get_item(item_id)

@get("/items")
async def get_all_items(service: MyService) -> list:
    """Get all items API"""
    return await service.get_all_items()
```

#### 5. Create Startup File

```python
# src/my_service/main.py
from litestar import Litestar
from my_service.api import get_item, get_all_items
from my_service.service import MyService
from my_service.repository import MyRepository

# Create dependencies
repository = MyRepository()
service = MyService(repository)

# Create application
app = Litestar(
    route_handlers=[get_item, get_all_items],
    dependencies={"service": lambda: service}
)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting service: http://localhost:8000")
    print("📊 API Documentation: http://localhost:8000/schema")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 6. Create Configuration File

```toml
# pyproject.toml
[project]
name = "my-service"
version = "1.0.0"
description = "My first microservice"
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

#### 7. Run Service

```bash
# Install the service (editable mode; also installs its litestar/uvicorn deps)
pip install -e .

# Run service
python src/my_service/main.py
```

**Expected Result**: Service starts at `http://localhost:8000`

#### 8. Test API

```bash
# Test getting single item
curl http://localhost:8000/items/1

# Test getting all items
curl http://localhost:8000/items

# Open API documentation in browser
open http://localhost:8000/schema
```

### Option 2: Using Framework Example Service

The framework provides complete Service Demo examples:

```bash
# Install user service example into the framework venv (editable mode)
cd framework
uv pip install -e ../services/user

# Run integration tests
uv run pytest tests/test_service_demo_integration.py -v

# Test results should show all 9 tests passing
```

## 🔧 Core Feature Usage Guide

### 1. Service Registration & Discovery

```python
from serviceframework.registry.registry import ServiceRegistry, ServiceMetadata
from serviceframework.contract.service import ServiceDefinition

# Create service registry
registry = ServiceRegistry()

# Create service
class MyService:
    async def do_something(self):
        return {"result": "success"}

# Create service metadata
metadata = ServiceMetadata(
    name="my-service",
    version="1.0.0",
    description="My service"
)

# Register service
registry.register("my-service", MyService(), metadata=metadata)

# Find service
service = registry.get_service("my-service")
result = await service.do_something()
```

### 2. Interceptor Usage

```python
from serviceframework.interceptor.base import ServiceInterceptor, InterceptorContext
from serviceframework.interceptor.pipeline import InterceptorPipeline

class LoggingInterceptor(ServiceInterceptor):
    async def before(self, context: InterceptorContext) -> None:
        # Runs before the call
        print(f"Calling service: {context.service_context.service_name}.{context.method}")

    async def after(self, context: InterceptorContext, result) -> None:
        # Runs after success (reverse order of addition)
        print(f"Call completed")

    async def on_error(self, context: InterceptorContext, error: Exception) -> None:
        # Runs on failure
        print(f"Call failed: {error}")

# Create interceptor pipeline
pipeline = InterceptorPipeline()
pipeline.add_interceptor(LoggingInterceptor())

# Use interceptor to wrap service call
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

### 3. Observability Integration

```python
from serviceframework.observability.telemetry import TelemetryManager, TraceConfig
from serviceframework.contract.service import ServiceContext

# Create tracing manager
config = TraceConfig(
    service_name="my-service",
    endpoint="http://localhost:14268/api/v2/spans",
    enabled=True
)

telemetry_manager = TelemetryManager(config)

# Create tracing span
service_context = ServiceContext("my-service", "do_something", "req-1")
span = telemetry_manager.create_span("do_something", service_context)

await span.start()
# Execute business logic
result = await service.do_something()
await span.end()

# Record metrics
telemetry_manager.record_counter("api_calls", 1, {"endpoint": "/api/do_something"})
telemetry_manager.record_histogram("response_time", 45.6, {"endpoint": "/api/do_something"})
```

### 4. Async Service Development

Framework fully supports async programming:

```python
import asyncio
from typing import List

class AsyncUserService:
    def __init__(self, repository):
        self.repository = repository
    
    async def get_user(self, user_id: int):
        return await self.repository.find(user_id)
    
    async def get_users_batch(self, user_ids: List[int]) -> List:
        """Batch get users (concurrent processing)"""
        tasks = [self.get_user(user_id) for user_id in user_ids]
        return await asyncio.gather(*tasks)

# Use concurrent service
user_service = AsyncUserService(repository)

# Batch get users
users = await user_service.get_users_batch([1, 2, 3, 4, 5])
# This executes 5 requests concurrently, significantly improving performance
```

## 🧪 Testing Framework

### 1. Writing Unit Tests

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

### 2. Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_my_service.py -v

# Run async tests
pytest tests/ -v --asyncio-mode=auto
```

## 📚 In-Depth Learning Resources

### Documentation
- [Architecture Documentation](doc/architecture.md) - Understand the framework's technical architecture
- [Build Specification](doc/build-spec.md) - Understand framework build and configuration specifications
- [Verification Report](Framework_Verification_Report.md) - View complete verification results

### Example Projects
- [User Service](services/user/) - Complete Service Demo example
- [Feature Demo](app/verification_demo.py) - Framework feature demonstration

### Test Verification
```bash
# Run Service Demo integration tests
cd framework
uv run pytest tests/test_service_demo_integration.py -v

# Run framework core tests
uv run pytest tests/test_service_contract.py tests/test_service_registry.py -v

# Run observability tests
uv run pytest tests/test_telemetry.py -v
```

## 🎯 Common Use Cases

### 1. Creating RESTful APIs

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

### 2. Inter-Service Communication

```python
# Remote service call
from serviceframework.transport.grpc.client import GrpcClient
from serviceframework.transport.grpc.config import GrpcConfig

config = GrpcConfig(host="remote-service", port=50051)
client = GrpcClient(config)

await client.connect()
result = await client.send_request("remote-service", request)
```

### 3. Database Integration

```python
from serviceframework.database.interceptor import DatabaseInterceptor, DatabaseConfig

# Configure database
config = DatabaseConfig(url="postgresql://user:pass@localhost/db")
interceptor = DatabaseInterceptor(config)

# Setup engine and models
interceptor.setup_engine()
interceptor.setup_model(Base)

# Use database session
session = interceptor.create_session()
users = session.query(User).all()
session.close()
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Dependency Installation Failure
```bash
# Use uv to install
cd framework
uv sync

# Or use pip to install
pip install -e .
```

#### 2. Import Errors
```bash
# Dependencies must be installed as packages; never point
# PYTHONPATH/sys.path at source directories
# (see doc/local_repository_spec.md section 19)
cd framework
uv sync

# Install example services into the framework venv in editable mode
uv pip install -e ../services/user
```

#### 3. Test Failures
```bash
# Check Python version
python --version  # Requires Python 3.12+

# Update dependencies
cd framework
uv sync --upgrade

# Clean cache and retest
pip cache purge
pytest tests/ -v
```

## 🎉 Next Steps

Congratulations! You've successfully gotten started with Python Logical Microservice Framework.

### Recommended Learning Path
1. **Master Basics**: Complete all examples in this guide
2. **Deep Dive Architecture**: Read [Architecture Documentation](doc/architecture.md)
3. **Practice Projects**: Create your own microservice applications
4. **Extend Features**: Learn interceptors, observability, and other advanced features
5. **Production Deployment**: Learn about service registration, monitoring, and operations

### Getting Help
- Read framework documentation
- Run example projects
- Check unit tests for more usage patterns

**Enjoy using the framework!** 🚀