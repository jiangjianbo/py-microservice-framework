"""
OpenTelemetry可观测性模块单元测试

测试追踪、指标和日志的可观测性功能。
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from serviceframework.observability.telemetry import TelemetryManager, TraceConfig, SpanKind
from serviceframework.contract.service import ServiceContext


class TestTraceConfig:
    
    def test_config_creation(self):
        """测试追踪配置创建"""
        config = TraceConfig(
            service_name="user-service",
            endpoint="http://jaeger:14268/api/v2/spans",
            sample_rate=1.0,
            enabled=True
        )
        
        assert config.service_name == "user-service"
        assert config.endpoint == "http://jaeger:14268/api/v2/spans"
        assert config.sample_rate == 1.0
        assert config.enabled is True


class TestTelemetryManager:
    
    def test_manager_creation(self):
        """测试管理器创建"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans")
        manager = TelemetryManager(config)
        
        assert manager.config == config
        assert manager.is_enabled() is True
    
    def test_disabled_manager(self):
        """测试禁用的管理器"""
        config = TraceConfig(
            service_name="user-service",
            endpoint="http://jaeger:14268/api/v2/spans",
            enabled=False
        )
        manager = TelemetryManager(config)

        assert manager.is_enabled() is False
    
    def test_create_span(self):
        """测试创建Span"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        service_context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123"
        )
        
        span = manager.create_span("get_user", service_context)
        
        assert span is not None
        assert span.name == "get_user"
        assert span.service_name == "user-service"
    
    def test_span_with_kind(self):
        """测试不同类型的Span"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        service_context = ServiceContext("user-service", "get_user")
        
        # 创建服务器Span
        server_span = manager.create_span("server", service_context, kind=SpanKind.SERVER)
        assert server_span.kind == SpanKind.SERVER
        
        # 创建客户端Span
        client_span = manager.create_span("client", service_context, kind=SpanKind.CLIENT)
        assert client_span.kind == SpanKind.CLIENT
        
        # 创建内部Span
        internal_span = manager.create_span("internal", service_context, kind=SpanKind.INTERNAL)
        assert internal_span.kind == SpanKind.INTERNAL
    
    @pytest.mark.asyncio
    async def test_span_lifecycle(self):
        """测试Span生命周期"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        service_context = ServiceContext("user-service", "get_user")
        
        # 创建并开始Span
        span = manager.create_span("get_user", service_context)
        assert span.is_started is False
        
        await span.start()
        assert span.is_started is True
        
        # 结束Span
        await span.end()
        assert span.is_ended is True
    
    @pytest.mark.asyncio
    async def test_span_with_attributes(self):
        """测试带属性的Span"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        service_context = ServiceContext("user-service", "get_user")
        span = manager.create_span("get_user", service_context)
        
        # 添加属性
        span.set_attribute("user_id", "123")
        span.set_attribute("action", "get_user")
        span.set_attribute("success", True)
        
        await span.start()
        
        assert span.get_attribute("user_id") == "123"
        assert span.get_attribute("action") == "get_user"
        assert span.get_attribute("success") is True
        
        await span.end()
    
    @pytest.mark.asyncio
    async def test_span_with_events(self):
        """测试Span事件"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        service_context = ServiceContext("user-service", "get_user")
        span = manager.create_span("get_user", service_context)
        
        events = []
        
        # 注册事件监听器
        def event_handler(event):
            events.append(event)
        
        span.add_event_listener(event_handler)
        
        await span.start()
        span.set_attribute("test", "value")
        await span.end()
        
        # 应该有开始和结束事件
        assert len(events) > 0
    
    @pytest.mark.asyncio
    async def test_span_with_parent(self):
        """测试父子Span关系"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        service_context = ServiceContext("user-service", "get_user")
        
        # 父Span
        parent_span = manager.create_span("get_user", service_context)
        
        # 创建子Span
        child_span = parent_span.create_child_span("query_database")
        
        await parent_span.start()
        await child_span.start()
        await child_span.end()
        await parent_span.end()
        
        # 验证父子关系
        assert child_span.parent is parent_span
    
    @pytest.mark.asyncio
    async def test_span_error_handling(self):
        """测试Span错误处理"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        service_context = ServiceContext("user-service", "get_user")
        span = manager.create_span("get_user", service_context)
        
        await span.start()
        
        # 记录错误
        error = ValueError("用户不存在")
        span.record_error(error)
        
        await span.end()
        
        # 验证错误被记录
        errors = span.get_errors()
        assert len(errors) > 0
        assert any("用户不存在" in str(e) for e in errors)
    
    def test_manager_create_span_with_context(self):
        """测试通过上下文创建Span"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        service_context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123",
            metadata={"user_id": "123"}
        )
        
        span = manager.create_span("get_user", service_context)
        
        # 验证上下文信息被正确传递到Span
        assert span.context == service_context
        assert span.trace_id == "req-123"
    
    def test_metrics_recording(self):
        """测试指标记录"""
        config = TraceConfig(service_name="user-service", endpoint="http://jaeger:14268/api/v2/spans", enabled=True)
        manager = TelemetryManager(config)
        
        # 记录指标
        manager.record_counter("http_requests_total", 1, {"method": "GET", "path": "/users"})
        manager.record_histogram("http_request_duration_ms", 123.5, {"method": "GET", "path": "/users"})
        manager.record_gauge("active_connections", 5)
        
        metrics = manager.get_metrics()
        
        assert "http_requests_total" in metrics
        assert "http_request_duration_ms" in metrics
        assert "active_connections" in metrics


class TestSpanKind:
    
    def test_span_kind_values(self):
        """测试SpanKind枚举值"""
        assert hasattr(SpanKind, 'SERVER')
        assert hasattr(SpanKind, 'CLIENT')
        assert hasattr(SpanKind, 'INTERNAL')
        assert hasattr(SpanKind, 'PRODUCER')
        assert hasattr(SpanKind, 'CONSUMER')