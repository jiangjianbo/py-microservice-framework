"""
传输基础模块

定义服务传输的抽象接口，支持不同的传输实现（本地、远程等）。
传输层负责将服务调用请求传递到目标服务实例。
"""

from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """
    传输协议
    
    定义服务传输的基本接口，所有传输实现都需要遵循此协议。
    传输层负责将调用请求传递到目标服务，并返回结果。
    """
    
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
        ...
    
    def is_available(self) -> bool:
        """
        检查传输是否可用
        
        Returns:
            如果传输可用返回True，否则返回False
        """
        ...
    
    def get_endpoint(self) -> str:
        """
        获取传输端点信息
        
        Returns:
            传输端点的字符串表示
        """
        ...