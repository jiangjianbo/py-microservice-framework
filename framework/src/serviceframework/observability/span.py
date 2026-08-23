"""
追踪Span类

实现OpenTelemetry的Span抽象，支持追踪链、属性、事件等功能。
Span表示追踪中的一个工作单元，可以嵌套形成调用链。
"""

import uuid
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from serviceframework.observability.config import SpanKind
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
        self.service_context = service_context
        self.service_name = service_context.service_name
        self.method = service_context.method
        self.trace_id = service_context.request_id
        self._status = SpanStatus.CREATED
        
        self._attributes: Dict[str, Any] = {}
        self._events: List[SpanEvent] = []
        self._errors: List[Exception] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._child_spans: List["Span"] = []
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
    
    def has_attribute(self, key: str) -> bool:
        """
        检查属性是否存在
        
        Args:
            key: 属性键
            
        Returns:
            如果存在返回True，否则返回False
        """
        return key in self._attributes
    
    def get_attributes(self) -> Dict[str, Any]:
        """获取所有属性"""
        return self._attributes.copy()
    
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
            listener(event)
    
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
        self._child_spans.append(child_span)
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
        self._record_event("end", {
            "duration_ms": (self._end_time - self._start_time) * 1000
        })
    
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
    
    def get_trace_id(self) -> str:
        """获取追踪ID"""
        return self.trace_id