"""
订单服务示例
"""

class OrderRepository:
    """订单数据存储"""

    def __init__(self):
        # 模拟数据存储
        self._orders = {
            1: {"id": 1, "user_id": 1, "product": "Product A", "amount": 100.0},
            2: {"id": 2, "user_id": 1, "product": "Product B", "amount": 150.0},
            3: {"id": 3, "user_id": 2, "product": "Product C", "amount": 200.0},
        }

    async def find(self, order_id: int):
        """根据订单ID查找订单"""
        return self._orders.get(order_id)

    async def find_by_user(self, user_id: int):
        """根据用户ID查找订单"""
        return [order for order in self._orders.values() if order["user_id"] == user_id]