"""
服务注册模块单元测试

测试服务注册表的各种场景和边界情况。
"""

import pytest
from serviceframework.contract.service import Service, ServiceMetadata
from serviceframework.registry.registry import ServiceRegistry, ServiceRegistration
from dataclasses import dataclass


class TestServiceRegistration:
    
    def test_service_registration_creation(self):
        """测试服务注册信息创建"""
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
        registration = ServiceRegistration(
            name="user-service",
            service=service,
            metadata=metadata
        )
        
        assert registration.name == "user-service"
        assert registration.service == service
        assert registration.metadata == metadata
    
    def test_service_registration_with_config(self):
        """测试带配置的服务注册信息创建"""
        metadata = ServiceMetadata(name="order-service", version="1.0.0")
        
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
        config = {"mode": "inprocess", "timeout": 30}
        registration = ServiceRegistration(
            name="order-service",
            service=service,
            metadata=metadata,
            config=config
        )
        
        assert registration.config["mode"] == "inprocess"
        assert registration.config["timeout"] == 30


class TestServiceRegistry:
    
    def test_registry_creation(self):
        """测试服务注册表创建"""
        registry = ServiceRegistry()
        assert len(registry.list_services()) == 0
    
    def test_register_service(self):
        """测试注册服务"""
        registry = ServiceRegistry()
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
        registry.register("user-service", service, metadata)
        
        assert len(registry.list_services()) == 1
        assert "user-service" in registry.list_services()
    
    def test_register_duplicate_service(self):
        """测试注册重复服务"""
        registry = ServiceRegistry()
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
        
        service1 = MockService()
        service2 = MockService()
        registry.register("user-service", service1, metadata)
        
        with pytest.raises(ValueError, match="服务'user-service'已经注册"):
            registry.register("user-service", service2, metadata)
    
    def test_unregister_service(self):
        """测试注销服务"""
        registry = ServiceRegistry()
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
        registry.register("user-service", service, metadata)
        assert len(registry.list_services()) == 1
        
        registry.unregister("user-service")
        assert len(registry.list_services()) == 0
    
    def test_unregister_nonexistent_service(self):
        """测试注销不存在的服务"""
        registry = ServiceRegistry()
        with pytest.raises(ValueError, match="服务'nonexistent'未注册"):
            registry.unregister("nonexistent")
    
    def test_get_service(self):
        """测试获取服务"""
        registry = ServiceRegistry()
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
        registry.register("user-service", service, metadata)
        
        retrieved = registry.get("user-service")
        assert retrieved.service == service
        assert retrieved.metadata == metadata
    
    def test_get_nonexistent_service(self):
        """测试获取不存在的服务"""
        registry = ServiceRegistry()
        with pytest.raises(ValueError, match="服务'nonexistent'未注册"):
            registry.get("nonexistent")
    
    def test_check_service_exists(self):
        """测试检查服务是否存在"""
        registry = ServiceRegistry()
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
        assert not registry.exists("user-service")
        
        registry.register("user-service", service, metadata)
        assert registry.exists("user-service")
    
    def test_get_service_metadata(self):
        """测试获取服务元数据"""
        registry = ServiceRegistry()
        metadata = ServiceMetadata(name="user-service", version="1.0.0", description="用户服务")
        
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
        registry.register("user-service", service, metadata)
        
        retrieved_metadata = registry.get_metadata("user-service")
        assert retrieved_metadata.description == "用户服务"
    
    def test_list_services(self):
        """测试列出所有服务"""
        registry = ServiceRegistry()
        
        for i in range(3):
            name = f"service-{i}"
            metadata = ServiceMetadata(name=name, version="1.0.0")
            
            @dataclass
            class MockService(Service):
                service_name: str = name
                
                async def get_metadata(self) -> ServiceMetadata:
                    return ServiceMetadata(name=self.service_name, version="1.0.0")
                
                async def health_check(self) -> bool:
                    return True
                
                async def initialize(self) -> None:
                    pass
                
                async def shutdown(self) -> None:
                    pass
            
            service = MockService()
            registry.register(name, service, metadata)
        
        services = registry.list_services()
        assert len(services) == 3
        assert "service-0" in services
        assert "service-1" in services
        assert "service-2" in services
    
    def test_get_all_registrations(self):
        """测试获取所有注册信息"""
        registry = ServiceRegistry()
        
        for i in range(2):
            name = f"service-{i}"
            metadata = ServiceMetadata(name=name, version="1.0.0")
            
            @dataclass
            class MockService(Service):
                service_name: str = name
                
                async def get_metadata(self) -> ServiceMetadata:
                    return ServiceMetadata(name=self.service_name, version="1.0.0")
                
                async def health_check(self) -> bool:
                    return True
                
                async def initialize(self) -> None:
                    pass
                
                async def shutdown(self) -> None:
                    pass
            
            service = MockService()
            registry.register(name, service, metadata)
        
        registrations = registry.get_all()
        assert len(registrations) == 2
        assert "service-0" in registrations
        assert "service-1" in registrations
    
    def test_clear_services(self):
        """测试清空所有服务"""
        registry = ServiceRegistry()
        
        for i in range(3):
            name = f"service-{i}"
            metadata = ServiceMetadata(name=name, version="1.0.0")
            
            @dataclass
            class MockService(Service):
                service_name: str = name
                
                async def get_metadata(self) -> ServiceMetadata:
                    return ServiceMetadata(name=self.service_name, version="1.0.0")
                
                async def health_check(self) -> bool:
                    return True
                
                async def initialize(self) -> None:
                    pass
                
                async def shutdown(self) -> None:
                    pass
            
            service = MockService()
            registry.register(name, service, metadata)
        
        assert len(registry.list_services()) == 3
        
        registry.clear()
        assert len(registry.list_services()) == 0