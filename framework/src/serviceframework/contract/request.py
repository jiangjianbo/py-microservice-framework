"""
服务请求模块

定义服务调用的请求契约，包含请求参数、上下文等信息。
请求对象在服务调用链中传递，支持位置透明性。
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from serviceframework.contract.service import ServiceContext


@dataclass
class ServiceRequest:
    """
    服务请求
    
    封装服务调用所需的所有信息，包括方法名、参数和上下文。
    请求对象可以序列化并通过不同传输方式传递。
    """
    
    service_name: str  # 目标服务名称
    method: str  # 调用的方法名
    args: tuple = field(default_factory=tuple)  # 位置参数
    kwargs: Dict[str, Any] = field(default_factory=dict)  # 关键字参数
    context: Optional[ServiceContext] = None  # 服务调用上下文
    timeout: Optional[float] = None  # 超时时间（秒）
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.service_name:
            raise ValueError("服务名称不能为空")
        if not self.method:
            raise ValueError("方法名不能为空")
        
        # 如果没有提供上下文，创建一个默认的
        if self.context is None:
            self.context = ServiceContext(
                service_name=self.service_name,
                method=self.method
            )
    
    def with_context(self, context: ServiceContext) -> "ServiceRequest":
        """
        创建带有新上下文的请求副本
        
        Args:
            context: 新的上下文
            
        Returns:
            带有新上下文的请求副本
        """
        return ServiceRequest(
            service_name=self.service_name,
            method=self.method,
            args=self.args,
            kwargs=self.kwargs,
            context=context,
            timeout=self.timeout
        )
    
    def with_args(self, *args, **kwargs) -> "ServiceRequest":
        """
        创建带有新参数的请求副本
        
        Args:
            *args: 新的位置参数
            **kwargs: 新的关键字参数
            
        Returns:
            带有新参数的请求副本
        """
        return ServiceRequest(
            service_name=self.service_name,
            method=self.method,
            args=args,
            kwargs=kwargs,
            context=self.context,
            timeout=self.timeout
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将请求转换为字典格式，便于序列化
        
        Returns:
            包含请求信息的字典
        """
        return {
            "service_name": self.service_name,
            "method": self.method,
            "args": self.args,
            "kwargs": self.kwargs,
            "context": {
                "service_name": self.context.service_name,
                "method": self.context.method,
                "request_id": self.context.request_id,
                "metadata": self.context.metadata
            } if self.context else None,
            "timeout": self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceRequest":
        """
        从字典创建请求对象
        
        Args:
            data: 包含请求信息的字典
            
        Returns:
            请求对象
        """
        context_data = data.get("context")
        context = None
        if context_data:
            context = ServiceContext(
                service_name=context_data["service_name"],
                method=context_data["method"],
                request_id=context_data.get("request_id", ""),
                metadata=context_data.get("metadata", {})
            )
        
        return cls(
            service_name=data["service_name"],
            method=data["method"],
            args=tuple(data.get("args", [])),
            kwargs=data.get("kwargs", {}),
            context=context,
            timeout=data.get("timeout")
        )