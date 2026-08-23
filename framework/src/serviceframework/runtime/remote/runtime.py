"""
远程服务运行时模块

实现远程服务的启动、停止和发现功能，支持gRPC通信和服务发现。
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from serviceframework.runtime.remote.config import RemoteServiceConfig, ServiceDiscoveryConfig
from serviceframework.contract.service import ServiceDefinition, ServiceContext
from serviceframework.transport.grpc.config import GrpcConfig
from serviceframework.transport.grpc.server import GrpcServer
from serviceframework.transport.grpc.client import GrpcClient
from serviceframework.transport.grpc.factory import GrpcTransportFactory

logger = logging.getLogger(__name__)


class RemoteServiceRuntime:
    """
    远程服务运行时
    
    提供远程服务的启动、停止、发现和通信能力。
    支持gRPC传输和服务发现功能。
    """
    
    def __init__(self, config: RemoteServiceConfig):
        """
        初始化远程服务运行时
        
        Args:
            config: 远程服务配置
        """
        self.config = config
        self._server: Optional[GrpcServer] = None
        self._clients: Dict[str, GrpcClient] = {}
        self._factory = GrpcTransportFactory()
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._discovery_task: Optional[asyncio.Task] = None
        self._registered_services: Dict[str, ServiceDefinition] = {}
    
    async def start(self) -> None:
        """
        启动远程服务运行时
        
        Raises:
            Exception: 启动失败时抛出异常
        """
        if self._running:
            logger.warning("远程服务运行时已经在运行中")
            return
        
        logger.info(f"启动远程服务: {self.config.service_definition.name}")
        
        # 创建gRPC服务器
        self._server = self._factory.create_server(self.config.grpc_config)
        
        # 注册服务
        self._server.register_service(self.config.service_definition)
        self._registered_services[self.config.service_definition.name] = self.config.service_definition
        
        # 启动服务器
        await self._server.start()
        
        # 启动心跳任务
        if self.config.discovery_config.enabled:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # 启动服务发现任务
        if self.config.auto_discovery:
            self._discovery_task = asyncio.create_task(self._discovery_loop())
        
        self._running = True
        logger.info(f"远程服务 {self.config.service_definition.name} 启动成功")
    
    async def stop(self) -> None:
        """停止远程服务运行时"""
        if not self._running:
            logger.warning("远程服务运行时未在运行")
            return
        
        logger.info(f"停止远程服务: {self.config.service_definition.name}")
        
        # 停止心跳任务
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        # 停止服务发现任务
        if self._discovery_task:
            self._discovery_task.cancel()
            self._discovery_task = None
        
        # 断开所有客户端
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()
        
        # 停止服务器
        if self._server:
            await self._server.stop()
            self._server = None
        
        self._running = False
        logger.info(f"远程服务 {self.config.service_definition.name} 已停止")
    
    def is_running(self) -> bool:
        """
        检查运行时是否在运行
        
        Returns:
            如果正在运行返回True，否则返回False
        """
        return self._running
    
    def get_registered_services(self) -> List[str]:
        """
        获取已注册的服务列表
        
        Returns:
            服务名称列表
        """
        return list(self._registered_services.keys())
    
    async def discover_services(self) -> List[ServiceDefinition]:
        """
        发现远程服务
        
        Returns:
            发现的服务定义列表
        """
        if not self.config.discovery_config.enabled:
            logger.warning("服务发现未启用")
            return []
        
        # 这里实现实际的服务发现逻辑
        # 由于没有实际的服务发现后端，返回空列表
        return []
    
    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while self._running:
            try:
                await asyncio.sleep(self.config.discovery_config.heartbeat_interval)
                await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循环错误: {e}")
    
    async def _send_heartbeat(self) -> None:
        """发送心跳"""
        # 这里实现实际的心跳发送逻辑
        logger.debug(f"发送服务心跳: {self.config.service_definition.name}")
    
    async def _discovery_loop(self) -> None:
        """服务发现循环"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒发现一次
                discovered_services = await self.discover_services()
                
                for service in discovered_services:
                    logger.debug(f"发现服务: {service.name}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"服务发现循环错误: {e}")
    
    async def get_client_for_service(self, service_name: str) -> GrpcClient:
        """
        获取指定服务的客户端
        
        Args:
            service_name: 服务名称
            
        Returns:
            gRPC客户端实例
            
        Raises:
            ValueError: 服务未找到时抛出异常
        """
        if service_name not in self._clients:
            # 创建新客户端
            # 这里需要从服务发现中获取服务的地址和端口
            # 由于没有实际的服务发现，使用默认配置
            client_config = GrpcConfig(host="localhost", port=50051)
            client = self._factory.create_client(client_config)
            await client.connect()
            self._clients[service_name] = client
        
        return self._clients[service_name]
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取运行时状态
        
        Returns:
            运行时状态信息
        """
        status = {
            "running": self._running,
            "service_name": self.config.service_definition.name,
            "service_version": self.config.service_definition.version,
            "grpc_port": self.config.grpc_config.port,
            "discovery_enabled": self.config.discovery_config.enabled,
            "auto_discovery": self.config.auto_discovery,
            "registered_services": list(self._registered_services.keys()),
            "connected_clients": len(self._clients)
        }
        
        if self._server:
            status["server_status"] = self._server.get_status()
        
        return status
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()