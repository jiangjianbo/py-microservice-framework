"""
用户数据存储层
"""

class UserRepository:
    """用户数据存储"""

    async def find(self, user_id: int):
        """
        根据用户ID查找用户

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典
        """
        # 模拟数据存储
        return {
            "id": user_id,
            "name": "Alice",
            "email": f"alice{user_id}@example.com"
        }