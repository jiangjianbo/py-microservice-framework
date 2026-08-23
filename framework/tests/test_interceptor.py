"""
服务拦截器模块单元测试

测试拦截器管道和各种拦截器的实现。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from serviceframework.interceptor.base import ServiceInterceptor, InterceptorContext
from serviceframework.interceptor.pipeline import InterceptorPipeline
from serviceframework.contract.service import ServiceContext, ServiceError
from dataclasses import dataclass


class TestInterceptorContext:
    
    def test_context_creation(self):
        """测试拦截器上下文创建"""
        service_context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123"
        )
        
        context = InterceptorContext(
            service_context=service_context,
            method="get_user",
            args=(123,),
            kwargs={"include_profile": True}
        )
        
        assert context.service_context == service_context
        assert context.method == "get_user"
        assert context.args == (123,)
        assert context.kwargs == {"include_profile": True}
    
    def test_context_with_result(self):
        """测试设置和获取结果"""
        service_context = ServiceContext("user-service", "get_user")
        
        context = InterceptorContext(
            service_context=service_context,
            method="get_user",
            args=(123,),
            kwargs={}
        )
        
        result = {"id": 123, "name": "Alice"}
        context.result = result
        
        assert context.result == result
    
    def test_context_with_error(self):
        """测试设置和获取错误"""
        service_context = ServiceContext("user-service", "get_user")
        
        context = InterceptorContext(
            service_context=service_context,
            method="get_user",
            args=(123,),
            kwargs={}
        )
        
        error = ServiceError("用户不存在", code="USER_NOT_FOUND")
        context.error = error
        
        assert context.error == error
    
    def test_context_metadata(self):
        """测试元数据操作"""
        service_context = ServiceContext("user-service", "get_user")
        
        context = InterceptorContext(
            service_context=service_context,
            method="get_user",
            args=(123,),
            kwargs={}
        )
        
        context.add_metadata("user_id", 123)
        context.add_metadata("action", "get_user")
        
        assert context.get_metadata("user_id") == 123
        assert context.get_metadata("action") == "get_user"
        assert context.get_metadata("nonexistent", "default") == "default"


class TestServiceInterceptor:
    
    @pytest.mark.asyncio
    async def test_interceptor_protocol(self):
        """测试拦截器协议"""
        from typing import Protocol
        
        # 检查ServiceInterceptor是否为Protocol
        assert issubclass(ServiceInterceptor, Protocol)
    
    @pytest.mark.asyncio
    async def test_base_interceptor_methods(self):
        """测试基础拦截器方法"""
        class MockInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                pass
            
            async def after(self, context: InterceptorContext, result):
                pass
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                pass
        
        interceptor = MockInterceptor()
        service_context = ServiceContext("user-service", "get_user")
        context = InterceptorContext(service_context, "get_user", (), {})
        
        # 测试各个方法
        await interceptor.before(context)
        await interceptor.after(context, {"id": 123})
        await interceptor.on_error(context, Exception("test error"))
        
        assert True  # 如果没有异常，测试通过


class TestInterceptorPipeline:
    
    @pytest.mark.asyncio
    async def test_pipeline_creation(self):
        """测试管道创建"""
        pipeline = InterceptorPipeline()
        assert pipeline is not None
        assert len(pipeline.get_interceptors()) == 0
    
    @pytest.mark.asyncio
    async def test_add_interceptor(self):
        """测试添加拦截器"""
        pipeline = InterceptorPipeline()
        
        class MockInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                pass
            
            async def after(self, context: InterceptorContext, result):
                pass
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                pass
        
        interceptor = MockInterceptor()
        pipeline.add_interceptor(interceptor)
        
        assert len(pipeline.get_interceptors()) == 1
    
    @pytest.mark.asyncio
    async def test_add_multiple_interceptors(self):
        """测试添加多个拦截器"""
        pipeline = InterceptorPipeline()
        
        class MockInterceptor(ServiceInterceptor):
            def __init__(self, name: str):
                self.name = name
            
            async def before(self, context: InterceptorContext):
                pass
            
            async def after(self, context: InterceptorContext, result):
                pass
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                pass
        
        for i in range(3):
            interceptor = MockInterceptor(f"interceptor-{i}")
            pipeline.add_interceptor(interceptor)
        
        assert len(pipeline.get_interceptors()) == 3
    
    @pytest.mark.asyncio
    async def test_remove_interceptor(self):
        """测试移除拦截器"""
        pipeline = InterceptorPipeline()
        
        class MockInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                pass
            
            async def after(self, context: InterceptorContext, result):
                pass
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                pass
        
        interceptor = MockInterceptor()
        pipeline.add_interceptor(interceptor)
        
        assert len(pipeline.get_interceptors()) == 1
        
        pipeline.remove_interceptor(interceptor)
        assert len(pipeline.get_interceptors()) == 0
    
    @pytest.mark.asyncio
    async def test_execute_with_no_interceptors(self):
        """测试无拦截器时直接执行目标"""
        pipeline = InterceptorPipeline()
        
        service_context = ServiceContext("user-service", "get_user")
        context = InterceptorContext(service_context, "get_user", (123,), {})
        
        async def target():
            return {"id": 123, "name": "Alice"}
        
        result = await pipeline.execute(context, target)
        
        assert result["id"] == 123
        assert result["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_execute_with_single_interceptor(self):
        """测试单个拦截器执行"""
        pipeline = InterceptorPipeline()
        
        calls = []
        
        class LoggingInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                calls.append("before")
                context.add_metadata("logged", True)
            
            async def after(self, context: InterceptorContext, result):
                calls.append("after")
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                calls.append("error")
        
        pipeline.add_interceptor(LoggingInterceptor())
        
        service_context = ServiceContext("user-service", "get_user")
        context = InterceptorContext(service_context, "get_user", (123,), {})
        
        async def target():
            return {"id": 123, "name": "Alice"}
        
        result = await pipeline.execute(context, target)
        
        assert "before" in calls
        assert "after" in calls
        assert context.get_metadata("logged") is True
        assert result["id"] == 123
    
    @pytest.mark.asyncio
    async def test_execute_with_multiple_interceptors(self):
        """测试多个拦截器按顺序执行"""
        pipeline = InterceptorPipeline()
        
        execution_order = []
        
        class FirstInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                execution_order.append("first_before")
                context.add_metadata("first", True)
            
            async def after(self, context: InterceptorContext, result):
                execution_order.append("first_after")
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                execution_order.append("first_error")
        
        class SecondInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                execution_order.append("second_before")
                context.add_metadata("second", True)
            
            async def after(self, context: InterceptorContext, result):
                execution_order.append("second_after")
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                execution_order.append("second_error")
        
        pipeline.add_interceptor(FirstInterceptor())
        pipeline.add_interceptor(SecondInterceptor())
        
        service_context = ServiceContext("user-service", "get_user")
        context = InterceptorContext(service_context, "get_user", (123,), {})
        
        async def target():
            return {"id": 123, "name": "Alice"}
        
        result = await pipeline.execute(context, target)
        
        # 验证执行顺序
        assert execution_order == [
            "first_before", "second_before",  # before方法按顺序执行
            "second_after", "first_after"     # after方法按逆序执行
        ]
        assert context.get_metadata("first") is True
        assert context.get_metadata("second") is True
        assert result["id"] == 123
    
    @pytest.mark.asyncio
    async def test_execute_with_exception(self):
        """测试目标函数抛出异常"""
        pipeline = InterceptorPipeline()
        
        error_interceptor_calls = []
        
        class ErrorInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                pass
            
            async def after(self, context: InterceptorContext, result):
                pass
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                error_interceptor_calls.append(error)
                context.add_metadata("error_handled", True)
        
        pipeline.add_interceptor(ErrorInterceptor())
        
        service_context = ServiceContext("user-service", "get_user")
        context = InterceptorContext(service_context, "get_user", (0,), {})
        
        async def target():
            raise ServiceError("用户不存在", code="USER_NOT_FOUND")
        
        # 应该抛出异常
        with pytest.raises(ServiceError, match="用户不存在"):
            await pipeline.execute(context, target)
        
        # 错误拦截器应该被调用
        assert len(error_interceptor_calls) == 1
        assert context.get_metadata("error_handled") is True
    
    @pytest.mark.asyncio
    async def test_interceptor_can_skip_execution(self):
        """测试拦截器可以跳过后续执行"""
        pipeline = InterceptorPipeline()
        
        calls = []
        
        class SkipInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                calls.append("skip")
                context.skip_execution = True
                context.result = {"cached": True}
            
            async def after(self, context: InterceptorContext, result):
                calls.append("skip_after")
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                calls.append("skip_error")
        
        class SecondInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                calls.append("second_before")
            
            async def after(self, context: InterceptorContext, result):
                calls.append("second_after")
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                calls.append("second_error")
        
        pipeline.add_interceptor(SkipInterceptor())
        pipeline.add_interceptor(SecondInterceptor())
        
        service_context = ServiceContext("user-service", "get_user")
        context = InterceptorContext(service_context, "get_user", (123,), {})
        
        async def target():
            return {"id": 123, "name": "Alice"}
        
        result = await pipeline.execute(context, target)
        
        # 应该只执行第一个拦截器
        assert "skip" in calls
        assert "second_before" not in calls
        assert result == {"cached": True}
    
    @pytest.mark.asyncio
    async def test_clear_interceptors(self):
        """测试清空拦截器"""
        pipeline = InterceptorPipeline()
        
        class MockInterceptor(ServiceInterceptor):
            async def before(self, context: InterceptorContext):
                pass
            
            async def after(self, context: InterceptorContext, result):
                pass
            
            async def on_error(self, context: InterceptorContext, error: Exception):
                pass
        
        pipeline.add_interceptor(MockInterceptor())
        pipeline.add_interceptor(MockInterceptor())
        
        assert len(pipeline.get_interceptors()) == 2
        
        pipeline.clear()
        
        assert len(pipeline.get_interceptors()) == 0