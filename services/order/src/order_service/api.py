"""
订单服务API层
"""

from litestar import get, post
from order_service.service import OrderService


@get("/orders/{order_id:int}")
async def get_order(
    order_id: int,
    service: OrderService,
):
    """
    获取订单信息API

    Args:
        order_id: 订单ID
        service: 订单服务实例

    Returns:
        订单信息
    """
    return await service.get_order(order_id)


@get("/orders/user/{user_id:int}")
async def get_user_orders(
    user_id: int,
    service: OrderService,
):
    """
    获取用户的所有订单API

    Args:
        user_id: 用户ID
        service: 订单服务实例

    Returns:
        订单列表
    """
    return await service.get_user_orders(user_id)


@post("/orders")
async def create_order(
    service: OrderService,
    data: dict,
):
    """
    创建订单API

    Args:
        service: 订单服务实例
        data: 订单数据

    Returns:
        创建结果
    """
    # 这里可以实现创建订单的逻辑
    return {
        "message": "订单创建成功",
        "order": data
    }