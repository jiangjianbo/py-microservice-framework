"""
本地进程内传输模块

实现同一进程内的服务调用，直接调用服务实例的方法，无需网络通信。
这是最高效的传输方式，适合开发和小规模部署场景。
"""

import inspect
from typing import Any
from serviceframework.contract.service import Service
from serviceframework.transport.base import Transport


class LocalTransport:
    """
    本地进程内传输
    
    直接调用服务实例的方法，适用于同一进程内的服务调用。
    这种传输方式最高效，没有网络开销，适合开发和测试环境。
    """
    
    def __init__(self, service: Service):
        """
        初始化本地传输
        
        Args:
            service: 目标服务实例
        """
        self.service = service
    
    async def invoke(
        self,
        method: str,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        调用目标服务的方法
        
        Args:
            method: 方法名
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            方法调用的结果
            
        Raises:
            AttributeError: 如果方法不存在
            Exception: 方法执行过程中的异常
        """
        if not hasattr(self.service, method):
            raise AttributeError(
                f"'{self.service.__class__.__name__}' object has no attribute '{method}'"
            )
        
        # 获取方法
        method_obj = getattr(self.service, method)
        
        # 检查是否是方法
        if not callable(method_obj):
            raise AttributeError(
                f"'{method}' is not a callable method of '{self.service.__class__.__name__}'"
            )
        
        # 调用方法
        if inspect.iscoroutinefunction(method_obj):
            # 异步方法
            result = await method_obj(*args, **kwargs)
        else:
            # 同步方法
            result = method_obj(*args, **kwargs)
        
        return result
    
    def is_available(self) -> bool:
        """
        检查传输是否可用
        
        Returns:
            本地传输总是可用，返回True
        """
        return True
    
    def get_endpoint(self) -> str:
        """
        获取传输端点信息
        
        Returns:
            本地传输的端点表示
        """
        return f"local:{self.service.__class__.__name__}"