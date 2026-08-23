"""
用户服务层
"""

from typing import Dict, Any


class UserService:
    """用户服务"""

    def __init__(self, repository):
        """
        初始化用户服务

        Args:
            repository: 用户数据存储
        """
        self.repository = repository

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典
        """
        return await self.repository.find(user_id)