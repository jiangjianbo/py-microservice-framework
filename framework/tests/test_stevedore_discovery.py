"""
Stevedore服务发现模块单元测试

测试基于Stevedore的服务自动发现和加载功能。
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from serviceframework.registry.stevedore_registry import (
    StevedoreServiceDiscovery,
    ServiceDiscoveryError
)
from serviceframework.registry.registry import ServiceRegistry
from serviceframework.contract.service import Service, ServiceMetadata
from dataclasses import dataclass


class TestServiceDiscoveryError:
    
    def test_error_creation(self):
        """测试错误创建"""
        error = ServiceDiscoveryError("Discovery failed", {"service": "test"})
        assert str(error) == "Discovery failed"
        assert error.details["service"] == "test"


class TestStevedoreServiceDiscovery:
    
    def test_discovery_creation(self):
        """测试服务发现器创建"""
        registry = ServiceRegistry()
        discovery = StevedoreServiceDiscovery(registry=registry)
        
        assert discovery.namespace == StevedoreServiceDiscovery.DEFAULT_NAMESPACE
        assert discovery.registry == registry
    
    def test_discovery_custom_namespace(self):
        """测试自定义命名空间"""
        discovery = StevedoreServiceDiscovery(namespace="custom.services")
        assert discovery.namespace == "custom.services"
    
    def test_get_registry(self):
        """测试获取注册表"""
        registry = ServiceRegistry()
        discovery = StevedoreServiceDiscovery(registry=registry)
        
        assert discovery.get_registry() == registry
    
    def test_clear_registry(self):
        """测试清空注册表"""
        registry = ServiceRegistry()
        discovery = StevedoreServiceDiscovery(registry=registry)
        
        metadata = ServiceMetadata(name="test-service", version="1.0.0")
        
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
        registry.register("test-service", service, metadata)
        
        assert len(registry.list_services()) == 1
        
        discovery.clear_registry()
        assert len(registry.list_services()) == 0
    
    @patch('stevedore.ExtensionManager')
    def test_discover_with_no_services(self, mock_manager_class):
        """测试发现无服务"""
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([]))
        mock_manager_class.return_value = mock_manager
        
        discovery = StevedoreServiceDiscovery()
        discovered = discovery.discover()
        
        assert discovered == []
    
    @patch('stevedore.ExtensionManager')
    def test_discover_with_services(self, mock_manager_class):
        """测试发现服务"""
        # 创建模拟扩展
        ext1 = MagicMock()
        ext1.name = "user-service"
        ext1.entry_point = "user_service.plugin:UserServicePlugin"
        ext1.module_name = "user_service.plugin"
        ext1.attrs = ["UserServicePlugin"]
        
        ext2 = MagicMock()
        ext2.name = "order-service"
        ext2.entry_point = "order_service.plugin:OrderServicePlugin"
        ext2.module_name = "order_service.plugin"
        ext2.attrs = ["OrderServicePlugin"]
        
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([ext1, ext2]))
        mock_manager_class.return_value = mock_manager
        
        discovery = StevedoreServiceDiscovery()
        discovered = discovery.discover()
        
        assert len(discovered) == 2
        assert discovered[0]["name"] == "user-service"
        assert discovered[1]["name"] == "order-service"
    
    @patch('stevedore.ExtensionManager')
    def test_discover_no_matches(self, mock_manager_class):
        """测试无匹配项"""
        from stevedore.exception import NoMatches
        mock_manager_class.side_effect = NoMatches("No extensions found")
        
        discovery = StevedoreServiceDiscovery()
        discovered = discovery.discover()
        
        assert discovered == []
    
    @patch('stevedore.ExtensionManager')
    def test_discover_with_error(self, mock_manager_class):
        """测试发现过程出错"""
        mock_manager_class.side_effect = RuntimeError("Discovery error")
        
        discovery = StevedoreServiceDiscovery()
        
        with pytest.raises(ServiceDiscoveryError, match="发现服务扩展点失败"):
            discovery.discover()
    
    @patch('stevedore.ExtensionManager')
    def test_get_available_services(self, mock_manager_class):
        """测试获取可用服务列表"""
        # 创建模拟扩展
        ext1 = MagicMock()
        ext1.name = "user-service"
        
        ext2 = MagicMock()
        ext2.name = "order-service"
        
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([ext1, ext2]))
        mock_manager_class.return_value = mock_manager
        
        discovery = StevedoreServiceDiscovery()
        available = discovery.get_available_services()
        
        assert len(available) == 2
        assert "user-service" in available
        assert "order-service" in available
    
    @patch('stevedore.ExtensionManager')
    def test_load_and_register_with_plugin(self, mock_manager_class):
        """测试加载带有register方法的插件"""
        # 创建模拟扩展
        ext = MagicMock()
        ext.name = "user-service"
        
        # 创建模拟插件
        mock_plugin = MagicMock()
        mock_plugin.register = MagicMock()
        ext.plugin = Mock(return_value=mock_plugin)
        
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([ext]))
        mock_manager_class.return_value = mock_manager
        
        discovery = StevedoreServiceDiscovery()
        loaded = discovery.load_and_register()
        
        assert "user-service" in loaded
        mock_plugin.register.assert_called_once()
    
    @patch('stevedore.ExtensionManager')
    def test_load_and_register_with_service_instance(self, mock_manager_class):
        """测试加载带有register方法的插件"""
        # 创建模拟扩展
        ext = MagicMock()
        ext.name = "user-service"
        
        # 创建模拟插件
        mock_plugin = MagicMock()
        mock_plugin.register = MagicMock()
        ext.plugin = Mock(return_value=mock_plugin)
        
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([ext]))
        mock_manager_class.return_value = mock_manager
        
        discovery = StevedoreServiceDiscovery()
        loaded = discovery.load_and_register()
        
        assert "user-service" in loaded
        mock_plugin.register.assert_called_once()
    
    @patch('stevedore.ExtensionManager')
    def test_load_and_register_with_filter(self, mock_manager_class):
        """测试使用过滤器加载服务"""
        # 创建模拟扩展
        ext1 = MagicMock()
        ext1.name = "user-service"
        ext1.plugin = Mock(return_value=MagicMock(register=MagicMock()))
        
        ext2 = MagicMock()
        ext2.name = "admin-service"
        ext2.plugin = Mock(return_value=MagicMock(register=MagicMock()))
        
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([ext1, ext2]))
        mock_manager_class.return_value = mock_manager
        
        discovery = StevedoreServiceDiscovery()
        
        # 只加载非admin的服务
        loaded = discovery.load_and_register(filter_func=lambda name: not name.startswith("admin"))
        
        assert "user-service" in loaded
        assert "admin-service" not in loaded
    
    @patch('stevedore.ExtensionManager')
    def test_load_and_register_with_service_names(self, mock_manager_class):
        """测试指定服务名称加载"""
        # 创建模拟扩展
        ext1 = MagicMock()
        ext1.name = "user-service"
        ext1.plugin = Mock(return_value=MagicMock(register=MagicMock()))
        
        ext2 = MagicMock()
        ext2.name = "order-service"
        ext2.plugin = Mock(return_value=MagicMock(register=MagicMock()))
        
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([ext1, ext2]))
        mock_manager_class.return_value = mock_manager
        
        discovery = StevedoreServiceDiscovery()
        
        # 只加载指定的服务
        loaded = discovery.load_and_register(service_names=["user-service"])
        
        assert "user-service" in loaded
        assert "order-service" not in loaded
    
    @patch('stevedore.ExtensionManager')
    def test_reload_services(self, mock_manager_class):
        """测试重新加载服务"""
        # 创建模拟扩展
        ext = MagicMock()
        ext.name = "user-service"
        
        # 创建模拟插件，确保它有register方法
        mock_plugin = MagicMock()
        # 让register方法实际注册一个服务到注册表
        def mock_register_func(registry):
            registry.register("user-service", MagicMock(), ServiceMetadata(name="user-service", version="1.0.0"))
        mock_plugin.register = MagicMock(side_effect=mock_register_func)
        ext.plugin = Mock(return_value=mock_plugin)
        
        # 每次调用ExtensionManager都返回一个新的manager实例
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([ext]))
        mock_manager_class.return_value = mock_manager
        
        # 先加载一次
        discovery = StevedoreServiceDiscovery()
        loaded1 = discovery.load_and_register()
        assert "user-service" in loaded1
        
        # 模拟注册表中有数据
        discovery.registry.register("temp-service", MagicMock(), ServiceMetadata(name="temp", version="1.0.0"))
        
        # 重新创建扩展对象，因为之前的已经用过了
        ext = MagicMock()
        ext.name = "user-service"
        mock_plugin = MagicMock()
        mock_plugin.register = MagicMock(side_effect=mock_register_func)
        ext.plugin = Mock(return_value=mock_plugin)
        
        mock_manager = MagicMock()
        mock_manager.__iter__ = Mock(return_value=iter([ext]))
        mock_manager_class.return_value = mock_manager
        
        # 重新加载
        loaded2 = discovery.reload_services()
        
        # 之前的数据应该被清空
        assert not discovery.registry.exists("temp-service")
        assert "user-service" in loaded2