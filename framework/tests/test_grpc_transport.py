"""
gRPC传输模块单元测试

测试gRPC客户端和服务器实现，支持远程服务调用。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from serviceframework.transport.grpc import (
    GrpcClient,
    GrpcServer,
    GrpcTransportFactory,
    GrpcConfig
)
from serviceframework.contract.service import ServiceDefinition, ServiceContext
from serviceframework.contract.request import ServiceRequest
from serviceframework.contract.response import ServiceResponse


class TestGrpcConfig:
    
    def test_config_creation(self):
        """测试gRPC配置创建"""
        config = GrpcConfig(
            host="0.0.0.0",
            port=50051,
            max_workers=10,
            timeout=30,
            enable_ssl=False
        )
        
        assert config.host == "0.0.0.0"
        assert config.port == 50051
        assert config.max_workers == 10
        assert config.timeout == 30
        assert config.enable_ssl is False
    
    def test_config_with_ssl(self):
        """测试SSL配置"""
        config = GrpcConfig(
            host="0.0.0.0",
            port=50051,
            enable_ssl=True,
            cert_file="server.crt",
            key_file="server.key"
        )
        
        assert config.enable_ssl is True
        assert config.cert_file == "server.crt"
        assert config.key_file == "server.key"


class TestGrpcClient:
    
    def test_client_creation(self):
        """测试gRPC客户端创建"""
        config = GrpcConfig(host="localhost", port=50051)
        client = GrpcClient(config)
        
        assert client.config == config
        assert client._channel is None
    
    @pytest.mark.asyncio
    async def test_client_connect(self):
        """测试客户端连接"""
        config = GrpcConfig(host="localhost", port=50051)
        client = GrpcClient(config)
        
        # 模拟连接
        with patch('grpc.aio.insecure_channel') as mock_channel:
            mock_channel.return_value = AsyncMock()
            await client.connect()
            
            assert client._channel is not None
    
    @pytest.mark.asyncio
    async def test_client_disconnect(self):
        """测试客户端断开连接"""
        config = GrpcConfig(host="localhost", port=50051)
        client = GrpcClient(config)
        
        # 模拟连接和断开
        with patch('grpc.aio.insecure_channel') as mock_channel:
            mock_channel.return_value = AsyncMock()
            await client.connect()
            await client.disconnect()
            
            assert client._channel is None
    
    @pytest.mark.asyncio
    async def test_client_send_request(self):
        """测试客户端发送请求"""
        config = GrpcConfig(host="localhost", port=50051)
        client = GrpcClient(config)

        context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123"
        )

        request = ServiceRequest(
            service_name="user-service",
            method="get_user",
            kwargs={"user_id": "123"},
            context=context
        )
        
        # 模拟请求发送
        with patch('grpc.aio.insecure_channel') as mock_channel:
            mock_channel.return_value = AsyncMock()
            response = await client.send_request("user-service", request)
            
            assert response is not None
    
    @pytest.mark.asyncio
    async def test_client_send_request_with_timeout(self):
        """测试带超时的请求发送"""
        config = GrpcConfig(host="localhost", port=50051, timeout=10)
        client = GrpcClient(config)

        context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123"
        )

        request = ServiceRequest(
            service_name="user-service",
            method="get_user",
            kwargs={"user_id": "123"},
            context=context
        )
        
        # 模拟带超时的请求
        with patch('grpc.aio.insecure_channel') as mock_channel:
            mock_channel.return_value = AsyncMock()
            response = await client.send_request("user-service", request, timeout=5)
            
            assert response is not None
    
    def test_client_get_status(self):
        """测试获取客户端状态"""
        config = GrpcConfig(host="localhost", port=50051)
        client = GrpcClient(config)
        
        status = client.get_status()
        
        assert status is not None
        assert "connected" in status


class TestGrpcServer:
    
    def test_server_creation(self):
        """测试gRPC服务器创建"""
        config = GrpcConfig(host="0.0.0.0", port=50051)
        server = GrpcServer(config)
        
        assert server.config == config
        assert server._server is None
    
    def test_server_registration(self):
        """测试服务注册"""
        config = GrpcConfig(host="0.0.0.0", port=50051)
        server = GrpcServer(config)
        
        service_definition = ServiceDefinition(
            name="user-service",
            version="1.0.0",
            description="用户服务"
        )
        
        server.register_service(service_definition)
        
        assert len(server.services) > 0
    
    @pytest.mark.asyncio
    async def test_server_start(self):
        """测试服务器启动"""
        config = GrpcConfig(host="0.0.0.0", port=50051)
        server = GrpcServer(config)
        
        # 模拟启动
        with patch('grpc.aio.server') as mock_server:
            mock_server.return_value = AsyncMock()
            await server.start()
            
            assert server._server is not None
    
    @pytest.mark.asyncio
    async def test_server_stop(self):
        """测试服务器停止"""
        config = GrpcConfig(host="0.0.0.0", port=50051)
        server = GrpcServer(config)
        
        # 模拟启动和停止
        with patch('grpc.aio.server') as mock_server:
            mock_server.return_value = AsyncMock()
            await server.start()
            await server.stop()
            
            assert server._server is None
    
    @pytest.mark.asyncio
    async def test_server_handle_request(self):
        """测试服务器处理请求"""
        config = GrpcConfig(host="0.0.0.0", port=50051)
        server = GrpcServer(config)

        service_definition = ServiceDefinition(
            name="user-service",
            version="1.0.0",
            description="用户服务"
        )

        server.register_service(service_definition)

        context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123"
        )

        request = ServiceRequest(
            service_name="user-service",
            method="get_user",
            kwargs={"user_id": "123"},
            context=context
        )
        
        # 模拟请求处理
        response = await server.handle_request(request)
        
        assert response is not None
    
    def test_server_get_status(self):
        """测试获取服务器状态"""
        config = GrpcConfig(host="0.0.0.0", port=50051)
        server = GrpcServer(config)
        
        status = server.get_status()
        
        assert status is not None
        assert "running" in status


class TestGrpcTransportFactory:
    
    def test_factory_creation(self):
        """测试传输工厂创建"""
        factory = GrpcTransportFactory()
        
        assert factory is not None
    
    def test_factory_create_client(self):
        """测试工厂创建客户端"""
        factory = GrpcTransportFactory()
        
        config = GrpcConfig(host="localhost", port=50051)
        client = factory.create_client(config)
        
        assert isinstance(client, GrpcClient)
    
    def test_factory_create_server(self):
        """测试工厂创建服务器"""
        factory = GrpcTransportFactory()
        
        config = GrpcConfig(host="0.0.0.0", port=50051)
        server = factory.create_server(config)
        
        assert isinstance(server, GrpcServer)
    
    def test_factory_get_transport_info(self):
        """测试获取传输信息"""
        factory = GrpcTransportFactory()
        
        info = factory.get_transport_info()
        
        assert info is not None
        assert info["type"] == "grpc"
        assert info["protocol"] == "http2"


class TestGrpcIntegration:
    
    @pytest.mark.asyncio
    async def test_client_server_communication(self):
        """测试客户端服务器通信"""
        # 创建服务器
        server_config = GrpcConfig(host="0.0.0.0", port=50051)
        server = GrpcServer(server_config)
        
        service_definition = ServiceDefinition(
            name="user-service",
            version="1.0.0",
            description="用户服务"
        )
        
        server.register_service(service_definition)
        
        # 创建客户端
        client_config = GrpcConfig(host="localhost", port=50051)
        client = GrpcClient(client_config)
        
        # 模拟通信
        with patch('grpc.aio.insecure_channel') as mock_channel, \
             patch('grpc.aio.server') as mock_server:
            
            mock_channel.return_value = AsyncMock()
            mock_server.return_value = AsyncMock()
            
            # 启动服务器
            await server.start()
            
            # 连接客户端
            await client.connect()

            # 发送请求
            context = ServiceContext(
                service_name="user-service",
                method="get_user",
                request_id="req-123"
            )

            request = ServiceRequest(
                service_name="user-service",
                method="get_user",
                kwargs={"user_id": "123"},
                context=context
            )

            response = await client.send_request("user-service", request)

        # 清理
        await client.disconnect()
        await server.stop()

        assert response is not None