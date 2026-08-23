"""
Service Demo 集成测试

测试 build-spec.md 中第31章节的 Service Demo 案例是否能正常运行
"""

import pytest
import asyncio
import sys
import os

# 添加services/user/src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'user', 'src'))


class TestServiceDemoIntegration:
    """Service Demo 集成测试"""

    @pytest.mark.asyncio
    async def test_repository_basic_functionality(self):
        """测试UserRepository基本功能"""
        from user_service.repository import UserRepository

        repository = UserRepository()

        # 测试查找用户
        user = await repository.find(1)
        assert user is not None
        assert user["id"] == 1
        assert user["name"] == "Alice"
        assert "email" in user

        # 测试不同用户ID
        user2 = await repository.find(2)
        assert user2["id"] == 2
        assert user2["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_service_basic_functionality(self):
        """测试UserService基本功能"""
        from user_service.repository import UserRepository
        from user_service.service import UserService

        # 创建依赖对象
        repository = UserRepository()
        service = UserService(repository)

        # 测试获取用户
        user = await service.get_user(1)
        assert user is not None
        assert user["id"] == 1
        assert user["name"] == "Alice"

        # 验证服务正确调用了repository
        direct_user = await repository.find(1)
        assert user == direct_user

    @pytest.mark.asyncio
    async def test_service_integration(self):
        """测试Service和Repository集成"""
        from user_service.repository import UserRepository
        from user_service.service import UserService

        repository = UserRepository()
        service = UserService(repository)

        # 测试多个用户
        test_user_ids = [1, 2, 3, 100, 999]

        for user_id in test_user_ids:
            user = await service.get_user(user_id)
            assert user["id"] == user_id
            assert user["name"] == "Alice"
            assert f"alice{user_id}@example.com" in user["email"]

    @pytest.mark.asyncio
    async def test_async_behavior(self):
        """测试异步行为"""
        import time
        from user_service.repository import UserRepository
        from user_service.service import UserService

        repository = UserRepository()
        service = UserService(repository)

        start_time = time.time()

        # 并发调用
        tasks = [service.get_user(i) for i in range(1, 10)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        elapsed_time = end_time - start_time

        # 验证结果
        assert len(results) == 9
        for i, user in enumerate(results, start=1):
            assert user["id"] == i
            assert user["name"] == "Alice"

        # 验证异步并发（应该很快完成）
        assert elapsed_time < 1.0

    def test_module_imports(self):
        """测试模块导入"""
        # 测试所有模块都能正确导入
        from user_service.repository import UserRepository
        from user_service.service import UserService

        # 测试类存在
        assert UserRepository is not None
        assert UserService is not None

        # 测试类可以实例化
        repository = UserRepository()
        service = UserService(repository)

        assert repository is not None
        assert service is not None
        assert service.repository == repository

    @pytest.mark.asyncio
    async def test_service_demo_full_flow(self):
        """测试完整的Service Demo流程"""
        from user_service.repository import UserRepository
        from user_service.service import UserService

        # 模拟完整的Service Demo流程
        # 1. Repository层
        repository = UserRepository()
        assert repository is not None

        # 2. Service层
        service = UserService(repository)
        assert service is not None
        assert service.repository == repository

        # 3. Service调用
        user = await service.get_user(42)
        assert user["id"] == 42
        assert user["name"] == "Alice"

        # 4. 验证数据一致性
        direct_data = await repository.find(42)
        assert user == direct_data

    @pytest.mark.asyncio
    async def test_service_demo_data_flow(self):
        """测试数据流向"""
        from user_service.repository import UserRepository
        from user_service.service import UserService

        # 创建数据链：Repository -> Service -> Application
        repository = UserRepository()
        service = UserService(repository)

        # 测试数据流向
        input_id = 123

        # Repository层数据
        repo_data = await repository.find(input_id)
        assert repo_data["id"] == input_id

        # Service层数据
        service_data = await service.get_user(input_id)
        assert service_data == repo_data

        # 验证数据结构符合预期
        expected_fields = ["id", "name", "email"]
        for field in expected_fields:
            assert field in service_data

    def test_service_architecture(self):
        """测试服务架构符合设计要求"""
        from user_service.repository import UserRepository
        from user_service.service import UserService
        import inspect

        # 测试Repository层设计
        assert hasattr(UserRepository, 'find')
        assert inspect.iscoroutinefunction(UserRepository.find)

        # 测试Service层设计
        assert hasattr(UserService, '__init__')
        assert hasattr(UserService, 'get_user')
        assert inspect.iscoroutinefunction(UserService.get_user)

        # 测试Service构造函数接受repository参数
        sig = inspect.signature(UserService.__init__)
        assert 'repository' in sig.parameters

    @pytest.mark.asyncio
    async def test_service_concurrent_access(self):
        """测试并发访问"""
        from user_service.repository import UserRepository
        from user_service.service import UserService

        repository = UserRepository()
        service = UserService(repository)

        # 模拟多个并发请求
        async def concurrent_request(user_id):
            return await service.get_user(user_id)

        # 创建10个并发请求
        tasks = [concurrent_request(i) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)

        # 验证所有请求都成功
        assert len(results) == 10
        for i, result in enumerate(results, start=1):
            assert result["id"] == i
            assert result["name"] == "Alice"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])