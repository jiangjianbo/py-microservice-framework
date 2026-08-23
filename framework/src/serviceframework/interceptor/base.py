"""
服务拦截器基础模块

定义服务拦截器的抽象接口和上下文，用于实现横切关注点。
拦截器是统一横切抽象，支持认证、授权、审计、追踪等功能。
"""

from typing import Protocol, Any, Optional, Dict
from dataclasses import dataclass, field
from serviceframework.contract.service import ServiceContext


class InterceptorContext:
    """
    拦截器上下文
    
    包含服务调用的完整上下文信息，在拦截器链中传递。
    拦截器可以通过修改上下文来影响后续处理流程。
    """
    
    def __init__(
        self,
        service_context: ServiceContext,
        method: str,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        初始化拦截器上下文
        
        Args:
            service_context: 服务上下文
            method: 调用的方法名
            args: 位置参数
            kwargs: 关键字参数
            metadata: 额外元数据
        """
        self.service_context = service_context
        self.method = method
        self.args = args
        self.kwargs = kwargs or {}
        self.metadata = metadata or {}
        self._result: Optional[Any] = None
        self._error: Optional[Exception] = None
        self.skip_execution: bool = False
        self._metadata_changes: Dict[str, Any] = {}
    
    @property
    def result(self) -> Optional[Any]:
        """
        获取调用结果
        
        Returns:
            调用结果，如果还没执行则为None
        """
        return self._result
    
    @result.setter
    def result(self, value: Any) -> None:
        """
        设置调用结果
        
        Args:
            value: 调用结果
        """
        self._result = value
    
    @property
    def error(self) -> Optional[Exception]:
        """
        获取错误
        
        Returns:
        错误信息，如果没有错误则为None
        """
        return self._error
    
    @error.setter
    def error(self, value: Exception) -> None:
        """
        设置错误
        
        Args:
            value: 错误信息
        """
        self._error = value
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        添加元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
        self._metadata_changes[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        获取元数据
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值或默认值
        """
        return self.metadata.get(key, default)
    
    def has_metadata(self, key: str) -> bool:
        """
        检查是否存在元数据
        
        Args:
            key: 元数据键
            
        Returns:
            如果存在返回True，否则返回False
        """
        return key in self.metadata
    
    def get_metadata_changes(self) -> Dict[str, Any]:
        """
        获取元数据变更
        
        Returns:
            当前拦截器链中添加或修改的元数据
        """
        return self._metadata_changes.copy()
    
    def copy(self) -> "InterceptorContext":
        """
        复制上下文
        
        Returns:
            新的上下文副本
        """
        return InterceptorContext(
            service_context=self.service_context,
            method=self.method,
            args=self.args,
            kwargs=self.kwargs.copy(),
            metadata=self.metadata.copy()
        )


class ServiceInterceptor(Protocol):
    """
    服务拦截器协议
    
    定义服务拦截器的接口，所有拦截器都需要实现此协议。
    拦截器可以在服务调用前后插入逻辑，实现横切关注点。
    """
    
    async def before(self, context: InterceptorContext) -> None:
        """
        在服务调用前执行
        
        Args:
            context: 拦截器上下文
        """
        ...
    
    async def after(self, context: InterceptorContext, result: Any) -> None:
        """
        在服务调用成功后执行
        
        Args:
            context: 拦截器上下文
            result: 调用结果
        """
        ...
    
    async def on_error(self, context: InterceptorContext, error: Exception) -> None:
        """
        在服务调用失败时执行
        
        Args:
            context: 拦截器上下文
            error: 异常信息
        """
        ...