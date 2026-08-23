"""
依赖注入容器模块单元测试

测试依赖注入容器的各种场景和边界情况。
"""

import pytest
from serviceframework.runtime.di import DependencyContainer, Scope


class TestDependencyContainer:
    
    def test_container_creation(self):
        """测试容器创建"""
        container = DependencyContainer()
        assert container is not None
    
    def test_register_singleton(self):
        """测试注册单例依赖"""
        container = DependencyContainer()
        
        class Database:
            def __init__(self):
                self.connected = False
        
        # 注册单例
        container.register(Database, scope=Scope.SINGLETON)
        
        # 解析两次，应该是同一个实例
        db1 = container.resolve(Database)
        db2 = container.resolve(Database)
        
        assert db1 is db2
    
    def test_register_transient(self):
        """测试注册瞬态依赖"""
        container = DependencyContainer()
        
        class Database:
            def __init__(self):
                self.connected = False
        
        # 注册瞬态
        container.register(Database, scope=Scope.TRANSIENT)
        
        # 解析两次，应该是不同的实例
        db1 = container.resolve(Database)
        db2 = container.resolve(Database)
        
        assert db1 is not db2
    
    def test_register_with_factory(self):
        """测试使用工厂函数注册"""
        container = DependencyContainer()
        
        class Database:
            def __init__(self, connection_string: str):
                self.connection_string = connection_string
        
        # 使用工厂函数注册
        container.register(
            Database,
            factory=lambda: Database("localhost:5432"),
            scope=Scope.SINGLETON
        )
        
        db = container.resolve(Database)
        assert db.connection_string == "localhost:5432"
    
    def test_register_with_instance(self):
        """测试注册已有实例"""
        container = DependencyContainer()
        
        class Database:
            def __init__(self):
                self.connected = True
        
        db = Database()
        
        # 注册已有实例
        container.register_instance(Database, db)
        
        # 解析应该是同一个实例
        resolved_db = container.resolve(Database)
        assert resolved_db is db
        assert resolved_db.connected is True
    
    def test_resolve_with_dependencies(self):
        """测试解析具有依赖的类"""
        container = DependencyContainer()
        
        class Database:
            def __init__(self):
                self.connected = True
        
        class UserRepository:
            def __init__(self, db: Database):
                self.db = db
        
        # 注册依赖
        container.register(Database, scope=Scope.SINGLETON)
        container.register(UserRepository, scope=Scope.SINGLETON)
        
        # 解析
        repo = container.resolve(UserRepository)
        
        assert repo is not None
        assert repo.db is not None
        assert repo.db.connected is True
    
    def test_resolve_nonexistent_dependency(self):
        """测试解析不存在的依赖"""
        container = DependencyContainer()
        
        class Nonexistent:
            pass
        
        with pytest.raises(ValueError, match="依赖'Nonexistent'未注册"):
            container.resolve(Nonexistent)
    
    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        container = DependencyContainer()
        
        class ServiceA:
            def __init__(self, service_b: "ServiceB"):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        # 注册循环依赖
        container.register(ServiceA, scope=Scope.SINGLETON)
        container.register(ServiceB, scope=Scope.SINGLETON)
        
        # 应该检测到循环依赖
        with pytest.raises(ValueError, match="检测到循环依赖"):
            container.resolve(ServiceA)
    
    def test_unregister_dependency(self):
        """测试注销依赖"""
        container = DependencyContainer()
        
        class Database:
            def __init__(self):
                self.connected = True
        
        container.register(Database, scope=Scope.SINGLETON)
        
        # 应该能够解析
        db = container.resolve(Database)
        assert db is not None
        
        # 注销依赖
        container.unregister(Database)
        
        # 不应该能够解析
        with pytest.raises(ValueError, match="依赖'Database'未注册"):
            container.resolve(Database)
    
    def test_clear_dependencies(self):
        """测试清空所有依赖"""
        container = DependencyContainer()
        
        class Database:
            pass
        
        class Cache:
            pass
        
        container.register(Database, scope=Scope.SINGLETON)
        container.register(Cache, scope=Scope.SINGLETON)
        
        # 清空依赖
        container.clear()
        
        # 都不应该能够解析
        with pytest.raises(ValueError, match="依赖'Database'未注册"):
            container.resolve(Database)
        
        with pytest.raises(ValueError, match="依赖'Cache'未注册"):
            container.resolve(Cache)
    
    def test_check_registered(self):
        """测试检查依赖是否已注册"""
        container = DependencyContainer()
        
        class Database:
            pass
        
        assert not container.is_registered(Database)
        
        container.register(Database, scope=Scope.SINGLETON)
        
        assert container.is_registered(Database)
    
    def test_get_registered_types(self):
        """测试获取所有已注册的类型"""
        container = DependencyContainer()
        
        class Database:
            pass
        
        class Cache:
            pass
        
        container.register(Database, scope=Scope.SINGLETON)
        container.register(Cache, scope=Scope.SINGLETON)
        
        registered = container.get_registered_types()
        
        assert Database in registered
        assert Cache in registered
        assert len(registered) == 2


class TestScope:
    
    def test_scope_values(self):
        """测试Scope枚举值"""
        assert hasattr(Scope, 'SINGLETON')
        assert hasattr(Scope, 'TRANSIENT')
        assert hasattr(Scope, 'SCOPED')