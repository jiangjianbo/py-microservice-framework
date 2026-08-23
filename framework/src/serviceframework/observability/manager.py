"""
追踪管理器模块

实现OpenTelemetry追踪功能，管理Span的创建和导出。
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from serviceframework.observability.config import TraceConfig
from serviceframework.observability.span import Span, SpanStatus


@dataclass
class MetricData:
    """指标数据"""
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metric:
    """指标"""
    name: str
    data: List[MetricData] = field(default_factory=list)


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
        self._active_spans: Dict[str, Span] = {}
        self._metrics: Dict[str, Metric] = {}
        self._logger = self._create_logger()
    
    def _create_logger(self):
        """创建日志记录器"""
        import logging
        logger = logging.getLogger("serviceframework.observability")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        return logger
    
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
        service_context,
        kind=None
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
        if kind is None:
            kind = SpanKind.INTERNAL
        
        span = Span(name, service_context, kind)
        
        self._active_spans[span.trace_id] = span
        
        self._logger.info(f"创建Span: {name}, trace_id: {span.trace_id}")
        
        return span
    
    def get_active_span(self, trace_id: str) -> Optional[Span]:
        """
        获取活跃的Span
        
        Args:
            trace_id: 追踪ID
            
        Returns:
            Span实例，如果不存在返回None
        """
        return self._active_spans.get(trace_id)
    
    def record_counter(self, name: str, value: float, attributes: Dict[str, str] = None) -> None:
        """
        记录计数器指标
        
        Args:
            name: 指标名称
            value: 指标值
            attributes: 指标属性
        """
        if name not in self._metrics:
            self._metrics[name] = Metric(name=name)
        
        metric_data = MetricData(
            name=name,
            value=value,
            timestamp=self._get_current_timestamp(),
            labels=attributes or {}
        )
        
        self._metrics[name].data.append(metric_data)
        
        self._logger.info(f"记录计数器: {name}={value}")
    
    def record_histogram(self, name: str, value: float, attributes: Dict[str, str] = None) -> None:
        """
        记录直方图指标
        
        Args:
            name: 指标名称
            value: 指标值
            attributes: 指标属性
        """
        if name not in self._metrics:
            self._metrics[name] = Metric(name=name)
        
        metric_data = MetricData(
            name=name,
            value=value,
            timestamp=self._get_current_timestamp(),
            labels=attributes or {}
        )
        
        self._metrics[name].data.append(metric_data)
        
        self._logger.info(f"记录直方图: {name}={value}")
    
    def record_gauge(self, name: str, value: float, attributes: Dict[str, str] = None) -> None:
        """
        记录测量指标
        
        Args:
            name: 指标名称
            value: 指标值
            attributes: 指标属性
        """
        if name not in self._metrics:
            self._metrics[name] = Metric(name=name)
        
        metric_data = MetricData(
            name=name,
            value=value,
            timestamp=self._get_current_timestamp(),
            labels=attributes or {}
        )
        
        self._metrics[name].data.append(metric_data)
        
        self._metrics[name].data = self._metrics[name].data[:-1]  # 只保留最新值
        
        self._logger.info(f"记录测量指标: {name}={value}")
    
    def get_metrics(self) -> Dict[str, Metric]:
        """
        获取所有指标
        
        Returns:
            指标字典
        """
        return self._metrics.copy()
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """
        获取指定指标
        
        Args:
            name: 指标名称
            
        Returns:
            指标对象，如果不存在返回None
        """
        return self._metrics.get(name)
    
    def _get_current_timestamp(self) -> float:
        """获取当前时间戳"""
        import time
        return time.time()
    
    async def export_spans(self) -> bool:
        """
        导出所有Span到追踪后端
        
        Returns:
            如果成功返回True，否则返回False
        """
        if not self.config.enabled:
            return False
        
        # TODO: 实现实际的导出逻辑
        # 这里需要根据endpoint类型选择不同的导出方式
        self._logger.info(f"导出{len(self._active_spans)}个Span到{self.config.endpoint}")
        
        return True
    
    async def export_metrics(self) -> bool:
        """
        导出所有指标到指标后端
        
        Returns:
            如果成功返回True，否则返回False
        """
        if not self.config.enabled:
            return False
        
        # TODO: 实现实际的导出逻辑
        self._logger.info(f"导出{len(self._metrics)}个指标")
        
        return True
    
    def clear_spans(self) -> None:
        """清空所有活跃的Span"""
        self._active_spans.clear()
    
    def clear_metrics(self) -> None:
        """清空所有指标"""
        self._metrics.clear()
    
    def get_span_count(self) -> int:
        """
        获取活跃Span数量
        
        Returns:
            Span数量
        """
        return len(self._active_spans)