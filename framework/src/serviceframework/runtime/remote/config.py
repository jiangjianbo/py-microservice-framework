"""
远程服务配置模块

定义远程服务的配置，包括gRPC配置和服务发现配置。
"""

from dataclasses import dataclass
from serviceframework.transport.grpc.config import GrpcConfig
from serviceframework.contract.service import ServiceDefinition


@dataclass
class ServiceDiscoveryConfig:
    """
    服务发现配置类
    
    配置服务发现功能，支持多种发现后端。
    """
    enabled: bool = True  # 是否启用服务发现
    discovery_type: str = "consul"  # 发现类型（consul、etcd、nacos等）
    discovery_endpoint: str = "http://localhost:8500"  # 发现后端端点
    heartbeat_interval: int = 30  # 心跳间隔（秒）
    service_ttl: int = 60  # 服务TTL（秒）
    tags: dict = None  # 服务标签
    
    def __post_init__(self):
        """初始化后验证"""
        if self.discovery_type not in ["consul", "etcd", "nacos", "none"]:
            raise ValueError(f"不支持的发现类型: {self.discovery_type}")
        
        if self.heartbeat_interval <= 0:
            raise ValueError("心跳间隔必须大于0")
        
        if self.service_ttl <= 0:
            raise ValueError("服务TTL必须大于0")
        
        if self.tags is None:
            self.tags = {}


@dataclass
class RemoteServiceConfig:
    """
    远程服务配置类
    
    配置远程服务运行时，包括服务定义、传输配置和发现配置。
    """
    service_definition: ServiceDefinition  # 服务定义
    grpc_config: GrpcConfig  # gRPC配置
    discovery_config: ServiceDiscoveryConfig  # 服务发现配置
    auto_discovery: bool = False  # 是否自动发现远程服务
    enable_health_check: bool = True  # 是否启用健康检查
    health_check_interval: int = 60  # 健康检查间隔（秒）
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.service_definition:
            raise ValueError("服务定义不能为空")
        
        if not self.grpc_config:
            raise ValueError("gRPC配置不能为空")
        
        if not self.discovery_config:
            raise ValueError("服务发现配置不能为空")
        
        if self.health_check_interval <= 0:
            raise ValueError("健康检查间隔必须大于0")