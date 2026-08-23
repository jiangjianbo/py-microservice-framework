"""
服务契约模块

定义逻辑微服务的核心抽象，包括服务协议、上下文、元数据和错误类型。
这些契约不依赖于具体的传输方式（HTTP/gRPC），实现了业务逻辑与部署方式的解耦。
"""

from typing import Protocol, Dict, Any, Optional, runtime_checkable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class ServiceDefinition:
    """
    服务定义类
    
    定义服务的元数据信息，包括名称、版本、描述等。
    用于服务注册和发现。
    """
    name: str  # 服务名称
    version: str  # 服务版本
    description: str  # 服务描述
    tags: Dict[str, str] = field(default_factory=dict)  # 服务标签


class ServiceError(Exception):
    """
    服务错误基类
    
    用于统一处理服务调用过程中的异常，支持错误码和详细信息。
    业务服务应该抛出此类异常而不是直接抛出普通Exception。
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化服务错误
        
        Args:
            message: 错误消息
            code: 错误码，用于标识错误类型
            details: 错误详细信息，可以包含相关的业务数据
        """
        super().__init__(message)
        self.message = message
        self.code = code or "SERVICE_ERROR"
        self.details = details or {}
    
    def __str__(self) -> str:
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将错误转换为字典格式，便于序列化和传输
        
        Returns:
            包含错误信息的字典
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


@dataclass
class ServiceMetadata:
    """
    服务元数据
    
    包含服务的基本信息和依赖关系，用于服务注册和发现。
    每个逻辑微服务都需要提供自己的元数据。
    """
    
    name: str  # 服务名称，唯一标识
    version: str  # 服务版本号，遵循语义化版本规范
    description: str = ""  # 服务描述
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他服务列表
    tags: Dict[str, str] = field(default_factory=dict)  # 服务标签，用于分类和筛选
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.name:
            raise ValueError("服务名称不能为空")
        if not self.version:
            raise ValueError("服务版本号不能为空")


@dataclass
class ServiceContext:
    """
    服务调用上下文
    
    包含单次服务调用的所有上下文信息，如请求ID、追踪信息、用户信息等。
    上下文会在服务调用链中传递，实现横切关注点的数据共享。
    """
    
    service_name: str  # 目标服务名称
    method: str  # 调用的方法名
    request_id: str = ""  # 请求唯一标识，用于追踪
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外的元数据
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        添加元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        获取元数据
        
        Args:
            key: 元数据键
            default: 默认值，当键不存在时返回
            
        Returns:
            元数据值或默认值
        """
        return self.metadata.get(key, default)
    
    def copy(self) -> "ServiceContext":
        """
        复制上下文，用于创建子上下文
        
        Returns:
            新的上下文副本
        """
        return ServiceContext(
            service_name=self.service_name,
            method=self.method,
            request_id=self.request_id,
            metadata=self.metadata.copy()
        )


@runtime_checkable
class Service(Protocol):
    """
    服务协议
    
    定义逻辑微服务必须实现的接口，所有业务服务都应该遵循此协议。
    使用Protocol而不是ABC，因为Protocol提供更好的类型检查和结构化子类型支持。
    """
    
    async def get_metadata(self) -> ServiceMetadata:
        """
        获取服务元数据
        
        Returns:
            服务的元数据信息
        """
        ...
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否健康，True表示健康，False表示不健康
        """
        ...
    
    async def initialize(self) -> None:
        """
        初始化服务
        
        在服务启动时调用，用于执行初始化逻辑，如建立连接、加载配置等。
        """
        ...
    
    async def shutdown(self) -> None:
        """
        关闭服务
        
        在服务停止时调用，用于执行清理逻辑，如释放资源、关闭连接等。
        """
        ...