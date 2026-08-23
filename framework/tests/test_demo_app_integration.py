"""
微服务框架完整示例应用测试

验证框架的所有核心功能是否正常工作
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from demo_app import (
    UserRepository, OrderRepository, UserService, OrderService,
    LoggingInterceptor, MetricsInterceptor, InterceptorPipeline,
    ServiceDefinition, ServiceRegistry, DIContainer,
    TelemetryManager, TraceConfig, ServiceContext,
    LocalTransportFactory, ServiceProxyFactory,
    ServiceRequest
)


class TestBasicService:
    """基础服务测试"""

    @pytest.mark.asyncio
    async def test_user_repository_find(self):
        """测试用户存储查找"""
        repository = UserRepository()
        user = await repository.find(1)

        assert user is not None
        assert user["id"] == 1
        assert user["name"] == "User1"
        assert "email" in user

    @pytest.mark.asyncio
    async def test_user_repository_find_all(self):
        """测试用户存储查找所有"""
        repository = UserRepository()
        users = await repository.find_all()

        assert len(users) == 2
        assert users[0]["id"] == 1
        assert users[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_order_repository_find(self):
        """测试订单存储查找"""
        repository = OrderRepository()
        order = await repository.find(1)

        assert order is not None
        assert order["id"] == 1
        assert order["user_id"] == 1
        assert order["product"] == "Product A"

    @pytest.mark.asyncio
    async def test_order_repository_find_by_user(self):
        """测试订单存储根据用户查找"""
        repository = OrderRepository()
        orders = await repository.find_by_user(1)

        assert len(orders) == 2
        assert all(order["user_id"] == 1 for order in orders)

    @pytest.mark.asyncio
    async def test_user_service_get_user(self):
        """测试用户服务获取用户"""
        repository = UserRepository()
        service = UserService(repository)

        user = await service.get_user(1)

        assert user["id"] == 1
        assert user["name"] == "User1"

    @pytest.mark.asyncio
    async def test_user_service_get_all_users(self):
        """测试用户服务获取所有用户"""
        repository = UserRepository()
        service = UserService(repository)

        users = await service.get_all_users()

        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_order_service_get_order(self):
        """测试订单服务获取订单"""
        user_repository = UserRepository()
        order_repository = OrderRepository()
        user_service = UserService(user_repository)
        order_service = OrderService(order_repository, user_service)

        order = await order_service.get_order(1)

        assert order["id"] == 1
        assert "user" in order
        assert order["user"]["id"] == 1

    @pytest.mark.asyncio
    async def test_order_service_get_user_orders(self):
        """测试订单服务获取用户订单"""
        user_repository = UserRepository()
        order_repository = OrderRepository()
        user_service = UserService(user_repository)
        order_service = OrderService(order_repository, user_service)

        user_orders = await order_service.get_user_orders(1)

        assert len(user_orders) == 2
        assert all("user" in order for order in user_orders)


class TestServiceRegistry:
    """服务注册测试"""

    def test_register_service(self):
        """测试服务注册"""
        registry = ServiceRegistry()
        service_def = ServiceDefinition(
            name="test-service",
            version="1.0.0",
            description="测试服务"
        )

        registry.register(service_def)

        assert "test-service" in registry.list_services()

    def test_list_services(self):
        """测试列出服务"""
        registry = ServiceRegistry()

        user_service = ServiceDefinition("user-service", "1.0.0", "用户服务")
        order_service = ServiceDefinition("order-service", "1.0.0", "订单服务")

        registry.register(user_service)
        registry.register(order_service)

        services = registry.list_services()
        assert len(services) == 2
        assert "user-service" in services
        assert "order-service" in services


class TestDependencyInjection:
    """依赖注入测试"""

    def test_register_instance(self):
        """测试注册实例"""
        container = DIContainer()
        user_repository = UserRepository()

        container.register_instance(UserRepository, user_repository)

        resolved = container.resolve(UserRepository)
        assert resolved is user_repository

    def test_register_factory(self):
        """测试注册工厂"""
        container = DIContainer()
        user_repository = UserRepository()

        container.register_factory(UserService, lambda: UserService(user_repository))

        resolved = container.resolve(UserService)
        assert isinstance(resolved, UserService)
        assert resolved.repository is user_repository

    def test_nested_dependencies(self):
        """测试嵌套依赖"""
        container = DIContainer()

        user_repository = UserRepository()
        order_repository = OrderRepository()

        container.register_instance(UserRepository, user_repository)
        container.register_instance(OrderRepository, order_repository)

        def create_user_service():
            return UserService(user_repository)

        def create_order_service():
            return OrderService(order_repository, UserService(user_repository))

        container.register_factory(UserService, create_user_service)
        container.register_factory(OrderService, create_order_service)

        order_service = container.resolve(OrderService)
        assert order_service.user_service.repository is user_repository


class TestInterceptors:
    """拦截器测试"""

    @pytest.mark.asyncio
    async def test_logging_interceptor(self):
        """测试日志拦截器"""
        interceptor = LoggingInterceptor()
        user_repository = UserRepository()
        user_service = UserService(user_repository)

        context = ServiceContext("user-service", "get_user", "req-1")
        request = ServiceRequest("user-service", "get_user", args=(1,), context=context)

        # 模拟拦截器上下文
        from serviceframework.interceptor.base import InterceptorContext

        interceptor_context = InterceptorContext(
            service_name="user-service",
            method="get_user",
            request=request,
            service=user_service,
            target_func=user_service.get_user,
            args=(1,),
            kwargs={}
        )

        result = await interceptor.intercept(interceptor_context)
        assert result is not None
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_metrics_interceptor(self):
        """测试指标拦截器"""
        interceptor = MetricsInterceptor()
        user_repository = UserRepository()
        user_service = UserService(user_service)

        context = ServiceContext("user-service", "get_user", "req-1")
        request = ServiceRequest("user-service", "get_user", args=(1,), context=context)

        from serviceframework.interceptor.base import InterceptorContext

        interceptor_context = InterceptorContext(
            service_name="user-service",
            method="get_user",
            request=request,
            service=user_service,
            target_func=user_service.get_user,
            args=(1,),
            kwargs={}
        )

        result = await interceptor.intercept(interceptor_context)

        assert interceptor.call_count == 1
        assert interceptor.error_count == 0
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_interceptor_pipeline(self):
        """测试拦截器管道"""
        pipeline = InterceptorPipeline()

        logging_interceptor = LoggingInterceptor()
        metrics_interceptor = MetricsInterceptor()

        pipeline.add_interceptor(logging_interceptor)
        pipeline.add_interceptor(metrics_interceptor)

        user_repository = UserRepository()
        user_service = UserService(user_repository)

        context = ServiceContext("user-service", "get_user", "req-1")
        request = ServiceRequest("user-service", "get_user", args=(1,), context=context)

        from serviceframework.interceptor.base import InterceptorContext

        interceptor_context = InterceptorContext(
            service_name="user-service",
            method="get_user",
            request=request,
            service=user_service,
            target_func=user_service.get_user,
            args=(1,),
            kwargs={}
        )

        result = await pipeline.execute(interceptor_context)

        assert result["id"] == 1
        assert metrics_interceptor.call_count == 1


class TestObservability:
    """可观测性测试"""

    def test_telemetry_manager_creation(self):
        """测试追踪管理器创建"""
        config = TraceConfig(
            service_name="demo-service",
            endpoint="http://localhost:14268/api/v2/spans",
            enabled=True
        )

        manager = TelemetryManager(config)

        assert manager.is_enabled() is True
        assert manager.config.service_name == "demo-service"

    def test_create_span(self):
        """测试创建Span"""
        config = TraceConfig(service_name="demo-service", endpoint="http://localhost:14268/api/v2/spans")
        manager = TelemetryManager(config)

        service_context = ServiceContext("user-service", "get_user", "req-1")
        span = manager.create_span("get_user", service_context)

        assert span is not None
        assert span.name == "get_user"

    def test_record_metrics(self):
        """测试记录指标"""
        config = TraceConfig(service_name="demo-service", endpoint="http://localhost:14268/api/v2/spans")
        manager = TelemetryManager(config)

        manager.record_counter("api_calls", 1, {"endpoint": "/users/1"})
        manager.record_histogram("response_time", 45.6, {"endpoint": "/users/1"})
        manager.record_gauge("active_connections", 5)

        metrics = manager.get_metrics()

        assert "api_calls" in metrics
        assert "response_time" in metrics
        assert "active_connections" in metrics


class TestServiceCommunication:
    """服务通信测试"""

    @pytest.mark.asyncio
    async def test_local_transport_communication(self):
        """测试本地传输通信"""
        transport_factory = LocalTransportFactory()
        proxy_factory = ServiceProxyFactory()

        user_service_def = ServiceDefinition("user-service", "1.0.0", "用户服务")
        user_repository = UserRepository()
        user_service = UserService(user_repository)

        user_transport = transport_factory.create_transport(user_service_def)
        user_transport.register_service(user_service)

        context = ServiceContext("user-service", "get_user", "req-1")
        request = ServiceRequest("user-service", "get_user", args=(1,), context=context)

        response = await user_transport.send_request(request)

        assert response is not None
        assert response.success is True
        assert response.data["id"] == 1

    @pytest.mark.asyncio
    async def test_cross_service_communication(self):
        """测试跨服务通信"""
        transport_factory = LocalTransportFactory()

        user_service_def = ServiceDefinition("user-service", "1.0.0", "用户服务")
        order_service_def = ServiceDefinition("order-service", "1.0.0", "订单服务")

        user_repository = UserRepository()
        order_repository = OrderRepository()
        user_service = UserService(user_repository)
        order_service = OrderService(order_repository, user_service)

        user_transport = transport_factory.create_transport(user_service_def)
        order_transport = transport_factory.create_transport(order_service_def)

        user_transport.register_service(user_service)
        order_transport.register_service(order_service)

        # 通过订单服务调用，间接调用用户服务
        context = ServiceContext("order-service", "get_order", "req-1")
        request = ServiceRequest("order-service", "get_order", args=(1,), context=context)

        response = await order_transport.send_request(request)

        assert response is not None
        assert response.success is True
        assert response.data["user"]["id"] == 1


class TestCompleteIntegration:
    """完整集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_scenario(self):
        """测试端到端场景"""
        # 1. 创建所有组件
        container = DIContainer()

        user_repository = UserRepository()
        order_repository = OrderRepository()

        container.register_instance(UserRepository, user_repository)
        container.register_instance(OrderRepository, order_repository)
        container.register_factory(UserService, lambda: UserService(user_repository))
        container.register_factory(OrderService, lambda: OrderService(order_repository, UserService(user_repository)))

        # 2. 解析服务
        user_service = container.resolve(UserService)
        order_service = container.resolve(OrderService)

        # 3. 测试完整流程
        # 获取用户信息
        user = await user_service.get_user(1)
        assert user["id"] == 1

        # 获取订单（包含用户信息）
        order = await order_service.get_order(1)
        assert order["id"] == 1
        assert order["user"]["id"] == 1

        # 获取用户的所有订单
        user_orders = await order_service.get_user_orders(1)
        assert len(user_orders) == 2

    @pytest.mark.asyncio
    async def test_async_concurrent_processing(self):
        """测试异步并发处理"""
        user_repository = UserRepository()
        user_service = UserService(user_repository)

        # 并发调用
        tasks = [user_service.get_user(i) for i in range(1, 6)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for i, result in enumerate(results, start=1):
            assert result["id"] == i