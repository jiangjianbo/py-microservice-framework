"""
Litestar Web适配器模块单元测试

测试HTTP/API层的适配功能，将HTTP请求转换为服务调用。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from litestar.testing import AsyncTestClient
from serviceframework.web.adapter import LitestarAdapter
from serviceframework.contract.service import Service, ServiceMetadata, ServiceError
from serviceframework.proxy.proxy import ServiceProxy
from serviceframework.transport.base import Transport
from dataclasses import dataclass


class TestLitestarAdapter:
    
    def test_adapter_creation(self):
        """测试Litestar适配器创建"""
        adapter = LitestarAdapter()
        assert adapter.app is not None
    
    def test_adapter_register_service_proxy(self):
        """测试注册服务代理"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        proxy.invoke = AsyncMock(return_value={"id": 123, "name": "Alice"})
        
        adapter.register_service_proxy(proxy)
        
        assert "user-service" in adapter.service_proxies
    
    def test_adapter_register_multiple_proxies(self):
        """测试注册多个服务代理"""
        adapter = LitestarAdapter()
        
        for i in range(3):
            transport = Mock(spec=Transport)
            proxy = ServiceProxy(f"service-{i}", transport)
            proxy.invoke = AsyncMock(return_value={"id": i})
            adapter.register_service_proxy(proxy)
        
        assert len(adapter.service_proxies) == 3
        for i in range(3):
            assert f"service-{i}" in adapter.service_proxies
    
    def test_adapter_get_service_proxy(self):
        """测试获取服务代理"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        adapter.register_service_proxy(proxy)
        
        retrieved = adapter.get_service_proxy("user-service")
        assert retrieved == proxy
    
    def test_adapter_get_nonexistent_proxy(self):
        """测试获取不存在的代理"""
        adapter = LitestarAdapter()
        
        with pytest.raises(ValueError, match="代理'user-service'未注册"):
            adapter.get_service_proxy("user-service")
    
    @pytest.mark.asyncio
    async def test_adapter_invoke_service(self):
        """测试调用服务"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        proxy.invoke = AsyncMock(return_value={"id": 123, "name": "Alice"})
        adapter.register_service_proxy(proxy)
        
        result = await adapter.invoke_service("user-service", "get_user", 123)
        
        assert result["id"] == 123
        proxy.invoke.assert_called_once_with("get_user", 123)
    
    @pytest.mark.asyncio
    async def test_adapter_invoke_service_with_error(self):
        """测试调用服务时发生错误"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        proxy.invoke = AsyncMock(side_effect=ServiceError("用户不存在", code="USER_NOT_FOUND"))
        adapter.register_service_proxy(proxy)
        
        with pytest.raises(ServiceError, match="用户不存在"):
            await adapter.invoke_service("user-service", "get_user", 0)
    
    def test_adapter_create_http_route(self):
        """测试创建HTTP路由"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        proxy.invoke = AsyncMock(return_value={"id": 123, "name": "Alice"})
        adapter.register_service_proxy(proxy)
        
        # 创建路由
        route = adapter.create_http_route("/users/{user_id:int}", "user-service", "get_user")
        
        assert route is not None
        # 路由应该已经添加到应用中
    
    def test_adapter_create_http_route_with_multiple_methods(self):
        """测试创建多个HTTP路由"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        proxy.invoke = AsyncMock(return_value={"id": 123, "name": "Alice"})
        adapter.register_service_proxy(proxy)
        
        # 创建多个路由
        adapter.create_http_route("/users/{user_id:int}", "user-service", "get_user", methods=["GET"])
        adapter.create_http_route("/users", "user-service", "create_user", methods=["POST"])
        
        # 检查路由数量
        routes = [route for route in adapter.app.routes]
        assert len(routes) > 0
    
    @pytest.mark.asyncio
    async def test_adapter_http_request(self):
        """测试HTTP请求处理"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        proxy.invoke = AsyncMock(return_value={"id": 123, "name": "Alice"})
        adapter.register_service_proxy(proxy)
        
        # 创建HTTP路由
        adapter.create_http_route("/users/{user_id:int}", "user-service", "get_user", methods=["GET"])
        
        # 使用测试客户端发送请求
        async with AsyncTestClient(adapter.app) as client:
            response = await client.get("/users/123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == 123
            assert data["data"]["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_adapter_http_request_with_service_error(self):
        """测试HTTP请求时的服务错误处理"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        proxy.invoke = AsyncMock(side_effect=ServiceError("用户不存在", code="USER_NOT_FOUND"))
        adapter.register_service_proxy(proxy)
        
        # 创建HTTP路由
        adapter.create_http_route("/users/{user_id:int}", "user-service", "get_user", methods=["GET"])
        
        # 使用测试客户端发送请求
        async with AsyncTestClient(adapter.app) as client:
            response = await client.get("/users/0")
            
            # 应该返回错误响应
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "USER_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_adapter_http_request_with_exception(self):
        """测试HTTP请求时的异常处理"""
        adapter = LitestarAdapter()
        
        transport = Mock(spec=Transport)
        proxy = ServiceProxy("user-service", transport)
        proxy.invoke = AsyncMock(side_effect=RuntimeError("内部错误"))
        adapter.register_service_proxy(proxy)
        
        # 创建HTTP路由
        adapter.create_http_route("/users/{user_id:int}", "user-service", "get_user", methods=["GET"])
        
        # 使用测试客户端发送请求
        async with AsyncTestClient(adapter.app) as client:
            response = await client.get("/users/999")
            
            # 应该返回错误响应
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
    
    def test_adapter_health_check(self):
        """测试健康检查端点"""
        adapter = LitestarAdapter()
        
        # 健康检查路由应该存在
        routes = [route.path for route in adapter.app.routes]
        assert "/health" in routes or any("health" in route for route in routes)