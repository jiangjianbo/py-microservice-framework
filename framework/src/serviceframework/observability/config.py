"""
OpenTelemetry配置模块

定义追踪配置和Span类型枚举，支持灵活的可观测性配置。
"""

from dataclasses import dataclass
from enum import Enum


class SpanKind(Enum):
    """
    Span类型枚举
    
    定义不同类型的Span，用于区分调用链中不同的环节。
    """
    SERVER = "server"  # 服务端Span
    CLIENT = "client"  # 客户端Span
    INTERNAL = "internal"  # 内部Span
    PRODUCER = "producer"  # 生产者Span
    CONSUMER = "consumer"  # 消费者Span


@dataclass
class TraceConfig:
    """
    追踪配置类
    
    配置OpenTelemetry追踪功能，包括服务名称、追踪后端、采样率等。
    """
    service_name: str  # 服务名称
    endpoint: str  # 追踪后端端点（如Jaeger、Zipkin）
    sample_rate: float = 1.0  # 采样率（0.0-1.0）
    enabled: bool = True  # 是否启用追踪
    timeout: int = 30  # 追踪超时时间（秒）
    
    def __post_init__(self):
        """初始化后验证"""
        if not 0.0 <= self.sample_rate <= 1.0:
            raise ValueError("采样率必须在0.0到1.0之间")
        
        if not self.service_name:
            raise ValueError("服务名称不能为空")
        
        if not self.endpoint:
            raise ValueError("追踪端点不能为空")