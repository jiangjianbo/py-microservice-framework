"""
服务代理模块

提供服务代理，实现服务调用的位置透明性。
代理通过传输层调用远程服务，屏蔽底层传输细节。
"""

from typing import Dict, Any, Optional
from serviceframework.transport.base import Transport


class ServiceProxy:
    """
    服务代理
    
    通过传输层调用目标服务，实现位置透明性。
    业务代码通过代理调用服务，无需关心服务是在本地还是远程。
    """
    
    def __init__(self, service_name: str, transport: Transport):
        """
        初始化服务代理
        
        Args:
            service_name: 目标服务名称
            transport: 传输对象
        """
        if not service_name:
            raise ValueError("服务名称不能为空")
        if transport is None:
            raise ValueError("传输对象不能为空")
            
        self.service_name = service_name
        self.transport = transport
    
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
            Exception: 传输或方法调用过程中的异常
        """
        return await self.transport.invoke(method, *args, **kwargs)
    
    def get_transport(self) -> Transport:
        """
        获取传输对象
        
        Returns:
            传输对象
        """
        return self.transport
    
    def get_service_name(self) -> str:
        """
        获取服务名称
        
        Returns:
            服务名称
        """
        return self.service_name
    
    def is_available(self) -> bool:
        """
        检查代理是否可用
        
        Returns:
            如果传输可用返回True，否则返回False
        """
        return self.transport.is_available()
    
    def get_endpoint(self) -> str:
        """
        获取端点信息
        
        Returns:
            端点信息字符串
        """
        return self.transport.get_endpoint()
    
    def __repr__(self) -> str:
        """代理的字符串表示"""
        return f"ServiceProxy(service_name='{self.service_name}', endpoint='{self.get_endpoint()}')"