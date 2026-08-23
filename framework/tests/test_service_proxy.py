"""
服务代理模块单元测试

测试服务代理的各种场景和边界情况。
"""

import pytest
from unittest.mock import Mock, AsyncMock
from serviceframework.contract.service import Service, ServiceMetadata
from serviceframework.transport.base import Transport
from serviceframework.proxy.proxy import ServiceProxy
from serviceframework.proxy.factory import ProxyFactory
from dataclasses import dataclass


class TestServiceProxy:
    
    @pytest.mark.asyncio
    async def test_proxy_creation(self):
        """测试服务代理创建"""
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        
        assert proxy.service_name == "user-service"
        assert proxy.transport == transport
    
    @pytest.mark.asyncio
    async def test_proxy_invoke_method(self):
        """测试代理调用方法"""
        transport = Mock(spec=Transport)
        transport.invoke = AsyncMock(return_value={"id": 123, "name": "Alice"})
        
        proxy = ServiceProxy("user-service", transport)
        result = await proxy.invoke("get_user", 123)
        
        assert result["id"] == 123
        assert result["name"] == "Alice"
        transport.invoke.assert_called_once_with("get_user", 123)
    
    @pytest.mark.asyncio
    async def test_proxy_invoke_with_kwargs(self):
        """测试代理使用关键字参数调用方法"""
        transport = Mock(spec=Transport)
        transport.invoke = AsyncMock(return_value={"id": 123, "name": "Alice", "profile": {"age": 30}})
        
        proxy = ServiceProxy("user-service", transport)
        result = await proxy.invoke("find_user", user_id=123, include_profile=True)
        
        assert result["profile"]["age"] == 30
        transport.invoke.assert_called_once_with("find_user", user_id=123, include_profile=True)
    
    @pytest.mark.asyncio
    async def test_proxy_invoke_with_exception(self):
        """测试代理调用方法时发生异常"""
        from serviceframework.contract.service import ServiceError
        
        transport = Mock(spec=Transport)
        transport.invoke = AsyncMock(side_effect=ServiceError("用户不存在", code="USER_NOT_FOUND"))
        
        proxy = ServiceProxy("user-service", transport)
        
        with pytest.raises(ServiceError, match="用户不存在"):
            await proxy.invoke("get_user", 0)
    
    @pytest.mark.asyncio
    async def test_proxy_get_transport(self):
        """测试代理获取传输对象"""
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        
        assert proxy.get_transport() == transport
    
    @pytest.mark.asyncio
    async def test_proxy_get_service_name(self):
        """测试代理获取服务名称"""
        proxy = ServiceProxy("user-service", Mock())
        assert proxy.get_service_name() == "user-service"
    
    @pytest.mark.asyncio
    async def test_proxy_is_available(self):
        """测试代理检查可用性"""
        transport = Mock(spec=Transport)
        transport.is_available = Mock(return_value=True)
        
        proxy = ServiceProxy("user-service", transport)
        assert proxy.is_available() is True
    
    @pytest.mark.asyncio
    async def test_proxy_get_endpoint(self):
        """测试代理获取端点信息"""
        transport = Mock(spec=Transport)
        transport.get_endpoint = Mock(return_value="local:UserService")
        
        proxy = ServiceProxy("user-service", transport)
        endpoint = proxy.get_endpoint()
        
        assert endpoint == "local:UserService"


class TestProxyFactory:
    
    def test_factory_create_local_proxy(self):
        """测试工厂创建本地代理"""
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
        factory = ProxyFactory()
        
        proxy = factory.create_local_proxy("user-service", service)
        
        assert proxy.service_name == "user-service"
        assert proxy.get_endpoint() == "local:MockService"
    
    def test_factory_create_proxy_with_custom_transport(self):
        """测试工厂使用自定义传输创建代理"""
        transport = Mock(spec=Transport)
        factory = ProxyFactory()
        
        proxy = factory.create_proxy("user-service", transport)
        
        assert proxy.service_name == "user-service"
        assert proxy.transport == transport
    
    def test_factory_create_multiple_proxies(self):
        """测试工厂创建多个代理"""
        transport1 = Mock(spec=Transport)
        transport2 = Mock(spec=Transport)
        factory = ProxyFactory()
        
        proxy1 = factory.create_proxy("user-service", transport1)
        proxy2 = factory.create_proxy("order-service", transport2)
        
        assert proxy1.service_name == "user-service"
        assert proxy2.service_name == "order-service"
        assert proxy1.transport != proxy2.transport
    
    def test_factory_proxy_registry(self):
        """测试工厂的代理注册表"""
        transport = Mock(spec=Transport)
        factory = ProxyFactory()
        
        proxy1 = factory.create_proxy("user-service", transport)
        proxy2 = factory.create_proxy("user-service", transport)
        
        # 工厂应该返回同一个代理实例
        assert proxy1 is proxy2
    
    def test_factory_get_proxy(self):
        """测试工厂获取已创建的代理"""
        transport = Mock(spec=Transport)
        factory = ProxyFactory()
        
        # 先创建代理
        created_proxy = factory.create_proxy("user-service", transport)
        
        # 再获取代理
        retrieved_proxy = factory.get_proxy("user-service")
        
        assert created_proxy is retrieved_proxy
    
    def test_factory_get_nonexistent_proxy(self):
        """测试获取不存在的代理"""
        factory = ProxyFactory()
        
        with pytest.raises(ValueError, match="代理'user-service'不存在"):
            factory.get_proxy("user-service")
    
    def test_factory_has_proxy(self):
        """测试检查代理是否存在"""
        transport = Mock(spec=Transport)
        factory = ProxyFactory()
        
        assert not factory.has_proxy("user-service")
        
        factory.create_proxy("user-service", transport)
        assert factory.has_proxy("user-service")
    
    def test_factory_clear_proxies(self):
        """测试清空所有代理"""
        transport = Mock(spec=Transport)
        factory = ProxyFactory()
        
        factory.create_proxy("user-service", transport)
        factory.create_proxy("order-service", transport)
        
        assert factory.has_proxy("user-service")
        assert factory.has_proxy("order-service")
        
        factory.clear_proxies()
        
        assert not factory.has_proxy("user-service")
        assert not factory.has_proxy("order-service")