"""
远程服务运行时模块

提供远程服务的启动、停止和发现功能，支持gRPC通信和服务发现。
"""

from serviceframework.runtime.remote.config import ServiceDiscoveryConfig, RemoteServiceConfig
from serviceframework.runtime.remote.runtime import RemoteServiceRuntime

__all__ = [
    "ServiceDiscoveryConfig",
    "RemoteServiceConfig",
    "RemoteServiceRuntime"
]