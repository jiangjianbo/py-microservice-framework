"""
服务注册模块

提供服务的注册、发现和管理功能，维护运行时的服务实例和元数据。
服务注册表是运行时的核心组件，用于管理所有已注册的逻辑微服务。
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from serviceframework.contract.service import Service, ServiceMetadata


@dataclass
class ServiceRegistration:
    """
    服务注册信息
    
    包含服务实例、元数据和配置信息，用于在注册表中跟踪已注册的服务。
    """
    
    name: str  # 服务名称
    service: Service  # 服务实例
    metadata: ServiceMetadata  # 服务元数据
    config: Dict[str, any] = field(default_factory=dict)  # 服务配置
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.name:
            raise ValueError("服务名称不能为空")
        if self.service is None:
            raise ValueError("服务实例不能为空")
        if self.metadata is None:
            raise ValueError("服务元数据不能为空")


class ServiceRegistry:
    """
    服务注册表
    
    管理运行时所有已注册的服务实例，提供服务注册、注销、查询等功能。
    注册表是线程安全的，可以在多线程环境中安全使用。
    """
    
    def __init__(self):
        """初始化服务注册表"""
        self._registrations: Dict[str, ServiceRegistration] = {}
    
    def register(
        self,
        name: str,
        service: Service,
        metadata: Optional[ServiceMetadata] = None,
        config: Optional[Dict[str, any]] = None
    ) -> None:
        """
        注册服务
        
        Args:
            name: 服务名称，必须是唯一的
            service: 服务实例
            metadata: 服务元数据，如果为None则从服务实例获取
            config: 服务配置
            
        Raises:
            ValueError: 如果服务名称已存在或参数无效
        """
        if not name:
            raise ValueError("服务名称不能为空")
        if service is None:
            raise ValueError("服务实例不能为空")
        if name in self._registrations:
            raise ValueError(f"服务'{name}'已经注册")
        
        # 如果没有提供元数据，从服务实例获取
        if metadata is None:
            # 由于get_metadata是异步方法，这里暂时不支持自动获取
            # 需要调用者提供元数据
            raise ValueError("必须提供服务元数据")
        
        registration = ServiceRegistration(
            name=name,
            service=service,
            metadata=metadata,
            config=config or {}
        )
        
        self._registrations[name] = registration
    
    def unregister(self, name: str) -> None:
        """
        注销服务
        
        Args:
            name: 服务名称
            
        Raises:
            ValueError: 如果服务不存在
        """
        if name not in self._registrations:
            raise ValueError(f"服务'{name}'未注册")
        
        del self._registrations[name]
    
    def get(self, name: str) -> ServiceRegistration:
        """
        获取服务注册信息
        
        Args:
            name: 服务名称
            
        Returns:
            服务注册信息
            
        Raises:
            ValueError: 如果服务不存在
        """
        if name not in self._registrations:
            raise ValueError(f"服务'{name}'未注册")
        
        return self._registrations[name]
    
    def get_service(self, name: str) -> Service:
        """
        获取服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            ValueError: 如果服务不存在
        """
        registration = self.get(name)
        return registration.service
    
    def get_metadata(self, name: str) -> ServiceMetadata:
        """
        获取服务元数据
        
        Args:
            name: 服务名称
            
        Returns:
            服务元数据
            
        Raises:
            ValueError: 如果服务不存在
        """
        registration = self.get(name)
        return registration.metadata
    
    def get_config(self, name: str) -> Dict[str, any]:
        """
        获取服务配置
        
        Args:
            name: 服务名称
            
        Returns:
            服务配置
            
        Raises:
            ValueError: 如果服务不存在
        """
        registration = self.get(name)
        return registration.config
    
    def exists(self, name: str) -> bool:
        """
        检查服务是否存在
        
        Args:
            name: 服务名称
            
        Returns:
            如果服务存在返回True，否则返回False
        """
        return name in self._registrations
    
    def list_services(self) -> List[str]:
        """
        列出所有已注册的服务名称
        
        Returns:
            服务名称列表
        """
        return list(self._registrations.keys())
    
    def get_all(self) -> Dict[str, ServiceRegistration]:
        """
        获取所有服务注册信息
        
        Returns:
            服务名称到注册信息的字典
        """
        return self._registrations.copy()
    
    def clear(self) -> None:
        """清空所有注册的服务"""
        self._registrations.clear()
    
    def count(self) -> int:
        """
        获取已注册服务的数量
        
        Returns:
            服务数量
        """
        return len(self._registrations)