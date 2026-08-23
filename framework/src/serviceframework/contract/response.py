"""
服务响应模块

定义服务调用的响应契约，包含返回值、错误信息等。
响应对象封装了服务调用的结果，支持成功和失败两种状态。
"""

from typing import Any, Optional, Dict, TypeVar, Generic
from dataclasses import dataclass
from serviceframework.contract.service import ServiceError

T = TypeVar("T")


@dataclass
class ServiceResponse(Generic[T]):
    """
    服务响应
    
    封装服务调用的结果，可以是成功或失败状态。
    使用泛型支持不同类型的返回值。
    """
    
    success: bool  # 是否成功
    data: Optional[T] = None  # 返回数据，成功时有值
    error: Optional[ServiceError] = None  # 错误信息，失败时有值
    metadata: Dict[str, Any] = None  # 响应元数据
    
    def __post_init__(self):
        """初始化后验证"""
        if self.metadata is None:
            self.metadata = {}
        
        # 验证状态的合理性
        if self.success:
            if self.error is not None:
                raise ValueError("成功的响应不能包含错误信息")
        else:
            if self.error is None:
                raise ValueError("失败的响应必须包含错误信息")
    
    @classmethod
    def success_response(cls, data: T, metadata: Optional[Dict[str, Any]] = None) -> "ServiceResponse[T]":
        """
        创建成功的响应
        
        Args:
            data: 返回数据
            metadata: 响应元数据
            
        Returns:
            成功的响应对象
        """
        return cls(success=True, data=data, metadata=metadata or {})
    
    @classmethod
    def error_response(cls, error: ServiceError, metadata: Optional[Dict[str, Any]] = None) -> "ServiceResponse[T]":
        """
        创建失败的响应
        
        Args:
            error: 错误信息
            metadata: 响应元数据
            
        Returns:
            失败的响应对象
        """
        return cls(success=False, error=error, metadata=metadata or {})
    
    def get_data(self) -> T:
        """
        获取返回数据，如果失败则抛出异常
        
        Returns:
            返回数据
            
        Raises:
            ServiceError: 如果响应失败
        """
        if not self.success:
            raise self.error
        return self.data
    
    def get_data_or_default(self, default: T) -> T:
        """
        获取返回数据，如果失败则返回默认值
        
        Args:
            default: 默认值
            
        Returns:
            返回数据或默认值
        """
        return self.data if self.success else default
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将响应转换为字典格式，便于序列化
        
        Returns:
            包含响应信息的字典
        """
        result = {
            "success": self.success,
            "metadata": self.metadata
        }
        
        if self.success:
            result["data"] = self.data
            result["error"] = None
        else:
            result["data"] = None
            result["error"] = self.error.to_dict() if self.error else None
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceResponse[T]":
        """
        从字典创建响应对象
        
        Args:
            data: 包含响应信息的字典
            
        Returns:
            响应对象
        """
        if data["success"]:
            return cls.success_response(
                data=data.get("data"),
                metadata=data.get("metadata", {})
            )
        else:
            error_data = data.get("error")
            error = None
            if error_data:
                error = ServiceError(
                    message=error_data["message"],
                    code=error_data["code"],
                    details=error_data.get("details", {})
                )
            return cls.error_response(
                error=error,
                metadata=data.get("metadata", {})
            )