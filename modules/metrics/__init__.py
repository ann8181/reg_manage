"""
Metrics Module - 指标监控模块
提供 Prometheus 格式的指标暴露
"""

import time
import threading
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Counter:
    """计数器"""
    name: str
    description: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    _value: int = 0
    _lock: threading.RLock = field(default_factory=threading.RLock)
    
    def inc(self, amount: int = 1, **labels):
        with self._lock:
            self._value += amount
    
    def value(self) -> int:
        return self._value
    
    def to_prometheus(self, name: str) -> str:
        help_text = f"# HELP {name} {self.description}" if self.description else f"# HELP {name}"
        type_text = f"# TYPE {name} counter"
        metric_text = f"{name}{{}} {self._value}"
        return f"{help_text}\n{type_text}\n{metric_text}\n"


@dataclass
class Gauge:
    """仪表值"""
    name: str
    description: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    _value: float = 0.0
    _lock: threading.RLock = field(default_factory=threading.RLock)
    
    def set(self, value: float, **labels):
        with self._lock:
            self._value = value
    
    def inc(self, amount: float = 1.0, **labels):
        with self._lock:
            self._value += amount
    
    def dec(self, amount: float = 1.0, **labels):
        with self._lock:
            self._value -= amount
    
    def value(self) -> float:
        return self._value
    
    def to_prometheus(self, name: str) -> str:
        help_text = f"# HELP {name} {self.description}" if self.description else f"# HELP {name}"
        type_text = f"# TYPE {name} gauge"
        metric_text = f"{name}{{}} {self._value}"
        return f"{help_text}\n{type_text}\n{metric_text}\n"


@dataclass
class Histogram:
    """直方图"""
    name: str
    description: str = ""
    buckets: List[float] = field(default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
    _values: List[float] = field(default_factory=list)
    _sum: float = 0.0
    _count: int = 0
    _lock: threading.RLock = field(default_factory=threading.RLock)
    
    def observe(self, value: float, **labels):
        with self._lock:
            self._values.append(value)
            self._sum += value
            self._count += 1
    
    def to_prometheus(self, name: str) -> str:
        help_text = f"# HELP {name} {self.description}" if self.description else f"# HELP {name}"
        type_text = f"# TYPE {name} histogram"
        
        lines = [help_text, type_text]
        
        sorted_values = sorted(self._values)
        total = len(sorted_values)
        
        cumulative = 0
        for bucket in self.buckets:
            cumulative = sum(1 for v in sorted_values if v <= bucket)
            lines.append(f'{name}_bucket{{le="{bucket}"}} {cumulative}')
        lines.append(f'{name}_bucket{{le="+Inf"}} {total}')
        lines.append(f"{name}_sum {self._sum}")
        lines.append(f"{name}_count {self._count}")
        
        return "\n".join(lines)


@dataclass
class Summary:
    """摘要"""
    name: str
    description: str = ""
    _values: List[float] = field(default_factory=list)
    _sum: float = 0.0
    _count: int = 0
    _lock: threading.RLock = field(default_factory=threading.RLock)
    
    def observe(self, value: float, **labels):
        with self._lock:
            self._values.append(value)
            self._sum += value
            self._count += 1
    
    def to_prometheus(self, name: str) -> str:
        help_text = f"# HELP {name} {self.description}" if self.description else f"# HELP {name}"
        type_text = f"# TYPE {name} summary"
        
        lines = [help_text, type_text]
        
        sorted_values = sorted(self._values)
        quantiles = [0.5, 0.9, 0.95, 0.99]
        for q in quantiles:
            idx = int(len(sorted_values) * q)
            if idx >= len(sorted_values):
                idx = len(sorted_values) - 1
            lines.append(f'{name}{{quantile="{q}"}} {sorted_values[idx] if sorted_values else 0}')
        
        lines.append(f"{name}_sum {self._sum}")
        lines.append(f"{name}_count {self._count}")
        
        return "\n".join(lines)


class MetricsModule:
    """
    指标监控模块
    提供 Prometheus 格式的指标暴露
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}
        self._lock = threading.RLock()
        self._logger = kernel.get_logger("metrics")
        
        self._init_default_metrics()
        self._logger.info("MetricsModule initialized")
    
    def _init_default_metrics(self):
        """初始化默认指标"""
        self.counter("tasks_total", "Total number of tasks executed", {"type": "all"})
        self.counter("tasks_success", "Number of successful tasks", {"type": "success"})
        self.counter("tasks_failed", "Number of failed tasks", {"type": "failed"})
        self.gauge("schedules_active", "Number of active schedules")
        self.histogram("task_duration_seconds", "Task execution duration in seconds", buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0])
        self.histogram("schedule_delay_seconds", "Schedule execution delay in seconds", buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0])
        self.gauge("workflows_active", "Number of active workflows")
        self.counter("workflows_total", "Total number of workflows executed")
        self.gauge("cache_hits", "Cache hit count")
        self.gauge("cache_misses", "Cache miss count")
        self.gauge("accounts_total", "Total number of accounts")
        self.gauge("accounts_active", "Number of active accounts")
    
    def counter(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Counter:
        """创建或获取计数器"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description, labels or {})
            return self._counters[name]
    
    def gauge(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Gauge:
        """创建或获取仪表"""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description, labels or {})
            return self._gauges[name]
    
    def histogram(self, name: str, description: str = "", buckets: List[float] = None) -> Histogram:
        """创建或获取直方图"""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
            return self._histograms[name]
    
    def summary(self, name: str, description: str = "") -> Summary:
        """创建或获取摘要"""
        with self._lock:
            if name not in self._summaries:
                self._summaries[name] = Summary(name, description)
            return self._summaries[name]
    
    def inc_task(self, success: bool = True):
        """增加任务计数"""
        self.counter("tasks_total").inc()
        if success:
            self.counter("tasks_success").inc()
        else:
            self.counter("tasks_failed").inc()
    
    def observe_task_duration(self, duration: float):
        """记录任务执行时长"""
        self.histogram("task_duration_seconds").observe(duration)
    
    def set_active_schedules(self, count: int):
        """设置活跃调度数"""
        self.gauge("schedules_active").set(count)
    
    def observe_schedule_delay(self, delay: float):
        """记录调度延迟"""
        self.histogram("schedule_delay_seconds").observe(delay)
    
    def inc_cache_hit(self):
        """增加缓存命中"""
        self.gauge("cache_hits").inc()
    
    def inc_cache_miss(self):
        """增加缓存未命中"""
        self.gauge("cache_misses").inc()
    
    def set_accounts_total(self, count: int):
        """设置账号总数"""
        self.gauge("accounts_total").set(count)
    
    def set_accounts_active(self, count: int):
        """设置活跃账号数"""
        self.gauge("accounts_active").set(count)
    
    def set_workflows_active(self, count: int):
        """设置活跃工作流数"""
        self.gauge("workflows_active").set(count)
    
    def inc_workflow(self):
        """增加工作流计数"""
        self.counter("workflows_total").inc()
    
    def get_metrics(self) -> str:
        """获取 Prometheus 格式的指标"""
        lines = []
        
        with self._lock:
            for name, counter in self._counters.items():
                lines.append(counter.to_prometheus(name))
            
            for name, gauge in self._gauges.items():
                lines.append(gauge.to_prometheus(name))
            
            for name, histogram in self._histograms.items():
                lines.append(histogram.to_prometheus(name))
            
            for name, summary in self._summaries.items():
                lines.append(summary.to_prometheus(name))
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "counters": {name: c.value() for name, c in self._counters.items()},
                "gauges": {name: g.value() for name, g in self._gauges.items()},
                "histograms": {name: {"count": h._count, "sum": h._sum} for name, h in self._histograms.items()},
                "summaries": {name: {"count": s._count, "sum": s._sum} for name, s in self._summaries.items()}
            }
    
    def reset(self):
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._summaries.clear()
            self._init_default_metrics()
    
    def stop(self):
        """停止模块"""
        self._logger.info("MetricsModule stopped")
