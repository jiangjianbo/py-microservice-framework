"""
服务生命周期管理模块

提供服务生命周期管理，包括服务注册、初始化、启动、停止等功能。
生命周期管理器确保服务按照正确的顺序和状态进行转换。
"""

import asyncio
from typing import List, Dict, Optional
from enum import Enum
from serviceframework.contract.service import Service, ServiceMetadata


class LifecycleState(Enum):
    """
    服务生命周期状态
    
    定义服务的生命周期状态和转换规则：
    - DISCOVERED: 服务被发现但未加载
    - LOADED: 服务已加载
    - CONFIGURED: 服务已配置
    - INITIALIZED: 服务已初始化
    - STARTED: 服务已启动
    - READY: 服务已就绪
    - STOPPING: 服务正在停止
    - STOPPED: 服务已停止
    - FAILED: 服务失败
    """
    DISCOVERED = "discovered"
    LOADED = "loaded"
    CONFIGURED = "configured"
    INITIALIZED = "initialized"
    STARTED = "started"
    READY = "ready"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class LifecycleError(Exception):
    """
    生命周期错误
    
    当生命周期操作失败时抛出此异常。
    """
    
    def __init__(self, message: str, code: Optional[str] = None):
        """
        初始化生命周期错误
        
        Args:
            message: 错误消息
            code: 错误码
        """
        super().__init__(message)
        self.message = message
        self.code = code or "LIFECYCLE_ERROR"


class LifecycleManager:
    """
    生命周期管理器
    
    负责管理所有服务的生命周期，包括注册、初始化、启动、停止等操作。
    """
    
    def __init__(self):
        """初始化生命周期管理器"""
        self._services: List[Service] = []
        self._state: LifecycleState = LifecycleState.DISCOVERED
        self._service_metadata: Dict[Service, ServiceMetadata] = {}
    
    def get_state(self) -> LifecycleState:
        """
        获取当前状态
        
        Returns:
            当前生命周期状态
        """
        return self._state
    
    def get_services(self) -> List[Service]:
        """
        获取所有服务
        
        Returns:
            服务列表
        """
        return self._services.copy()
    
    def register_service(self, service: Service) -> None:
        """
        注册服务
        
        Args:
            service: 服务实例
            
        Raises:
            ValueError: 如果服务已注册或状态转换无效
        """
        if service in self._services:
            raise ValueError(f"服务'{service.__class__.__name__}'已经注册")
        
        self._services.append(service)
        self._state = LifecycleState.LOADED
    
    async def get_metadata(self, service: Service) -> ServiceMetadata:
        """
        获取服务元数据
        
        Args:
            service: 服务实例
            
        Returns:
            服务元数据
        """
        if service not in self._service_metadata:
            self._service_metadata[service] = await service.get_metadata()
        
        return self._service_metadata[service]
    
    async def initialize(self) -> None:
        """
        初始化所有服务
        
        执行所有服务的初始化操作。
        
        Raises:
            LifecycleError: 如果初始化失败
        """
        if not self._is_valid_transition(LifecycleState.INITIALIZED):
            raise LifecycleError(
                f"无法从{self._state.value}状态转换到initialized状态",
                "INVALID_STATE_TRANSITION"
            )
        
        for service in self._services:
            try:
                await service.initialize()
            except Exception as e:
                self._state = LifecycleState.FAILED
                raise LifecycleError(
                    f"初始化服务'{service.__class__.__name__}'失败: {str(e)}",
                    "INITIALIZATION_FAILED"
                ) from e
        
        self._state = LifecycleState.INITIALIZED
    
    async def start(self) -> None:
        """
        启动所有服务
        
        执行所有服务的启动操作。
        
        Raises:
            LifecycleError: 如果启动失败
        """
        if not self._is_valid_transition(LifecycleState.STARTED):
            raise LifecycleError(
                f"无法从{self._state.value}状态转换到started状态",
                "INVALID_STATE_TRANSITION"
            )
        
        for service in self._services:
            try:
                # 如果服务有start方法，调用它
                if hasattr(service, 'start') and callable(getattr(service, 'start')):
                    await service.start()
            except Exception as e:
                self._state = LifecycleState.FAILED
                raise LifecycleError(
                    f"启动服务'{service.__class__.__name__}'失败: {str(e)}",
                    "START_FAILED"
                ) from e
        
        self._state = LifecycleState.STARTED
    
    async def mark_ready(self) -> None:
        """
        标记所有服务为就绪状态
        
        Raises:
            LifecycleError: 如果状态转换无效
        """
        if not self._is_valid_transition(LifecycleState.READY):
            raise LifecycleError(
                f"无法从{self._state.value}状态转换到ready状态",
                "INVALID_STATE_TRANSITION"
            )
        
        # 检查所有服务的健康状态
        health_ok = await self.health_check()
        if not health_ok:
            raise LifecycleError(
                "服务健康检查失败",
                "HEALTH_CHECK_FAILED"
            )
        
        self._state = LifecycleState.READY
    
    async def stop(self) -> None:
        """
        停止所有服务
        
        执行所有服务的停止操作。
        
        Raises:
            LifecycleError: 如果停止失败
        """
        if not self._is_valid_transition(LifecycleState.STOPPING):
            raise LifecycleError(
                f"无法从{self._state.value}状态转换到stopping状态",
                "INVALID_STATE_TRANSITION"
            )
        
        self._state = LifecycleState.STOPPING
        
        # 反向停止服务
        for service in reversed(self._services):
            try:
                await service.shutdown()
            except Exception as e:
                raise LifecycleError(
                    f"停止服务'{service.__class__.__name__}'失败: {str(e)}",
                    "STOP_FAILED"
                ) from e
        
        self._state = LifecycleState.STOPPED
    
    async def health_check(self) -> bool:
        """
        检查所有服务的健康状态
        
        Returns:
            如果所有服务都健康返回True，否则返回False
        """
        all_healthy = True
        
        for service in self._services:
            try:
                healthy = await service.health_check()
                if not healthy:
                    all_healthy = False
            except Exception:
                all_healthy = False
        
        return all_healthy
    
    def _is_valid_transition(self, target_state: LifecycleState) -> bool:
        """
        检查状态转换是否有效
        
        Args:
            target_state: 目标状态
            
        Returns:
            如果转换有效返回True，否则返回False
        """
        valid_transitions = {
            LifecycleState.DISCOVERED: [LifecycleState.LOADED],
            LifecycleState.LOADED: [LifecycleState.INITIALIZED],
            LifecycleState.INITIALIZED: [LifecycleState.STARTED],
            LifecycleState.STARTED: [LifecycleState.READY, LifecycleState.STOPPING],
            LifecycleState.READY: [LifecycleState.STOPPING],
            LifecycleState.STOPPING: [LifecycleState.STOPPED],
            LifecycleState.STOPPED: [],
            LifecycleState.FAILED: [LifecycleState.STOPPING],
        }
        
        valid_targets = valid_transitions.get(self._state, [])
        return target_state in valid_targets
    
    async def restart(self) -> None:
        """
        重启所有服务
        
        先停止所有服务，然后重新启动。
        
        Raises:
            LifecycleError: 如果重启失败
        """
        await self.stop()
        
        # 短暂等待
        await asyncio.sleep(0.1)
        
        await self.initialize()
        await self.start()
        await self.mark_ready()
    
    def count_services(self) -> int:
        """
        获取服务数量
        
        Returns:
            服务数量
        """
        return len(self._services)