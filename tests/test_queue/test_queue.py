"""
Queue 模块测试
"""
import pytest
from modules.queue import (
    QueueModule,
    MemoryQueue,
    Job,
    JobStatus
)


class TestMemoryQueue:
    """测试内存队列"""

    def test_enqueue(self):
        """测试入队"""
        queue = MemoryQueue()
        job = Job(id="1", queue_name="default", func_name="test")
        
        result = queue.enqueue(job)
        
        assert result is True
        assert queue.length("default") == 1

    def test_dequeue(self):
        """测试出队"""
        queue = MemoryQueue()
        job = Job(id="1", queue_name="default", func_name="test")
        queue.enqueue(job)
        
        dequeued = queue.dequeue(timeout=0)
        
        assert dequeued is not None
        assert dequeued.id == "1"

    def test_dequeue_empty(self):
        """测试空队列出队"""
        queue = MemoryQueue()
        
        dequeued = queue.dequeue(timeout=0)
        
        assert dequeued is None

    def test_ack(self):
        """测试确认"""
        queue = MemoryQueue()
        job = Job(id="1", queue_name="default", func_name="test")
        queue.enqueue(job)
        job = queue.dequeue(timeout=0)
        
        result = queue.ack(job.id)
        
        assert result is True
        assert queue.length("default") == 0

    def test_nack_retry(self):
        """测试拒绝后重试"""
        queue = MemoryQueue()
        job = Job(id="1", queue_name="default", func_name="test", max_retries=3)
        queue.enqueue(job)
        job = queue.dequeue(timeout=0)
        
        queue.nack(job.id)
        
        assert queue.length("default") == 1

    def test_priority(self):
        """测试优先级"""
        queue = MemoryQueue()
        job1 = Job(id="1", queue_name="default", func_name="test", priority=1)
        job2 = Job(id="2", queue_name="default", func_name="test", priority=10)
        queue.enqueue(job1)
        queue.enqueue(job2)
        
        dequeued = queue.dequeue(timeout=0)
        
        assert dequeued.priority == 10

    def test_length(self):
        """测试队列长度"""
        queue = MemoryQueue()
        
        assert queue.length("default") == 0
        
        queue.enqueue(Job(id="1", queue_name="default", func_name="test"))
        queue.enqueue(Job(id="2", queue_name="default", func_name="test"))
        
        assert queue.length("default") == 2

    def test_clear(self):
        """测试清空队列"""
        queue = MemoryQueue()
        queue.enqueue(Job(id="1", queue_name="default", func_name="test"))
        queue.enqueue(Job(id="2", queue_name="default", func_name="test"))
        
        queue.clear("default")
        
        assert queue.length("default") == 0


class TestQueueModule:
    """测试队列模块"""

    def test_create_module(self, queue):
        """测试创建模块"""
        assert queue is not None
        assert queue.backend is not None

    def test_register_function(self, queue):
        """测试注册函数"""
        def my_func(x):
            return x * 2
        
        queue.register_function("double", my_func)
        
        assert "double" in queue._functions

    def test_enqueue(self, queue):
        """测试入队"""
        def my_func():
            pass
        
        queue.register_function("test", my_func)
        job_id = queue.enqueue("test")
        
        assert job_id is not None
        assert queue.length("default") == 1

    def test_enqueue_with_priority(self, queue):
        """测试带优先级入队"""
        def my_func():
            pass
        
        queue.register_function("test", my_func)
        queue.enqueue("test", priority=1)
        queue.enqueue("test", priority=10)
        
        job = queue.dequeue(timeout=0)
        
        assert job.priority == 10

    def test_dequeue(self, queue):
        """测试出队"""
        def my_func():
            return "result"
        
        queue.register_function("test", my_func)
        queue.enqueue("test")
        
        job = queue.dequeue(timeout=0)
        
        assert job is not None
        assert queue.backend._jobs[job.id].status == JobStatus.RUNNING.value

    def test_execute_job(self, queue):
        """测试执行任务"""
        def add(a, b):
            return a + b
        
        queue.register_function("add", add)
        job_id = queue.enqueue("add", 2, 3)
        job = queue.dequeue(timeout=0)
        
        result = queue.execute_job(job)
        
        assert result == 5
        assert queue.get_job(job_id).status == JobStatus.COMPLETED.value

    def test_execute_job_failure(self, queue):
        """测试任务执行失败"""
        def fail_func():
            raise ValueError("Test error")
        
        queue.register_function("fail", fail_func)
        queue.enqueue("fail")
        job = queue.dequeue(timeout=0)
        
        with pytest.raises(ValueError):
            queue.execute_job(job)
        
        assert queue.get_job(job.id).status == JobStatus.FAILED.value

    def test_cancel_job(self, queue):
        """测试取消任务"""
        def my_func():
            pass
        
        queue.register_function("test", my_func)
        job_id = queue.enqueue("test")
        
        result = queue.cancel_job(job_id)
        
        assert result is True
        assert queue.get_job(job_id).status == JobStatus.CANCELLED.value

    def test_get_stats(self, queue):
        """测试获取统计"""
        def my_func():
            pass
        
        queue.register_function("test", my_func)
        queue.enqueue("test")
        queue.enqueue("test")
        
        stats = queue.get_stats()
        
        assert stats["registered_functions"] == 1
        assert stats["pending_default"] == 2


class TestQueueModuleKernelIntegration:
    """测试 QueueModule 与 Kernel 集成"""

    def test_kernel_queue_property(self, running_kernel):
        """测试 kernel.queue 属性"""
        assert running_kernel.queue is not None
        assert running_kernel.queue.__class__.__name__ == "QueueModule"
