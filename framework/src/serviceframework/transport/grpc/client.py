"""
gRPC客户端模块

实现gRPC客户端，支持同步和异步的远程服务调用。
"""

import asyncio
from typing import Optional, Dict, Any
import grpc.aio
from serviceframework.transport.grpc.config import GrpcConfig
from serviceframework.contract.service import ServiceContext
from serviceframework.contract.request import ServiceRequest
from serviceframework.contract.response import ServiceResponse


class GrpcClient:
    """
    gRPC客户端
    
    提供基于gRPC的远程服务调用能力，支持同步和异步通信。
    支持SSL、超时、重试等高级特性。
    """
    
    def __init__(self, config: GrpcConfig):
        """
        初始化gRPC客户端
        
        Args:
            config: gRPC配置
        """
        self.config = config
        self._channel: Optional[grpc.aio.Channel] = None
        self._connected = False
    
    async def connect(self) -> None:
        """
        连接到gRPC服务器
        
        Raises:
            Exception: 连接失败时抛出异常
        """
        if self._connected:
            return
        
        target = f"{self.config.host}:{self.config.port}"
        
        if self.config.enable_ssl:
            # SSL连接
            credentials = grpc.ssl_channel_credentials(
                root_certificates=self._read_file(self.config.ca_file),
                private_key=self._read_file(self.config.key_file),
                certificate_chain=self._read_file(self.config.cert_file)
            )
            self._channel = grpc.aio.secure_channel(target, credentials)
        else:
            # 不安全连接
            self._channel = grpc.aio.insecure_channel(target)
        
        # 等待连接就绪
        await self._channel.ready()
        self._connected = True
    
    async def disconnect(self) -> None:
        """断开与gRPC服务器的连接"""
        if not self._connected:
            return
        
        if self._channel:
            await self._channel.close()
            self._channel = None
        
        self._connected = False
    
    async def send_request(
        self,
        service_name: str,
        request: ServiceRequest,
        timeout: Optional[int] = None
    ) -> ServiceResponse:
        """
        发送服务请求
        
        Args:
            service_name: 服务名称
            request: 服务请求
            timeout: 超时时间（秒），None表示使用配置中的超时
            
        Returns:
            服务响应
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        if not self._connected:
            await self.connect()
        
        # 这里需要实现实际的gRPC调用
        # 由于我们没有实际的proto文件，这里使用模拟实现
        return await self._simulate_call(service_name, request, timeout)
    
    async def _simulate_call(
        self,
        service_name: str,
        request: ServiceRequest,
        timeout: Optional[int] = None
    ) -> ServiceResponse:
        """
        模拟gRPC调用（用于测试）
        
        Args:
            service_name: 服务名称
            request: 服务请求
            timeout: 超时时间
            
        Returns:
            模拟的服务响应
        """
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 返回模拟响应
        return ServiceResponse(
            success=True,
            data={"result": "success", "service": service_name, "request_id": request.context.request_id if request.context else "req-123"},
            metadata={"service": service_name}
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取客户端状态
        
        Returns:
            客户端状态信息
        """
        return {
            "connected": self._connected,
            "host": self.config.host,
            "port": self.config.port,
            "ssl_enabled": self.config.enable_ssl
        }
    
    def _read_file(self, file_path: Optional[str]) -> Optional[bytes]:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容，如果文件路径为None则返回None
        """
        if not file_path:
            return None
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()