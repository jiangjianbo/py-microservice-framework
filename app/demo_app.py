"""
微服务框架完整示例应用

演示框架的核心功能：
- 服务创建和注册
- 进程内服务通信
- 服务间调用
- 依赖注入
- 可观测性追踪
- 拦截器使用
"""

import asyncio
import time
from typing import Dict, Any

from serviceframework.contract.service import (
    ServiceDefinition, ServiceContext, ServiceMetadata, ServiceError,
)
from serviceframework.contract.request import ServiceRequest
from serviceframework.contract.response import ServiceResponse
from serviceframework.proxy.factory import ProxyFactory
from serviceframework.registry.registry import ServiceRegistry
from serviceframework.transport.local import LocalTransport
from serviceframework.interceptor.pipeline import InterceptorPipeline
from serviceframework.interceptor.base import ServiceInterceptor, InterceptorContext
from serviceframework.observability.telemetry import TelemetryManager
from serviceframework.observability.config import TraceConfig
from serviceframework.runtime.di import DependencyContainer

# 兼容别名：示例与测试统一使用的名字
DIContainer = DependencyContainer
ServiceProxyFactory = ProxyFactory


class LoggingInterceptor(ServiceInterceptor):
    """日志拦截器：调用前后输出日志"""

    def __init__(self):
        self.call_count = 0
        self.error_count = 0

    async def before(self, context: InterceptorContext) -> None:
        self.call_count += 1
        print(f"[LOGGING] 调用服务: {context.service_context.service_name}.{context.method}")

    async def after(self, context: InterceptorContext, result: Any) -> None:
        print(f"[LOGGING] 调用成功")

    async def on_error(self, context: InterceptorContext, error: Exception) -> None:
        self.error_count += 1
        print(f"[LOGGING] 调用失败: {error}")


class MetricsInterceptor(ServiceInterceptor):
    """指标拦截器：统计调用次数、错误次数和耗时"""

    def __init__(self):
        self.call_count = 0
        self.error_count = 0

    async def before(self, context: InterceptorContext) -> None:
        self.call_count += 1
        context.add_metadata("metrics_start_time", time.monotonic())

    async def after(self, context: InterceptorContext, result: Any) -> None:
        start = context.get_metadata("metrics_start_time")
        if start is not None:
            duration = time.monotonic() - start
            print(f"[METRICS] 调用次数: {self.call_count}, 耗时: {duration:.6f}s")

    async def on_error(self, context: InterceptorContext, error: Exception) -> None:
        self.error_count += 1
        print(f"[METRICS] 错误次数: {self.error_count}")


class UserRepository:
    """用户数据存储"""

    async def find(self, user_id: int) -> Dict[str, Any]:
        """查找用户"""
        return {
            "id": user_id,
            "name": f"User{user_id}",
            "email": f"user{user_id}@example.com"
        }

    async def find_all(self) -> list:
        """查找所有用户"""
        return [
            {"id": 1, "name": "User1", "email": "user1@example.com"},
            {"id": 2, "name": "User2", "email": "user2@example.com"},
        ]


class OrderRepository:
    """订单数据存储"""

    def __init__(self):
        self._orders = {
            1: {"id": 1, "user_id": 1, "product": "Product A", "amount": 100.0},
            2: {"id": 2, "user_id": 1, "product": "Product B", "amount": 150.0},
            3: {"id": 3, "user_id": 2, "product": "Product C", "amount": 200.0},
        }

    async def find(self, order_id: int) -> Dict[str, Any]:
        """查找订单"""
        return self._orders.get(order_id)

    async def find_by_user(self, user_id: int) -> list:
        """根据用户ID查找订单"""
        return [order for order in self._orders.values() if order["user_id"] == user_id]


class UserService:
    """用户服务"""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """获取用户"""
        return await self.repository.find(user_id)

    async def get_all_users(self) -> list:
        """获取所有用户"""
        return await self.repository.find_all()


class OrderService:
    """订单服务"""

    def __init__(self, repository: OrderRepository, user_service: UserService):
        self.repository = repository
        self.user_service = user_service

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """获取订单"""
        order = await self.repository.find(order_id)
        if order:
            # 通过服务调用获取用户信息
            user = await self.user_service.get_user(order["user_id"])
            order["user"] = user
        return order

    async def get_user_orders(self, user_id: int) -> list:
        """获取用户的所有订单"""
        orders = await self.repository.find_by_user(user_id)
        user = await self.user_service.get_user(user_id)
        for order in orders:
            order["user"] = user
        return orders


class LocalTransportEndpoint:
    """
    本地传输端点

    包装 LocalTransport，提供请求-响应式的进程内服务调用。
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._transport: LocalTransport = None

    def register_service(self, service: Any) -> None:
        """注册服务实例到传输端点"""
        self._transport = LocalTransport(service)

    async def send_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        发送服务调用请求

        Args:
            request: 服务请求

        Returns:
            服务响应

        Raises:
            RuntimeError: 如果服务未注册
        """
        if self._transport is None:
            raise RuntimeError(f"服务'{self.service_name}'未注册到传输端点")

        try:
            data = await self._transport.invoke(
                request.method, *request.args, **request.kwargs
            )
            return ServiceResponse.success_response(data)
        except Exception as exc:
            if isinstance(exc, ServiceError):
                error = exc
            else:
                error = ServiceError(str(exc), code="TRANSPORT_ERROR")
            return ServiceResponse.error_response(error)


class LocalTransportFactory:
    """本地传输工厂：为服务定义创建进程内传输端点"""

    def create_transport(self, service_def: ServiceDefinition) -> LocalTransportEndpoint:
        """根据服务定义创建本地传输端点"""
        return LocalTransportEndpoint(service_def.name)


async def demo_basic_service():
    """基础服务演示"""
    print("=" * 50)
    print("基础服务演示")
    print("=" * 50)

    # 创建数据存储
    user_repository = UserRepository()
    order_repository = OrderRepository()

    # 创建服务
    user_service = UserService(user_repository)
    order_service = OrderService(order_repository, user_service)

    # 测试基础服务功能
    print("\n1. 获取单个用户:")
    user = await user_service.get_user(1)
    print(f"   结果: {user}")

    print("\n2. 获取所有用户:")
    users = await user_service.get_all_users()
    print(f"   结果: {users}")

    print("\n3. 获取订单（包含用户信息）:")
    order = await order_service.get_order(1)
    print(f"   结果: {order}")

    print("\n4. 获取用户的所有订单:")
    user_orders = await order_service.get_user_orders(1)
    print(f"   结果: {user_orders}")


async def demo_service_registry():
    """服务注册演示"""
    print("\n" + "=" * 50)
    print("服务注册演示")
    print("=" * 50)

    # 创建服务注册表
    registry = ServiceRegistry()

    # 创建服务实例
    user_repository = UserRepository()
    order_repository = OrderRepository()
    user_service = UserService(user_repository)
    order_service = OrderService(order_repository, user_service)

    # 注册服务（名称 + 实例 + 元数据）
    registry.register(
        "user-service",
        user_service,
        metadata=ServiceMetadata(name="user-service", version="1.0.0", description="用户服务"),
    )
    registry.register(
        "order-service",
        order_service,
        metadata=ServiceMetadata(name="order-service", version="1.0.0", description="订单服务"),
    )

    print(f"\n注册的服务: {registry.list_services()}")
    print(f"服务总数: {registry.count()}")


async def demo_dependency_injection():
    """依赖注入演示"""
    print("\n" + "=" * 50)
    print("依赖注入演示")
    print("=" * 50)

    # 创建DI容器
    container = DIContainer()

    # 注册依赖
    user_repository = UserRepository()
    order_repository = OrderRepository()

    container.register_instance(UserRepository, user_repository)
    container.register_instance(OrderRepository, order_repository)
    container.register_factory(UserService, lambda: UserService(user_repository))
    container.register_factory(
        OrderService,
        lambda: OrderService(order_repository, UserService(user_repository)),
    )

    # 解析服务
    print("\n从DI容器解析服务...")
    user_service = container.resolve(UserService)
    order_service = container.resolve(OrderService)

    print(f"UserService实例: {user_service}")
    print(f"OrderService实例: {order_service}")
    print(f"OrderService中的UserService: {order_service.user_service}")

    # 测试服务功能
    user = await user_service.get_user(1)
    print(f"\n通过DI容器调用服务: {user}")


async def demo_interceptors():
    """拦截器演示"""
    print("\n" + "=" * 50)
    print("拦截器演示")
    print("=" * 50)

    # 创建拦截器管道
    pipeline = InterceptorPipeline()

    # 添加拦截器
    logging_interceptor = LoggingInterceptor()
    metrics_interceptor = MetricsInterceptor()

    pipeline.add_interceptor(logging_interceptor)
    pipeline.add_interceptor(metrics_interceptor)

    # 创建测试服务
    user_repository = UserRepository()
    user_service = UserService(user_repository)

    # 创建拦截上下文并执行
    print("\n执行带拦截器的服务调用...")
    service_context = ServiceContext("user-service", "get_user", "req-1")
    interceptor_context = InterceptorContext(
        service_context=service_context,
        method="get_user",
        args=(1,),
        kwargs={}
    )

    async def target():
        return await user_service.get_user(1)

    result = await pipeline.execute(interceptor_context, target)
    print(f"调用结果: {result}")

    print(f"\n指标统计: 调用次数={metrics_interceptor.call_count}, 错误次数={metrics_interceptor.error_count}")


async def demo_observability():
    """可观测性演示"""
    print("\n" + "=" * 50)
    print("可观测性演示")
    print("=" * 50)

    # 创建追踪管理器
    config = TraceConfig(
        service_name="demo-service",
        endpoint="http://localhost:14268/api/v2/spans",
        enabled=True
    )

    telemetry_manager = TelemetryManager(config)

    print(f"追踪管理器状态: {'启用' if telemetry_manager.is_enabled() else '禁用'}")

    # 创建服务上下文和Span
    service_context = ServiceContext("user-service", "get_user", "req-1")
    span = telemetry_manager.create_span("get_user", service_context)

    print(f"创建的Span: {span.name}, trace_id: {span.trace_id}")

    # 记录指标
    telemetry_manager.record_counter("api_calls", 1, {"endpoint": "/users/1"})
    telemetry_manager.record_histogram("response_time", 45.6, {"endpoint": "/users/1"})
    telemetry_manager.record_gauge("active_connections", 5)

    print("\n记录的指标:")
    metrics = telemetry_manager.get_metrics()
    for name, data in metrics.items():
        print(f"  {name}: {len(data)} 条记录")


async def demo_service_communication():
    """服务间通信演示"""
    print("\n" + "=" * 50)
    print("服务间通信演示")
    print("=" * 50)

    # 创建传输工厂和服务代理工厂
    transport_factory = LocalTransportFactory()
    proxy_factory = ServiceProxyFactory()

    # 创建服务实例
    user_repository = UserRepository()
    order_repository = OrderRepository()
    user_service = UserService(user_repository)
    order_service = OrderService(order_repository, user_service)

    # 创建传输端点并注册服务
    user_transport = transport_factory.create_transport(
        ServiceDefinition(name="user-service", version="1.0.0", description="用户服务")
    )
    order_transport = transport_factory.create_transport(
        ServiceDefinition(name="order-service", version="1.0.0", description="订单服务")
    )
    user_transport.register_service(user_service)
    order_transport.register_service(order_service)

    # 通过代理工厂创建本地代理
    user_proxy = proxy_factory.create_local_proxy("user-service", user_service)

    print("\n服务通信测试:")
    print("1. 通过传输层调用用户服务")
    request = ServiceRequest("user-service", "get_user", args=(1,))
    response = await user_transport.send_request(request)
    print(f"   结果: {response.data}")

    print("\n2. 通过本地代理调用用户服务")
    proxy_result = await user_proxy.invoke("get_user", 1)
    print(f"   结果: {proxy_result}")

    print("\n3. 通过传输层调用订单服务（包含用户信息）")
    request = ServiceRequest("order-service", "get_order", args=(1,))
    response = await order_transport.send_request(request)
    print(f"   结果: {response.data}")


async def main():
    """主函数"""
    print("🚀 Python 逻辑微服务框架完整示例")
    print("=" * 50)

    # 运行所有演示
    await demo_basic_service()
    await demo_service_registry()
    await demo_dependency_injection()
    await demo_interceptors()
    await demo_observability()
    await demo_service_communication()

    print("\n" + "=" * 50)
    print("✅ 所有演示完成！")
    print("=" * 50)
    print("\n框架核心功能演示总结:")
    print("✅ 基础服务功能 - Repository、Service、API分层架构")
    print("✅ 服务注册 - 动态服务发现")
    print("✅ 依赖注入 - 自动依赖解析和生命周期管理")
    print("✅ 拦截器链 - AOP编程和横切关注点")
    print("✅ 可观测性 - 分布式追踪和指标收集")
    print("✅ 服务通信 - 多种传输方式和代理模式")


if __name__ == "__main__":
    asyncio.run(main())
