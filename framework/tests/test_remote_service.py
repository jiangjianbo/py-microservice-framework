"""
远程服务运行时模块单元测试

测试远程服务的启动、停止和发现功能。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from serviceframework.runtime.remote import (
    RemoteServiceRuntime,
    RemoteServiceConfig,
    ServiceDiscoveryConfig
)
from serviceframework.contract.service import ServiceDefinition, ServiceContext
from serviceframework.transport.grpc import GrpcConfig, GrpcServer, GrpcClient
from serviceframework.registry.registry import ServiceRegistry


class TestServiceDiscoveryConfig:
    
    def test_config_creation(self):
        """测试服务发现配置创建"""
        config = ServiceDiscoveryConfig(
            enabled=True,
            discovery_type="consul",
            discovery_endpoint="http://consul:8500",
            heartbeat_interval=30,
            service_ttl=60
        )
        
        assert config.enabled is True
        assert config.discovery_type == "consul"
        assert config.discovery_endpoint == "http://consul:8500"
        assert config.heartbeat_interval == 30
        assert config.service_ttl == 60


class TestRemoteServiceConfig:
    
    def test_config_creation(self):
        """测试远程服务配置创建"""
        grpc_config = GrpcConfig(host="0.0.0.0", port=50051)
        discovery_config = ServiceDiscoveryConfig(enabled=False)
        
        config = RemoteServiceConfig(
            service_definition=ServiceDefinition(
                name="user-service",
                version="1.0.0",
                description="用户服务"
            ),
            grpc_config=grpc_config,
            discovery_config=discovery_config,
            auto_discovery=False
        )
        
        assert config.service_definition.name == "user-service"
        assert config.grpc_config.host == "0.0.0.0"
        assert config.discovery_config.enabled is False
        assert config.auto_discovery is False


class TestRemoteServiceRuntime:
    
    def test_runtime_creation(self):
        """测试远程服务运行时创建"""
        grpc_config = GrpcConfig(host="0.0.0.0", port=50051)
        discovery_config = ServiceDiscoveryConfig(enabled=False)
        
        config = RemoteServiceConfig(
            service_definition=ServiceDefinition(
                name="user-service",
                version="1.0.0",
                description="用户服务"
            ),
            grpc_config=grpc_config,
            discovery_config=discovery_config
        )
        
        runtime = RemoteServiceRuntime(config)
        
        assert runtime.config == config
        assert runtime.is_running() is False
    
    @pytest.mark.asyncio
    async def test_runtime_start(self):
        """测试启动远程服务"""
        grpc_config = GrpcConfig(host="0.0.0.0", port=50051)
        discovery_config = ServiceDiscoveryConfig(enabled=False)
        
        config = RemoteServiceConfig(
            service_definition=ServiceDefinition(
                name="user-service",
                version="1.0.0",
                description="用户服务"
            ),
            grpc_config=grpc_config,
            discovery_config=discovery_config
        )
        
        runtime = RemoteServiceRuntime(config)
        
        # 模拟启动
        with patch('grpc.aio.server') as mock_server:
            mock_server.return_value = AsyncMock()
            await runtime.start()
            
            assert runtime.is_running() is True
    
    @pytest.mark.asyncio
    async def test_runtime_stop(self):
        """测试停止远程服务"""
        grpc_config = GrpcConfig(host="0.0.0.0", port=50051)
        discovery_config = ServiceDiscoveryConfig(enabled=False)
        
        config = RemoteServiceConfig(
            service_definition=ServiceDefinition(
                name="user-service",
                version="1.0.0",
                description="用户服务"
            ),
            grpc_config=grpc_config,
            discovery_config=discovery_config
        )
        
        runtime = RemoteServiceRuntime(config)
        
        # 模拟启动和停止
        with patch('grpc.aio.server') as mock_server:
            mock_server.return_value = AsyncMock()
            await runtime.start()
            assert runtime.is_running() is True
            
            await runtime.stop()
            assert runtime.is_running() is False
    
    @pytest.mark.asyncio
    async def test_runtime_service_registration(self):
        """测试服务注册"""
        grpc_config = GrpcConfig(host="0.0.0.0", port=50051)
        discovery_config = ServiceDiscoveryConfig(enabled=False)
        
        config = RemoteServiceConfig(
            service_definition=ServiceDefinition(
                name="user-service",
                version="1.0.0",
                description="用户服务"
            ),
            grpc_config=grpc_config,
            discovery_config=discovery_config
        )
        
        runtime = RemoteServiceRuntime(config)
        
        with patch('grpc.aio.server') as mock_server:
            mock_server.return_value = AsyncMock()
            await runtime.start()
            
            # 检查服务是否注册
            assert "user-service" in runtime.get_registered_services()
            
            await runtime.stop()
    
    def test_runtime_get_status(self):
        """测试获取运行时状态"""
        grpc_config = GrpcConfig(host="0.0.0.0", port=50051)
        discovery_config = ServiceDiscoveryConfig(enabled=False)
        
        config = RemoteServiceConfig(
            service_definition=ServiceDefinition(
                name="user-service",
                version="1.0.0",
                description="用户服务"
            ),
            grpc_config=grpc_config,
            discovery_config=discovery_config
        )
        
        runtime = RemoteServiceRuntime(config)
        
        status = runtime.get_status()
        
        assert status is not None
        assert "running" in status
        assert "service_name" in status
        assert "service_version" in status
    
    @pytest.mark.asyncio
    async def test_runtime_auto_discovery(self):
        """测试自动发现功能"""
        grpc_config = GrpcConfig(host="0.0.0.0", port=50051)
        discovery_config = ServiceDiscoveryConfig(
            enabled=True,
            discovery_type="consul",
            discovery_endpoint="http://consul:8500"
        )
        
        config = RemoteServiceConfig(
            service_definition=ServiceDefinition(
                name="user-service",
                version="1.0.0",
                description="用户服务"
            ),
            grpc_config=grpc_config,
            discovery_config=discovery_config,
            auto_discovery=True
        )
        
        runtime = RemoteServiceRuntime(config)
        
        # 模拟启动（包括自动发现）
        with patch('grpc.aio.server') as mock_server:
            mock_server.return_value = AsyncMock()
            await runtime.start()
            
            assert runtime.is_running() is True
            
            # 模拟发现远程服务
            discovered_services = await runtime.discover_services()
            
            assert discovered_services is not None
            
            await runtime.stop()


class TestRemoteServiceIntegration:
    
    @pytest.mark.asyncio
    async def test_remote_service_communication(self):
        """测试远程服务通信"""
        # 创建服务端
        grpc_config = GrpcConfig(host="0.0.0.0", port=50051)
        discovery_config = ServiceDiscoveryConfig(enabled=False)
        
        server_config = RemoteServiceConfig(
            service_definition=ServiceDefinition(
                name="user-service",
                version="1.0.0",
                description="用户服务"
            ),
            grpc_config=grpc_config,
            discovery_config=discovery_config
        )
        
        server_runtime = RemoteServiceRuntime(server_config)
        
        # 模拟服务端启动
        with patch('grpc.aio.server') as mock_server:
            mock_server.return_value = AsyncMock()
            await server_runtime.start()
            
            # 验证服务端状态
            assert server_runtime.is_running() is True
            
            # 创建客户端
            client_config = GrpcConfig(host="localhost", port=50051)
            client = GrpcClient(client_config)
            
            # 模拟客户端连接
            with patch('grpc.aio.insecure_channel') as mock_channel:
                mock_channel.return_value = AsyncMock()
                await client.connect()
                
                # 验证客户端状态
                assert client.get_status()["connected"] is True
                
                # 清理
                await client.disconnect()
                await server_runtime.stop()