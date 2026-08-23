"""
用户服务集成测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from httpx import AsyncClient
from litestar import Litestar
from litestar.testing import AsyncTestClient

# 导入用户服务模块
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from user_service.repository import UserRepository
from user_service.service import UserService
from user_service.api import get_user


class TestUserServiceIntegration:
    """用户服务集成测试"""

    @pytest.mark.asyncio
    async def test_repository_find_user(self):
        """测试用户存储查找用户"""
        repository = UserRepository()
        user = await repository.find(1)

        assert user is not None
        assert user["id"] == 1
        assert user["name"] == "Alice"
        assert user["email"] == "alice1@example.com"

    @pytest.mark.asyncio
    async def test_service_get_user(self):
        """测试用户服务获取用户"""
        repository = UserRepository()
        service = UserService(repository)

        user = await service.get_user(1)

        assert user is not None
        assert user["id"] == 1
        assert user["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_service_with_different_user_ids(self):
        """测试用户服务获取不同用户"""
        repository = UserRepository()
        service = UserService(repository)

        user1 = await service.get_user(1)
        user2 = await service.get_user(2)

        assert user1["id"] == 1
        assert user2["id"] == 2
        assert user1["name"] == user2["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_api_get_user_endpoint(self):
        """测试API端点获取用户"""
        # 创建测试应用
        from litestar import Litestar

        # 创建依赖提供者
        repository = UserRepository()
        service = UserService(repository)

        # 创建测试应用
        app = Litestar(
            route_handlers=[get_user],
            dependencies={"service": service}
        )

        # 创建测试客户端
        async with AsyncTestClient(app=app) as client:
            response = await client.get("/users/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_api_get_user_different_ids(self):
        """测试API端点获取不同用户"""
        from litestar import Litestar

        repository = UserRepository()
        service = UserService(repository)

        app = Litestar(
            route_handlers=[get_user],
            dependencies={"service": service}
        )

        async with AsyncTestClient(app=app) as client:
            response1 = await client.get("/users/1")
            response2 = await client.get("/users/2")

            assert response1.status_code == 200
            assert response2.status_code == 200

            data1 = response1.json()
            data2 = response2.json()

            assert data1["id"] == 1
            assert data2["id"] == 2
            assert data1["name"] == data2["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_full_integration_flow(self):
        """测试完整的集成流程"""
        # 1. 创建Repository
        repository = UserRepository()
        # 2. 创建Service
        service = UserService(repository)
        # 3. 创建API应用
        from litestar import Litestar
        app = Litestar(
            route_handlers=[get_user],
            dependencies={"service": service}
        )

        # 4. 测试完整流程
        async with AsyncTestClient(app=app) as client:
            # 直接通过repository测试
            repo_data = await repository.find(100)
            assert repo_data["id"] == 100

            # 通过service测试
            service_data = await service.get_user(100)
            assert service_data["id"] == 100

            # 通过API测试
            api_response = await client.get("/users/100")
            api_data = api_response.json()
            assert api_data["id"] == 100

            # 验证数据一致性
            assert repo_data == service_data == api_data

    @pytest.mark.asyncio
    async def test_async_behavior(self):
        """测试异步行为"""
        import time

        repository = UserRepository()
        service = UserService(repository)

        start_time = time.time()

        # 模拟并发请求
        tasks = [service.get_user(i) for i in range(1, 10)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        elapsed_time = end_time - start_time

        # 验证所有结果都正确
        assert len(results) == 9
        for i, user in enumerate(results, start=1):
            assert user["id"] == i
            assert user["name"] == "Alice"

        # 验证确实是异步并发执行
        # 如果是串行执行，时间会更长
        assert elapsed_time < 1.0  # 应该很快完成

    def test_imports_work(self):
        """测试导入是否正常工作"""
        from user_service.repository import UserRepository
        from user_service.service import UserService
        from user_service.api import get_user

        assert UserRepository is not None
        assert UserService is not None
        assert get_user is not None