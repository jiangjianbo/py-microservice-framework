"""
依赖注入容器模块

提供依赖注入功能，支持自动解析依赖关系和生命周期管理。
依赖注入容器管理服务实例的创建和生命周期，减少服务之间的耦合。
"""

from typing import Type, TypeVar, Callable, Dict, Any, Set, Optional
from enum import Enum


T = TypeVar("T")


class Scope(Enum):
    """
    依赖作用域
    
    定义依赖实例的生命周期：
    - SINGLETON: 单例模式，整个应用生命周期只创建一次
    - TRANSIENT: 瞬态模式，每次解析都创建新实例
    - SCOPED: 作用域模式，在特定作用域内共享实例
    """
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class DependencyContainer:
    """
    依赖注入容器
    
    提供依赖注入功能，支持自动解析依赖关系和生命周期管理。
    """
    
    def __init__(self):
        """初始化依赖注入容器"""
        self._registrations: Dict[Type, Dict[str, Any]] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Dict[int, Any]] = {}
        self._resolving: Set[Type] = set()  # 用于检测循环依赖
    
    def register(
        self,
        dependency_type: Type[T],
        factory: Optional[Callable[..., T]] = None,
        scope: Scope = Scope.SINGLETON,
        **kwargs
    ) -> None:
        """
        注册依赖
        
        Args:
            dependency_type: 依赖类型
            factory: 工厂函数，如果为None则使用类构造函数
            scope: 依赖作用域
            **kwargs: 额外参数
        """
        if dependency_type in self._registrations:
            raise ValueError(f"依赖'{dependency_type.__name__}'已经注册")
        
        # 如果没有提供工厂函数，使用类构造函数
        if factory is None:
            factory = dependency_type
        
        self._registrations[dependency_type] = {
            "factory": factory,
            "scope": scope,
            "kwargs": kwargs,
            "type": dependency_type  # 保存类型信息
        }
    
    def register_factory(
        self,
        dependency_type: Type[T],
        factory: Callable[..., T],
        scope: Scope = Scope.SINGLETON
    ) -> None:
        """
        注册依赖工厂

        Args:
            dependency_type: 依赖类型
            factory: 工厂函数
            scope: 依赖作用域
        """
        self.register(dependency_type, factory=factory, scope=scope)
    
    def register_instance(
        self,
        dependency_type: Type[T],
        instance: T
    ) -> None:
        """
        注册已有实例（单例）
        
        Args:
            dependency_type: 依赖类型
            instance: 已有实例
        """
        self._singletons[dependency_type] = instance
        self._registrations[dependency_type] = {
            "factory": lambda: instance,
            "scope": Scope.SINGLETON,
            "kwargs": {},
            "instance": True
        }
    
    def resolve(self, dependency_type: Type[T]) -> T:
        """
        解析依赖
        
        Args:
            dependency_type: 依赖类型
            
        Returns:
            依赖实例
            
        Raises:
            ValueError: 如果依赖未注册或检测到循环依赖
        """
        # 检查循环依赖
        if dependency_type in self._resolving:
            cycle = " -> ".join([dep.__name__ if hasattr(dep, '__name__') else str(dep) for dep in self._resolving] + [str(dependency_type)])
            raise ValueError(f"检测到循环依赖: {cycle}")
        
        if dependency_type not in self._registrations:
            raise ValueError(f"依赖'{dependency_type.__name__ if hasattr(dependency_type, '__name__') else str(dependency_type)}'未注册")
        
        registration = self._registrations[dependency_type]
        
        # 根据作用域解析实例
        scope = registration["scope"]
        
        if scope == Scope.SINGLETON:
            return self._resolve_singleton(dependency_type, registration)
        elif scope == Scope.TRANSIENT:
            return self._resolve_transient(dependency_type, registration)
        elif scope == Scope.SCOPED:
            return self._resolve_scoped(dependency_type, registration)
        else:
            raise ValueError(f"未知的作用域: {scope}")
    
    def _resolve_singleton(
        self,
        dependency_type: Type[T],
        registration: Dict[str, Any]
    ) -> T:
        """解析单例依赖"""
        if dependency_type in self._singletons:
            return self._singletons[dependency_type]
        
        instance = self._create_instance(dependency_type, registration)
        self._singletons[dependency_type] = instance
        return instance
    
    def _resolve_transient(
        self,
        dependency_type: Type[T],
        registration: Dict[str, Any]
    ) -> T:
        """解析瞬态依赖"""
        return self._create_instance(dependency_type, registration)
    
    def _resolve_scoped(
        self,
        dependency_type: Type[T],
        registration: Dict[str, Any]
    ) -> T:
        """解析作用域依赖（暂时使用单例实现）"""
        # TODO: 实现真正的作用域管理
        return self._resolve_singleton(dependency_type, registration)
    
    def _resolve_annotation(self, annotation: Any) -> Any:
        """
        解析类型注解

        支持字符串形式的前向引用注解：按已注册类型的 __name__ 匹配。
        无法匹配时原样返回。

        Args:
            annotation: 参数类型注解

        Returns:
            解析后的类型
        """
        if not isinstance(annotation, str):
            return annotation
        for registered in self._registrations:
            if getattr(registered, "__name__", None) == annotation:
                return registered
        return annotation

    def _create_instance(
        self,
        dependency_type: Type[T],
        registration: Dict[str, Any]
    ) -> T:
        """创建实例并注入依赖"""
        self._resolving.add(dependency_type)
        
        try:
            factory = registration["factory"]
            kwargs = registration.get("kwargs", {})
            
            # 如果是实例注册，直接返回
            if registration.get("instance", False):
                return factory()
            
            # 尝试自动注入依赖
            try:
                import inspect
                sig = inspect.signature(factory)
                
                # 检查工厂函数是否接受有类型注解的参数
                has_params = any(
                    param.name != 'self' and param.annotation != inspect.Parameter.empty
                    for param in sig.parameters.values()
                )
                
                if has_params:
                    # 构建注入参数
                    injected_kwargs = {}
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        
                        if param.annotation != inspect.Parameter.empty:
                            # 尝试解析依赖
                            dependency = self.resolve(
                                self._resolve_annotation(param.annotation)
                            )
                            injected_kwargs[param_name] = dependency
                    
                    # 合并参数
                    all_kwargs = {**injected_kwargs, **kwargs}
                    
                    # 创建实例
                    instance = factory(**all_kwargs)
                else:
                    # 工厂函数没有参数，直接调用
                    instance = factory()
                
                return instance
                
            except ValueError:
                # 依赖解析错误（未注册/循环依赖）必须向上传播，
                # 不能被回退逻辑掩盖
                raise
            except Exception:
                # 如果自动注入失败，使用原始参数
                try:
                    instance = factory(**kwargs)
                except TypeError:
                    # 如果还是失败，直接调用无参数版本
                    instance = factory()
                return instance
                
        finally:
            self._resolving.discard(dependency_type)
    
    def unregister(self, dependency_type: Type[T]) -> None:
        """
        注销依赖
        
        Args:
            dependency_type: 依赖类型
            
        Raises:
            ValueError: 如果依赖未注册
        """
        if dependency_type not in self._registrations:
            raise ValueError(f"依赖'{dependency_type.__name__}'未注册")
        
        del self._registrations[dependency_type]
        
        # 清理实例缓存
        if dependency_type in self._singletons:
            del self._singletons[dependency_type]
    
    def clear(self) -> None:
        """清空所有注册的依赖"""
        self._registrations.clear()
        self._singletons.clear()
        self._scoped_instances.clear()
    
    def is_registered(self, dependency_type: Type[T]) -> bool:
        """
        检查依赖是否已注册
        
        Args:
            dependency_type: 依赖类型
            
        Returns:
            如果已注册返回True，否则返回False
        """
        return dependency_type in self._registrations
    
    def get_registered_types(self) -> Set[Type]:
        """
        获取所有已注册的类型
        
        Returns:
            已注册类型集合
        """
        return set(self._registrations.keys())
    
    def get_singleton(self, dependency_type: Type[T]) -> Optional[T]:
        """
        获取单例实例
        
        Args:
            dependency_type: 依赖类型
            
        Returns:
            单例实例，如果不存在返回None
        """
        return self._singletons.get(dependency_type)