"""
服务契约模块单元测试

测试服务契约的各种场景和边界情况。
"""

import pytest
import asyncio
from serviceframework.contract.service import Service, ServiceContext, ServiceMetadata, ServiceError
from dataclasses import dataclass


class TestServiceError:
    
    def test_service_error_creation(self):
        """测试服务错误创建"""
        error = ServiceError("Test error", code="TEST_ERROR")
        assert str(error) == "Test error"
        assert error.code == "TEST_ERROR"
        assert error.message == "Test error"
    
    def test_service_error_with_code(self):
        """测试带代码的服务错误创建"""
        error = ServiceError("User not found", code="USER_NOT_FOUND", details={"user_id": 123})
        assert error.code == "USER_NOT_FOUND"
        assert error.details == {"user_id": 123}
    
    def test_service_error_inheritance(self):
        """测试服务错误继承"""
        error = ServiceError("Test")
        assert isinstance(error, Exception)
    
    def test_service_error_to_dict(self):
        """测试服务错误转换为字典"""
        error = ServiceError("User not found", code="USER_NOT_FOUND", details={"user_id": 123})
        error_dict = error.to_dict()
        assert error_dict["code"] == "USER_NOT_FOUND"
        assert error_dict["message"] == "User not found"
        assert error_dict["details"]["user_id"] == 123


class TestServiceMetadata:
    
    def test_service_metadata_creation(self):
        """测试服务元数据创建"""
        metadata = ServiceMetadata(
            name="user-service",
            version="1.0.0",
            description="User management service"
        )
        assert metadata.name == "user-service"
        assert metadata.version == "1.0.0"
        assert metadata.description == "User management service"
    
    def test_service_metadata_with_dependencies(self):
        """测试带依赖的服务元数据创建"""
        metadata = ServiceMetadata(
            name="order-service",
            version="1.0.0",
            dependencies=["user-service", "product-service"]
        )
        assert "user-service" in metadata.dependencies
        assert "product-service" in metadata.dependencies
    
    def test_service_metadata_validation_empty_name(self):
        """测试服务元数据验证：空名称"""
        with pytest.raises(ValueError, match="服务名称不能为空"):
            ServiceMetadata(name="", version="1.0.0")
    
    def test_service_metadata_validation_empty_version(self):
        """测试服务元数据验证：空版本"""
        with pytest.raises(ValueError, match="服务版本号不能为空"):
            ServiceMetadata(name="user-service", version="")
    
    def test_service_metadata_with_tags(self):
        """测试带标签的服务元数据创建"""
        metadata = ServiceMetadata(
            name="user-service",
            version="1.0.0",
            tags={"category": "business", "team": "platform"}
        )
        assert metadata.tags["category"] == "business"
        assert metadata.tags["team"] == "platform"


class TestServiceContext:
    
    def test_service_context_creation(self):
        """测试服务上下文创建"""
        context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123"
        )
        assert context.service_name == "user-service"
        assert context.method == "get_user"
        assert context.request_id == "req-123"
    
    def test_service_context_with_metadata(self):
        """测试带元数据的服务上下文创建"""
        metadata = {"user_id": 123, "trace_id": "trace-456"}
        context = ServiceContext(
            service_name="user-service",
            method="get_user",
            metadata=metadata
        )
        assert context.metadata["user_id"] == 123
        assert context.metadata["trace_id"] == "trace-456"
    
    def test_service_context_add_metadata(self):
        """测试添加元数据"""
        context = ServiceContext(service_name="test", method="test")
        context.add_metadata("key", "value")
        assert context.metadata["key"] == "value"
    
    def test_service_context_get_metadata(self):
        """测试获取元数据"""
        context = ServiceContext(
            service_name="test",
            method="test",
            metadata={"existing_key": "existing_value"}
        )
        assert context.get_metadata("existing_key") == "existing_value"
        assert context.get_metadata("non_existing_key", "default") == "default"
    
    def test_service_context_copy(self):
        """测试复制上下文"""
        original = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123",
            metadata={"user_id": 123}
        )
        copy = original.copy()
        assert copy.service_name == original.service_name
        assert copy.method == original.method
        assert copy.request_id == original.request_id
        assert copy.metadata == original.metadata
        
        # 修改副本不应该影响原始对象
        copy.add_metadata("new_key", "new_value")
        assert "new_key" not in original.metadata
        assert "new_key" in copy.metadata


class TestServiceProtocol:
    
    def test_service_is_protocol(self):
        """测试服务是否为协议"""
        from typing import Protocol
        assert issubclass(Service, Protocol)
    
    @pytest.mark.asyncio
    async def test_service_can_be_implemented(self):
        """测试服务可以被实现"""
        @dataclass
        class MockService:
            name: str = "mock-service"
            
            async def get_metadata(self) -> ServiceMetadata:
                return ServiceMetadata(name=self.name, version="1.0.0")
            
            async def health_check(self) -> bool:
                return True
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
        
        # MockService应该符合Service协议
        service = MockService()
        metadata = await service.get_metadata()
        assert metadata.name == "mock-service"
        assert await service.health_check() is True
        
        # 验证service符合Service协议
        assert isinstance(service, Service)
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """测试服务生命周期"""
        lifecycle_calls = []
        
        @dataclass
        class LifecycleService:
            name: str = "lifecycle-service"
            
            async def get_metadata(self) -> ServiceMetadata:
                lifecycle_calls.append("get_metadata")
                return ServiceMetadata(name=self.name, version="1.0.0")
            
            async def health_check(self) -> bool:
                lifecycle_calls.append("health_check")
                return True
            
            async def initialize(self) -> None:
                lifecycle_calls.append("initialize")
            
            async def shutdown(self) -> None:
                lifecycle_calls.append("shutdown")
        
        service = LifecycleService()
        
        # 测试初始化
        await service.initialize()
        assert "initialize" in lifecycle_calls
        
        # 测试健康检查
        await service.health_check()
        assert "health_check" in lifecycle_calls
        
        # 测试关闭
        await service.shutdown()
        assert "shutdown" in lifecycle_calls