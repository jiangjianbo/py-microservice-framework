"""
OpenTelemetry追踪模块

实现分布式追踪、指标记录和可观测性功能。
支持灵活的追踪后端集成和自定义Span管理。
"""

import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from serviceframework.observability.config import SpanKind, TraceConfig
from serviceframework.contract.service import ServiceContext


class SpanStatus(Enum):
    """Span状态枚举"""
    CREATED = "created"
    STARTED = "started"
    ENDED = "ended"
    ERROR = "error"


@dataclass
class SpanEvent:
    """Span事件"""
    timestamp: float
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricData:
    """指标数据"""
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)


class Span:
    """
    追踪Span
    
    表示追踪中的一个工作单元，可以嵌套形成调用链。
    支持生命周期管理、属性设置、事件监听、错误处理等功能。
    """
    
    def __init__(
        self,
        name: str,
        service_context: ServiceContext,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional["Span"] = None
    ):
        """
        初始化Span
        
        Args:
            name: Span名称
            service_context: 服务上下文
            kind: Span类型
            parent: 父Span
        """
        self.name = name
        self.kind = kind
        self.parent = parent
        self.context = service_context
        self.service_context = service_context
        self.service_name = service_context.service_name
        self.trace_id = service_context.request_id or str(uuid.uuid4())
        self._status = SpanStatus.CREATED
        
        self._attributes: Dict[str, Any] = {}
        self._events: List[SpanEvent] = []
        self._errors: List[Exception] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._event_listeners: List[Callable[[SpanEvent], None]] = []
    
    @property
    def is_started(self) -> bool:
        """检查Span是否已启动"""
        return self._status in [SpanStatus.STARTED, SpanStatus.ENDED, SpanStatus.ERROR]
    
    @property
    def is_ended(self) -> bool:
        """检查Span是否已结束"""
        return self._status in [SpanStatus.ENDED, SpanStatus.ERROR]
    
    def set_attribute(self, key: str, value: Any) -> None:
        """
        设置属性
        
        Args:
            key: 属性键
            value: 属性值
        """
        self._attributes[key] = value
    
    def get_attribute(self, key: str, default: Any = None) -> Any:
        """
        获取属性
        
        Args:
            key: 属性键
            default: 默认值
            
        Returns:
            属性值或默认值
        """
        return self._attributes.get(key, default)
    
    def add_event_listener(self, listener: Callable[[SpanEvent], None]) -> None:
        """
        添加事件监听器
        
        Args:
            listener: 事件监听器函数
        """
        self._event_listeners.append(listener)
    
    def _record_event(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """
        记录事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        event = SpanEvent(
            timestamp=time.time(),
            event_type=event_type,
            data=data or {}
        )
        self._events.append(event)
        
        # 通知监听器
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception:
                pass
    
    def create_child_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL) -> "Span":
        """
        创建子Span
        
        Args:
            name: Span名称
            kind: Span类型
            
        Returns:
            子Span实例
        """
        child_span = Span(name, self.service_context, kind, parent=self)
        return child_span
    
    async def start(self) -> None:
        """启动Span"""
        if self._status != SpanStatus.CREATED:
            raise ValueError(f"Span状态为{self._status.value}，无法启动")
        
        self._status = SpanStatus.STARTED
        self._start_time = time.time()
        self._record_event("start")
    
    async def end(self) -> None:
        """结束Span"""
        if not self.is_started:
            raise ValueError(f"Span状态为{self._status.value}，无法结束")
        
        self._status = SpanStatus.ENDED
        self._end_time = time.time()
        duration = (self._end_time - self._start_time) * 1000 if self._start_time else 0
        self._record_event("end", {"duration_ms": duration})
    
    def record_error(self, error: Exception) -> None:
        """
        记录错误
        
        Args:
            error: 异常对象
        """
        self._errors.append(error)
        self._status = SpanStatus.ERROR
        self._record_event("error", {
            "error_type": type(error).__name__,
            "error_message": str(error)
        })
    
    def get_errors(self) -> List[Exception]:
        """获取错误列表"""
        return self._errors.copy()
    
    def get_duration_ms(self) -> Optional[float]:
        """
        获取执行时长（毫秒）
        
        Returns:
            执行时长，如果未结束返回None
        """
        if self._start_time is None or self._end_time is None:
            return None
        return (self._end_time - self._start_time) * 1000
    
    def get_events(self) -> List[SpanEvent]:
        """获取事件列表"""
        return self._events.copy()


class TelemetryManager:
    """
    追踪管理器
    
    提供追踪、指标、日志的可观测性功能。
    支持本地和远程追踪后端，用于服务调用的监控和分析。
    """
    
    def __init__(self, config: TraceConfig):
        """
        初始化追踪管理器
        
        Args:
            config: 追踪配置
        """
        self.config = config
        self._spans: Dict[str, Span] = {}
        self._metrics: Dict[str, List[MetricData]] = {}
    
    def is_enabled(self) -> bool:
        """
        检查追踪是否启用
        
        Returns:
            如果启用返回True，否则返回False
        """
        return self.config.enabled
    
    def create_span(
        self,
        name: str,
        service_context: ServiceContext,
        kind: SpanKind = SpanKind.INTERNAL
    ) -> Span:
        """
        创建Span
        
        Args:
            name: Span名称
            service_context: 服务上下文
            kind: Span类型
            
        Returns:
            Span实例
        """
        span = Span(name, service_context, kind)
        self._spans[span.trace_id] = span
        return span
    
    def record_counter(self, name: str, value: float, attributes: Dict[str, str] = None) -> None:
        """
        记录计数器指标
        
        Args:
            name: 指标名称
            value: 指标值
            attributes: 指标属性
        """
        if name not in self._metrics:
            self._metrics[name] = []
        
        metric_data = MetricData(
            name=name,
            value=value,
            timestamp=time.time(),
            labels=attributes or {}
        )
        self._metrics[name].append(metric_data)
    
    def record_histogram(self, name: str, value: float, attributes: Dict[str, str] = None) -> None:
        """
        记录直方图指标
        
        Args:
            name: 指标名称
            value: 指标值
            attributes: 指标属性
        """
        if name not in self._metrics:
            self._metrics[name] = []
        
        metric_data = MetricData(
            name=name,
            value=value,
            timestamp=time.time(),
            labels=attributes or {}
        )
        self._metrics[name].append(metric_data)
    
    def record_gauge(self, name: str, value: float, attributes: Dict[str, str] = None) -> None:
        """
        记录测量指标
        
        Args:
            name: 指标名称
            value: 指标值
            attributes: 指标属性
        """
        if name not in self._metrics:
            self._metrics[name] = []
        
        metric_data = MetricData(
            name=name,
            value=value,
            timestamp=time.time(),
            labels=attributes or {}
        )
        
        self._metrics[name] = [metric_data]  # 测量指标只保留最新值
    
    def get_metrics(self) -> Dict[str, List[MetricData]]:
        """
        获取所有指标
        
        Returns:
            指标字典
        """
        return self._metrics.copy()
    
    async def shutdown(self) -> None:
        """关闭追踪管理器"""
        self._spans.clear()
        self._metrics.clear()