"""
gRPC传输工厂模块

提供gRPC客户端和服务器的工厂方法。
"""

from typing import Dict, Any
from serviceframework.transport.grpc.config import GrpcConfig
from serviceframework.transport.grpc.client import GrpcClient
from serviceframework.transport.grpc.server import GrpcServer


class GrpcTransportFactory:
    """
    gRPC传输工厂
    
    提供统一的客户端和服务器创建接口。
    支持配置验证和传输信息查询。
    """
    
    def __init__(self):
        """初始化传输工厂"""
        self._clients: Dict[str, GrpcClient] = {}
        self._servers: Dict[str, GrpcServer] = {}
    
    def create_client(self, config: GrpcConfig) -> GrpcClient:
        """
        创建gRPC客户端
        
        Args:
            config: gRPC配置
            
        Returns:
            gRPC客户端实例
            
        Raises:
            ValueError: 配置无效时抛出异常
        """
        if not config:
            raise ValueError("配置不能为空")
        
        client = GrpcClient(config)
        
        # 缓存客户端
        key = f"{config.host}:{config.port}"
        self._clients[key] = client
        
        return client
    
    def create_server(self, config: GrpcConfig) -> GrpcServer:
        """
        创建gRPC服务器
        
        Args:
            config: gRPC配置
            
        Returns:
            gRPC服务器实例
            
        Raises:
            ValueError: 配置无效时抛出异常
        """
        if not config:
            raise ValueError("配置不能为空")
        
        server = GrpcServer(config)
        
        # 缓存服务器
        key = f"{config.host}:{config.port}"
        self._servers[key] = server
        
        return server
    
    def get_transport_info(self) -> Dict[str, Any]:
        """
        获取传输信息
        
        Returns:
            传输信息字典
        """
        return {
            "type": "grpc",
            "protocol": "http2",
            "version": "1.0.0",
            "features": [
                "ssl_support",
                "async_support",
                "streaming",
                "compression"
            ],
            "clients": len(self._clients),
            "servers": len(self._servers)
        }
    
    def get_client(self, host: str, port: int) -> GrpcClient:
        """
        获取已创建的客户端
        
        Args:
            host: 主机地址
            port: 端口号
            
        Returns:
            gRPC客户端实例
            
        Raises:
            KeyError: 客户端不存在时抛出异常
        """
        key = f"{host}:{port}"
        return self._clients[key]
    
    def get_server(self, host: str, port: int) -> GrpcServer:
        """
        获取已创建的服务器
        
        Args:
            host: 主机地址
            port: 端口号
            
        Returns:
            gRPC服务器实例
            
        Raises:
            KeyError: 服务器不存在时抛出异常
        """
        key = f"{host}:{port}"
        return self._servers[key]
    
    def remove_client(self, host: str, port: int) -> None:
        """
        移除客户端
        
        Args:
            host: 主机地址
            port: 端口号
        """
        key = f"{host}:{port}"
        if key in self._clients:
            del self._clients[key]
    
    def remove_server(self, host: str, port: int) -> None:
        """
        移除服务器
        
        Args:
            host: 主机地址
            port: 端口号
        """
        key = f"{host}:{port}"
        if key in self._servers:
            del self._servers[key]
    
    async def shutdown_all(self) -> None:
        """关闭所有客户端和服务器"""
        # 断开所有客户端
        for client in self._clients.values():
            await client.disconnect()
        
        # 停止所有服务器
        for server in self._servers.values():
            await server.stop()
        
        # 清空缓存
        self._clients.clear()
        self._servers.clear()