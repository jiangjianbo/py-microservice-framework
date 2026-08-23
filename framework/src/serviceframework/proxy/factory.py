"""
服务代理工厂模块

提供服务代理的创建和管理，支持代理实例的复用和生命周期管理。
工厂类负责根据服务名称创建对应的代理实例。
"""

from typing import Dict
from serviceframework.contract.service import Service
from serviceframework.proxy.proxy import ServiceProxy
from serviceframework.transport.base import Transport
from serviceframework.transport.local import LocalTransport


class ProxyFactory:
    """
    代理工厂
    
    负责创建和管理服务代理，支持代理实例的复用。
    同一个服务名称的代理只会创建一次，后续调用会返回同一个实例。
    """
    
    def __init__(self):
        """初始化代理工厂"""
        self._proxies: Dict[str, ServiceProxy] = {}
    
    def create_proxy(
        self,
        service_name: str,
        transport: Transport
    ) -> ServiceProxy:
        """
        创建服务代理
        
        如果已存在相同服务名称的代理，则返回现有实例。
        
        Args:
            service_name: 服务名称
            transport: 传输对象
            
        Returns:
            服务代理实例
        """
        if not service_name:
            raise ValueError("服务名称不能为空")
        if transport is None:
            raise ValueError("传输对象不能为空")
        
        # 如果已存在，返回现有实例
        if service_name in self._proxies:
            return self._proxies[service_name]
        
        # 创建新代理
        proxy = ServiceProxy(service_name, transport)
        self._proxies[service_name] = proxy
        return proxy
    
    def create_local_proxy(
        self,
        service_name: str,
        service: Service
    ) -> ServiceProxy:
        """
        创建本地代理
        
        使用LocalTransport创建代理，适用于同一进程内的服务调用。
        
        Args:
            service_name: 服务名称
            service: 服务实例
            
        Returns:
            服务代理实例
        """
        transport = LocalTransport(service)
        return self.create_proxy(service_name, transport)
    
    def get_proxy(self, service_name: str) -> ServiceProxy:
        """
        获取已创建的代理
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务代理实例
            
        Raises:
            ValueError: 如果代理不存在
        """
        if service_name not in self._proxies:
            raise ValueError(f"代理'{service_name}'不存在")
        
        return self._proxies[service_name]
    
    def has_proxy(self, service_name: str) -> bool:
        """
        检查代理是否存在
        
        Args:
            service_name: 服务名称
            
        Returns:
            如果代理存在返回True，否则返回False
        """
        return service_name in self._proxies
    
    def remove_proxy(self, service_name: str) -> None:
        """
        移除代理
        
        Args:
            service_name: 服务名称
            
        Raises:
            ValueError: 如果代理不存在
        """
        if service_name not in self._proxies:
            raise ValueError(f"代理'{service_name}'不存在")
        
        del self._proxies[service_name]
    
    def clear_proxies(self) -> None:
        """清空所有代理"""
        self._proxies.clear()
    
    def count_proxies(self) -> int:
        """
        获取代理数量
        
        Returns:
            代理数量
        """
        return len(self._proxies)
    
    def list_proxies(self) -> list[str]:
        """
        列出所有代理的服务名称
        
        Returns:
            服务名称列表
        """
        return list(self._proxies.keys())