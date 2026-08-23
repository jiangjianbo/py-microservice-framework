"""
服务生命周期模块单元测试

测试服务生命周期的各种场景和边界情况。
"""

import pytest
import asyncio
from serviceframework.runtime.lifecycle import LifecycleManager, LifecycleState, LifecycleError
from serviceframework.contract.service import Service, ServiceMetadata
from dataclasses import dataclass


class TestLifecycleState:
    
    def test_lifecycle_state_values(self):
        """测试生命周期状态值"""
        assert hasattr(LifecycleState, 'DISCOVERED')
        assert hasattr(LifecycleState, 'LOADED')
        assert hasattr(LifecycleState, 'CONFIGURED')
        assert hasattr(LifecycleState, 'INITIALIZED')
        assert hasattr(LifecycleState, 'STARTED')
        assert hasattr(LifecycleState, 'READY')
        assert hasattr(LifecycleState, 'STOPPING')
        assert hasattr(LifecycleState, 'STOPPED')
        assert hasattr(LifecycleState, 'FAILED')
    
    def test_lifecycle_state_transitions(self):
        """测试生命周期状态转换"""
        manager = LifecycleManager()
        
        # 初始状态
        assert manager.get_state() == LifecycleState.DISCOVERED


class TestLifecycleError:
    
    def test_lifecycle_error_creation(self):
        """测试生命周期错误创建"""
        error = LifecycleError("服务启动失败", "START_FAILED")
        assert str(error) == "服务启动失败"
        assert error.code == "START_FAILED"
        assert error.message == "服务启动失败"


class TestLifecycleManager:
    
    def test_manager_creation(self):
        """测试生命周期管理器创建"""
        manager = LifecycleManager()
        assert manager is not None
        assert manager.get_state() == LifecycleState.DISCOVERED
    
    @pytest.mark.asyncio
    async def test_service_registration(self):
        """测试服务注册"""
        manager = LifecycleManager()
        
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
        manager.register_service(service)
        
        assert manager.get_state() == LifecycleState.LOADED
        assert len(manager.get_services()) == 1
    
    @pytest.mark.asyncio
    async def test_service_lifecycle_transitions(self):
        """测试服务生命周期转换"""
        manager = LifecycleManager()
        
        metadata = ServiceMetadata(name="user-service", version="1.0.0")
        
        calls = []
        
        @dataclass
        class MockService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                calls.append("get_metadata")
                return metadata
            
            async def health_check(self) -> bool:
                calls.append("health_check")
                return True
            
            async def initialize(self) -> None:
                calls.append("initialize")
            
            async def shutdown(self) -> None:
                calls.append("shutdown")
        
        service = MockService()
        manager.register_service(service)
        
        # 执行完整生命周期
        await manager.initialize()
        assert manager.get_state() == LifecycleState.INITIALIZED
        assert "initialize" in calls
        
        await manager.start()
        assert manager.get_state() == LifecycleState.STARTED
        
        await manager.mark_ready()
        assert manager.get_state() == LifecycleState.READY
        
        await manager.stop()
        assert manager.get_state() == LifecycleState.STOPPED
        assert "shutdown" in calls
    
    @pytest.mark.asyncio
    async def test_service_health_check(self):
        """测试服务健康检查"""
        manager = LifecycleManager()
        
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
        manager.register_service(service)
        
        # 执行生命周期
        await manager.initialize()
        await manager.start()
        await manager.mark_ready()
        
        # 健康检查
        health = await manager.health_check()
        assert health is True
    
    @pytest.mark.asyncio
    async def test_multiple_services_lifecycle(self):
        """测试多个服务的生命周期管理"""
        manager = LifecycleManager()
        
        for i in range(3):
            metadata = ServiceMetadata(name=f"service-{i}", version="1.0.0")
            
            @dataclass
            class MockService(Service):
                service_name: str = f"service-{i}"
                
                async def get_metadata(self) -> ServiceMetadata:
                    return metadata
                
                async def health_check(self) -> bool:
                    return True
                
                async def initialize(self) -> None:
                    pass
                
                async def shutdown(self) -> None:
                    pass
            
            service = MockService()
            manager.register_service(service)
        
        # 执行完整生命周期
        await manager.initialize()
        await manager.start()
        await manager.mark_ready()
        
        # 检查所有服务状态
        health = await manager.health_check()
        assert health is True
        
        await manager.stop()
        assert manager.get_state() == LifecycleState.STOPPED
    
    @pytest.mark.asyncio
    async def test_service_failure_handling(self):
        """测试服务失败处理"""
        manager = LifecycleManager()
        
        metadata = ServiceMetadata(name="failing-service", version="1.0.0")
        
        @dataclass
        class FailingService(Service):
            async def get_metadata(self) -> ServiceMetadata:
                return metadata
            
            async def health_check(self) -> bool:
                return False  # 不健康
            
            async def initialize(self) -> None:
                pass
            
            async def shutdown(self) -> None:
                pass
        
        service = FailingService()
        manager.register_service(service)
        
        # 执行生命周期
        await manager.initialize()
        await manager.start()
        
        # 健康检查应该失败并抛出异常
        with pytest.raises(LifecycleError, match="服务健康检查失败"):
            await manager.mark_ready()
        
        # 手动停止服务
        await manager.stop()
        assert manager.get_state() == LifecycleState.STOPPED
    
    @pytest.mark.asyncio
    async def test_state_transitions_valid(self):
        """测试有效的状态转换"""
        manager = LifecycleManager()
        
        # 测试有效转换
        valid_transitions = [
            (LifecycleState.DISCOVERED, LifecycleState.LOADED),
            (LifecycleState.LOADED, LifecycleState.INITIALIZED),
            (LifecycleState.INITIALIZED, LifecycleState.STARTED),
            (LifecycleState.STARTED, LifecycleState.READY),
            (LifecycleState.READY, LifecycleState.STOPPING),
            (LifecycleState.STOPPING, LifecycleState.STOPPED),
        ]
        
        for from_state, to_state in valid_transitions:
            # 模拟状态转换
            manager._state = from_state
            # 检查转换是否有效
            assert manager._is_valid_transition(to_state)
    
    @pytest.mark.asyncio
    async def test_state_transitions_invalid(self):
        """测试无效的状态转换"""
        manager = LifecycleManager()
        
        # 设置为已停止状态
        manager._state = LifecycleState.STOPPED
        
        # 尝试转换到已就绪状态，应该失败
        assert not manager._is_valid_transition(LifecycleState.READY)