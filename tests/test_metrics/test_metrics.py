"""
Metrics 模块测试
"""
import pytest
from modules.metrics import (
    MetricsModule,
    Counter,
    Gauge,
    Histogram,
    Summary
)


class TestCounter:
    """测试计数器"""

    def test_create_counter(self):
        """测试创建计数器"""
        counter = Counter("test_counter", "A test counter")
        
        assert counter.name == "test_counter"
        assert counter.value() == 0

    def test_inc(self):
        """测试增加"""
        counter = Counter("test_counter")
        
        counter.inc()
        counter.inc(5)
        
        assert counter.value() == 6

    def test_to_prometheus(self):
        """测试 Prometheus 格式输出"""
        counter = Counter("test_counter", "A test counter")
        counter.inc(10)
        
        output = counter.to_prometheus("test_counter")
        
        assert "# HELP test_counter" in output
        assert "# TYPE test_counter counter" in output
        assert "test_counter{} 10" in output


class TestGauge:
    """测试仪表"""

    def test_create_gauge(self):
        """测试创建仪表"""
        gauge = Gauge("test_gauge", "A test gauge")
        
        assert gauge.name == "test_gauge"
        assert gauge.value() == 0.0

    def test_set(self):
        """测试设置值"""
        gauge = Gauge("test_gauge")
        
        gauge.set(42.5)
        
        assert gauge.value() == 42.5

    def test_inc(self):
        """测试增加"""
        gauge = Gauge("test_gauge")
        
        gauge.inc(10)
        
        assert gauge.value() == 10.0

    def test_dec(self):
        """测试减少"""
        gauge = Gauge("test_gauge")
        
        gauge.set(10)
        gauge.dec(3)
        
        assert gauge.value() == 7.0


class TestHistogram:
    """测试直方图"""

    def test_create_histogram(self):
        """测试创建直方图"""
        histogram = Histogram("test_histogram", buckets=[0.1, 0.5, 1.0])
        
        assert histogram.name == "test_histogram"
        assert len(histogram.buckets) == 3

    def test_observe(self):
        """测试观测"""
        histogram = Histogram("test_histogram")
        
        histogram.observe(0.5)
        histogram.observe(1.0)
        
        assert histogram._count == 2
        assert histogram._sum == 1.5


class TestMetricsModule:
    """测试指标模块"""

    def test_create_module(self, metrics):
        """测试创建模块"""
        assert metrics is not None

    def test_counter(self, metrics):
        """测试计数器"""
        counter = metrics.counter("my_counter", "My counter")
        
        counter.inc()
        counter.inc(5)
        
        assert counter.value() == 6

    def test_gauge(self, metrics):
        """测试仪表"""
        gauge = metrics.gauge("my_gauge", "My gauge")
        
        gauge.set(100)
        
        assert gauge.value() == 100

    def test_histogram(self, metrics):
        """测试直方图"""
        histogram = metrics.histogram("my_histogram", buckets=[0.1, 0.5, 1.0])
        
        histogram.observe(0.3)
        
        assert histogram._count == 1

    def test_summary(self, metrics):
        """测试摘要"""
        summary = metrics.summary("my_summary", "My summary")
        
        summary.observe(1.5)
        
        assert summary._count == 1

    def test_inc_task(self, metrics):
        """测试任务计数"""
        metrics.inc_task(success=True)
        metrics.inc_task(success=True)
        metrics.inc_task(success=False)
        
        stats = metrics.get_stats()
        
        assert stats["counters"]["tasks_total"] == 3
        assert stats["counters"]["tasks_success"] == 2
        assert stats["counters"]["tasks_failed"] == 1

    def test_observe_task_duration(self, metrics):
        """测试任务时长记录"""
        metrics.observe_task_duration(1.5)
        metrics.observe_task_duration(2.0)
        
        stats = metrics.get_stats()
        
        assert stats["histograms"]["task_duration_seconds"]["count"] == 2
        assert stats["histograms"]["task_duration_seconds"]["sum"] == 3.5

    def test_set_active_schedules(self, metrics):
        """测试设置活跃调度数"""
        metrics.set_active_schedules(5)
        
        stats = metrics.get_stats()
        
        assert stats["gauges"]["schedules_active"] == 5

    def test_cache_stats(self, metrics):
        """测试缓存统计"""
        metrics.inc_cache_hit()
        metrics.inc_cache_hit()
        metrics.inc_cache_miss()
        
        stats = metrics.get_stats()
        
        assert stats["gauges"]["cache_hits"] == 2
        assert stats["gauges"]["cache_misses"] == 1

    def test_account_stats(self, metrics):
        """测试账号统计"""
        metrics.set_accounts_total(10)
        metrics.set_accounts_active(7)
        
        stats = metrics.get_stats()
        
        assert stats["gauges"]["accounts_total"] == 10
        assert stats["gauges"]["accounts_active"] == 7

    def test_get_metrics(self, metrics):
        """测试获取 Prometheus 格式指标"""
        metrics.inc_task(success=True)
        
        output = metrics.get_metrics()
        
        assert "# HELP tasks_total" in output
        assert "# TYPE tasks_total counter" in output

    def test_reset(self, metrics):
        """测试重置"""
        metrics.inc_task(success=True)
        metrics.reset()
        
        stats = metrics.get_stats()
        
        assert stats["counters"]["tasks_total"] == 0


class TestMetricsModuleKernelIntegration:
    """测试 MetricsModule 与 Kernel 集成"""

    def test_kernel_metrics_property(self, running_kernel):
        """测试 kernel.metrics 属性"""
        assert running_kernel.metrics is not None
        assert running_kernel.metrics.__class__.__name__ == "MetricsModule"

    def test_metrics_endpoint(self, running_kernel):
        """测试指标端点返回 Prometheus 格式"""
        running_kernel.metrics.inc_task(success=True)
        
        output = running_kernel.metrics.get_metrics()
        
        assert "tasks_total" in output
        assert "counter" in output
