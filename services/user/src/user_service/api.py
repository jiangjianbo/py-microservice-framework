"""
用户服务API层
"""

from litestar import get
from user_service.service import UserService


@get("/users/{user_id:int}")
async def get_user(
    user_id: int,
    service: UserService,
):
    """
    获取用户信息API

    Args:
        user_id: 用户ID
        service: 用户服务实例

    Returns:
        用户信息
    """
    return await service.get_user(user_id)