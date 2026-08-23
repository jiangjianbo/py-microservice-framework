"""
传输模块单元测试

测试本地进程内传输功能，用于同一进程内的服务调用。
"""

import pytest
from serviceframework.contract.service import Service, ServiceMetadata
from serviceframework.contract.request import ServiceRequest
from serviceframework.contract.response import ServiceResponse
from serviceframework.transport.base import Transport
from serviceframework.transport.local import LocalTransport
from dataclasses import dataclass


class TestLocalTransport:
    
    @pytest.mark.asyncio
    async def test_local_transport_creation(self):
        """测试本地传输创建"""
        metadata = ServiceMetadata(name="user-service", version="1.0.0")
        
        @dataclass
        class MockService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                return metadata
            
            async def health_check(self) -> bool:
                return True
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
            
            async def get_user(self, user_id: int):
                return {"id": user_id, "name": "Alice"}
        
        service = MockService()
        transport = LocalTransport(service)
        
        assert transport.service == service
    
    @pytest.mark.asyncio
    async def test_local_transport_invoke_method(self):
        """测试本地传输调用方法"""
        metadata = ServiceMetadata(name="user-service", version="1.0.0")
        
        @dataclass
        class MockService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                return metadata
            
            async def health_check(self) -> bool:
                return True
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
            
            async def get_user(self, user_id: int):
                return {"id": user_id, "name": "Alice"}
            
            async def create_user(self, name: str):
                return {"id": 456, "name": name}
        
        service = MockService()
        transport = LocalTransport(service)
        
        # 调用get_user方法
        result = await transport.invoke("get_user", 123)
        assert result["id"] == 123
        assert result["name"] == "Alice"
        
        # 调用create_user方法
        result = await transport.invoke("create_user", "Bob")
        assert result["id"] == 456
        assert result["name"] == "Bob"
    
    @pytest.mark.asyncio
    async def test_local_transport_invoke_with_kwargs(self):
        """测试本地传输使用关键字参数调用方法"""
        metadata = ServiceMetadata(name="user-service", version="1.0.0")
        
        @dataclass
        class MockService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                return metadata
            
            async def health_check(self) -> bool:
                return True
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
            
            async def find_user(self, user_id: int, include_profile: bool = False):
                result = {"id": user_id, "name": "Alice"}
                if include_profile:
                    result["profile"] = {"age": 30, "email": "alice@example.com"}
                return result
        
        service = MockService()
        transport = LocalTransport(service)
        
        # 使用位置参数
        result = await transport.invoke("find_user", 123, False)
        assert result["id"] == 123
        assert "profile" not in result
        
        # 使用关键字参数
        result = await transport.invoke("find_user", user_id=123, include_profile=True)
        assert result["id"] == 123
        assert "profile" in result
    
    @pytest.mark.asyncio
    async def test_local_transport_invoke_nonexistent_method(self):
        """测试调用不存在的方法"""
        metadata = ServiceMetadata(name="user-service", version="1.0.0")
        
        @dataclass
        class MockService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                return metadata
            
            async def health_check(self) -> bool:
                return True
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
        
        service = MockService()
        transport = LocalTransport(service)
        
        with pytest.raises(AttributeError, match="'MockService' object has no attribute 'nonexistent_method'"):
            await transport.invoke("nonexistent_method")
    
    @pytest.mark.asyncio
    async def test_local_transport_invoke_with_exception(self):
        """测试方法抛出异常时的处理"""
        metadata = ServiceMetadata(name="user-service", version="1.0.0")
        
        @dataclass
        class MockService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                return metadata
            
            async def health_check(self) -> bool:
                return True
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
            
            async def get_user(self, user_id: int):
                if user_id == 0:
                    raise ValueError("用户ID不能为0")
                return {"id": user_id, "name": "Alice"}
        
        service = MockService()
        transport = LocalTransport(service)
        
        # 正常调用
        result = await transport.invoke("get_user", 123)
        assert result["id"] == 123
        
        # 异常调用
        with pytest.raises(ValueError, match="用户ID不能为0"):
            await transport.invoke("get_user", 0)
    
    @pytest.mark.asyncio
    async def test_local_transport_uses_transport_protocol(self):
        """测试本地传输实现了Transport协议"""
        from typing import Protocol
        
        metadata = ServiceMetadata(name="user-service", version="1.0.0")
        
        @dataclass
        class MockService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                return metadata
            
            async def health_check(self) -> bool:
                return True
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
        
        service = MockService()
        transport = LocalTransport(service)
        
        # LocalTransport应该符合Transport协议
        assert isinstance(transport, Transport)
    
    @pytest.mark.asyncio
    async def test_local_transport_with_service_request(self):
        """测试使用服务请求对象调用"""
        metadata = ServiceMetadata(name="user-service", version="1.0.0")
        
        @dataclass
        class MockService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                return metadata
            
            async def health_check(self) -> bool:
                return True
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
            
            async def get_user(self, user_id: int, include_profile: bool = False):
                return {"id": user_id, "name": "Alice", "profile": include_profile}
        
        service = MockService()
        transport = LocalTransport(service)
        
        # 使用服务请求对象
        request = ServiceRequest(
            service_name="user-service",
            method="get_user",
            args=(123,),
            kwargs={"include_profile": True}
        )
        
        result = await transport.invoke(request.method, *request.args, **request.kwargs)
        assert result["id"] == 123
        assert result["profile"] is True