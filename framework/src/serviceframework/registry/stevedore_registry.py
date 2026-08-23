"""
Stevedore服务发现模块

使用Python Entry Points实现服务的自动发现和加载，实现动态扩展能力。
Stevedore提供基于命名空间的扩展点加载机制，适合作为服务发现的基础实现。
"""

import stevedore
from typing import List, Dict, Any, Optional, Callable
from serviceframework.contract.service import Service, ServiceMetadata
from serviceframework.registry.registry import ServiceRegistry


class ServiceDiscoveryError(Exception):
    """
    服务发现错误
    
    当服务发现过程中出现问题时抛出此异常。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class StevedoreServiceDiscovery:
    """
    基于Stevedore的服务发现器
    
    通过Python Entry Points自动发现和加载逻辑微服务。
    支持自定义命名空间和服务加载逻辑。
    """
    
    DEFAULT_NAMESPACE = "backend.services"
    
    def __init__(
        self,
        namespace: str = DEFAULT_NAMESPACE,
        registry: Optional[ServiceRegistry] = None
    ):
        """
        初始化服务发现器
        
        Args:
            namespace: Entry Points命名空间
            registry: 服务注册表，如果为None则创建新的
        """
        self.namespace = namespace
        self.registry = registry or ServiceRegistry()
        self._extensions: Optional[stevedore.ExtensionManager] = None
    
    def discover(self) -> List[Dict[str, Any]]:
        """
        发现所有可用的服务扩展点
        
        Returns:
            发现的服务扩展点信息列表
        """
        try:
            manager = stevedore.ExtensionManager(
                namespace=self.namespace,
                invoke_on_load=False  # 不自动加载，延迟加载
            )
            
            discovered = []
            for ext in manager:
                discovered.append({
                    "name": ext.name,
                    "entry_point": ext.entry_point,
                    "module": ext.module_name,
                    "attrs": ext.attrs
                })
            
            return discovered
        except stevedore.exception.NoMatches:
            return []
        except Exception as e:
            raise ServiceDiscoveryError(
                f"发现服务扩展点失败: {str(e)}",
                {"namespace": self.namespace}
            )
    
    def load_and_register(
        self,
        service_names: Optional[List[str]] = None,
        filter_func: Optional[Callable[[str], bool]] = None
    ) -> Dict[str, Service]:
        """
        加载并注册服务
        
        Args:
            service_names: 要加载的服务名称列表，如果为None则加载所有服务
            filter_func: 服务过滤函数，返回True表示加载该服务
            
        Returns:
            服务名称到服务实例的字典
            
        Raises:
            ServiceDiscoveryError: 服务加载失败
        """
        loaded_services = {}
        
        try:
            manager = stevedore.ExtensionManager(
                namespace=self.namespace,
                invoke_on_load=False
            )
            
            for ext in manager:
                service_name = ext.name
                
                # 检查是否需要加载此服务
                if service_names is not None and service_name not in service_names:
                    continue
                if filter_func is not None and not filter_func(service_name):
                    continue
                
                try:
                    # 加载服务插件
                    plugin = ext.plugin()
                    
                    # 处理不同类型的插件
                    if hasattr(plugin, 'register'):
                        # 插件有register方法，调用它来注册服务
                        plugin.register(self.registry)
                        loaded_services[service_name] = plugin
                    elif isinstance(plugin, Service):
                        # 插件本身就是服务实例，但暂时不支持异步元数据获取
                        # 调用者需要提供元数据或使用register方法
                        raise ServiceDiscoveryError(
                            f"服务插件'{service_name}'是Service实例但不支持直接注册，请提供register方法",
                            {"service_name": service_name}
                        )
                    else:
                        raise ServiceDiscoveryError(
                            f"服务插件'{service_name}'不符合Service协议",
                            {"service_name": service_name}
                        )
                        
                except Exception as e:
                    raise ServiceDiscoveryError(
                        f"加载服务'{service_name}'失败: {str(e)}",
                        {"service_name": service_name}
                    )
            
            return loaded_services
            
        except stevedore.exception.NoMatches:
            return {}
        except Exception as e:
            raise ServiceDiscoveryError(
                f"服务发现过程失败: {str(e)}",
                {"namespace": self.namespace}
            )
    
    def get_registry(self) -> ServiceRegistry:
        """
        获取服务注册表
        
        Returns:
            服务注册表
        """
        return self.registry
    
    def clear_registry(self) -> None:
        """清空服务注册表"""
        self.registry.clear()
    
    def reload_services(
        self,
        service_names: Optional[List[str]] = None
    ) -> Dict[str, Service]:
        """
        重新加载服务
        
        先清空注册表，然后重新发现和加载服务。
        
        Args:
            service_names: 要重新加载的服务名称列表
            
        Returns:
            服务名称到服务实例的字典
        """
        self.clear_registry()
        return self.load_and_register(service_names)
    
    def get_available_services(self) -> List[str]:
        """
        获取可用的服务名称列表
        
        Returns:
            可用服务名称列表
        """
        discovered = self.discover()
        return [item["name"] for item in discovered]