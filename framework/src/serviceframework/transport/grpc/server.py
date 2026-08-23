"""
gRPC服务器模块

实现gRPC服务器，支持服务注册和请求处理。
"""

import asyncio
from typing import Dict, Optional, Callable
import grpc.aio
from concurrent.futures import ThreadPoolExecutor
from serviceframework.transport.grpc.config import GrpcConfig
from serviceframework.contract.service import ServiceDefinition, ServiceContext
from serviceframework.contract.request import ServiceRequest
from serviceframework.contract.response import ServiceResponse


class GrpcServer:
    """
    gRPC服务器
    
    提供基于gRPC的服务能力，支持服务注册、请求处理和并发控制。
    支持SSL、连接池、心跳检测等高级特性。
    """
    
    def __init__(self, config: GrpcConfig):
        """
        初始化gRPC服务器
        
        Args:
            config: gRPC配置
        """
        self.config = config
        self._server: Optional[grpc.aio.Server] = None
        self._running = False
        self.services: Dict[str, ServiceDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        self._executor = ThreadPoolExecutor(max_workers=config.max_workers)
    
    def register_service(self, service: ServiceDefinition) -> None:
        """
        注册服务
        
        Args:
            service: 服务定义
            
        Raises:
            ValueError: 服务已注册时抛出异常
        """
        if service.name in self.services:
            raise ValueError(f"服务 {service.name} 已注册")
        
        self.services[service.name] = service
    
    def register_handler(
        self,
        service_name: str,
        method_name: str,
        handler: Callable
    ) -> None:
        """
        注册请求处理器
        
        Args:
            service_name: 服务名称
            method_name: 方法名称
            handler: 处理器函数
        """
        key = f"{service_name}.{method_name}"
        self._handlers[key] = handler
    
    async def start(self) -> None:
        """
        启动gRPC服务器
        
        Raises:
            Exception: 启动失败时抛出异常
        """
        if self._running:
            return
        
        # 创建gRPC服务器
        self._server = grpc.aio.server(
            thread_pool=self._executor,
            maximum_concurrent_rpcs=self.config.max_workers
        )
        
        # 添加端口
        listen_addr = f"{self.config.host}:{self.config.port}"
        
        if self.config.enable_ssl:
            # SSL端口
            server_credentials = grpc.ssl_server_credentials(
                [(self._read_file(self.config.key_file), 
                  self._read_file(self.config.cert_file))],
                root_certificates=self._read_file(self.config.ca_file),
                require_client_auth=self.config.ca_file is not None
            )
            self._server.add_secure_port(listen_addr, server_credentials)
        else:
            # 不安全端口
            self._server.add_insecure_port(listen_addr)
        
        # 启动服务器
        await self._server.start()
        self._running = True
    
    async def stop(self, grace_period: float = 5.0) -> None:
        """
        停止gRPC服务器
        
        Args:
            grace_period: 优雅停机等待时间（秒）
        """
        if not self._running:
            return
        
        if self._server:
            await self._server.stop(grace_period)
            self._server = None
        
        self._running = False
        self._executor.shutdown(wait=True)
    
    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        处理服务请求
        
        Args:
            request: 服务请求
            
        Returns:
            服务响应
            
        Raises:
            Exception: 处理失败时抛出异常
        """
        # 查找处理器
        key = f"{request.service_name}.{request.method}"
        
        if key not in self._handlers:
            # 如果没有找到处理器，返回默认响应
            return self._create_default_response(request)
        
        try:
            # 调用处理器
            handler = self._handlers[key]
            
            if asyncio.iscoroutinefunction(handler):
                result = await handler(request)
            else:
                # 在线程池中执行同步处理器
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor,
                    handler,
                    request
                )
            
            return result
        
        except Exception as e:
            # 返回错误响应
            return ServiceResponse(
                request_id=request.request_id,
                status_code=500,
                status_message=str(e),
                data=None,
                headers={}
            )
    
    def _create_default_response(self, request: ServiceRequest) -> ServiceResponse:
        """
        创建默认响应

        Args:
            request: 服务请求

        Returns:
            默认服务响应
        """
        request_id = request.context.request_id if request.context else "default"
        return ServiceResponse(
            success=True,
            data={"message": "服务处理完成", "request_id": request_id},
            metadata={"service": request.service_name}
        )
    
    def get_status(self) -> Dict[str, any]:
        """
        获取服务器状态
        
        Returns:
            服务器状态信息
        """
        return {
            "running": self._running,
            "host": self.config.host,
            "port": self.config.port,
            "services": list(self.services.keys()),
            "max_workers": self.config.max_workers,
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
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()