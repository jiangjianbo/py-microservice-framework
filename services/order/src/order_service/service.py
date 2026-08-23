"""
订单服务层
"""

from typing import List, Dict, Any


class OrderService:
    """订单服务"""

    def __init__(self, repository):
        """
        初始化订单服务

        Args:
            repository: 订单数据存储
        """
        self.repository = repository

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """
        获取订单信息

        Args:
            order_id: 订单ID

        Returns:
            订单信息字典
        """
        return await self.repository.find(order_id)

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户的所有订单

        Args:
            user_id: 用户ID

        Returns:
            订单列表
        """
        return await self.repository.find_by_user(user_id)