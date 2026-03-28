"""
Kernel 任务管理测试
"""
import pytest


class DummyTask:
    """测试用任务类"""
    def __init__(self, kernel, **kwargs):
        self.kernel = kernel
        self.params = kwargs
    
    def execute(self):
        return {"success": True, "data": self.params.get("test_data", "default")}


class FailingTask:
    """测试用失败任务类"""
    def __init__(self, kernel, **kwargs):
        self.kernel = kernel
    
    def execute(self):
        raise ValueError("Task failed intentionally")


class TestKernelTaskRegistration:
    """测试任务注册"""

    def test_register_task(self, running_kernel):
        """测试注册任务"""
        running_kernel.register_task("dummy", DummyTask)
        assert running_kernel.get_task("dummy") is DummyTask

    def test_register_duplicate_task(self, running_kernel):
        """测试重复注册任务（覆盖）"""
        running_kernel.register_task("dup", DummyTask)
        running_kernel.register_task("dup", FailingTask)
        assert running_kernel.get_task("dup") is FailingTask

    def test_list_tasks_empty(self, kernel):
        """测试空任务列表"""
        kernel.start()
        assert len(kernel.list_tasks()) == 0
        kernel.stop()

    def test_list_tasks_with_tasks(self, running_kernel):
        """测试有任务时的列表"""
        running_kernel.register_task("task1", DummyTask)
        running_kernel.register_task("task2", DummyTask)
        
        tasks = running_kernel.list_tasks()
        assert "task1" in tasks
        assert "task2" in tasks


class TestKernelTaskExecution:
    """测试任务执行"""

    def test_run_task_success(self, running_kernel):
        """测试任务执行成功"""
        running_kernel.register_task("success", DummyTask)
        
        result = running_kernel.run_task("success", {"test_data": "test_value"})
        
        assert result["success"] is True
        assert result["data"] == "test_value"

    def test_run_task_not_found(self, running_kernel):
        """测试任务不存在"""
        with pytest.raises(ValueError, match="Task not found"):
            running_kernel.run_task("nonexistent")

    def test_run_task_with_error(self, running_kernel):
        """测试任务执行出错"""
        running_kernel.register_task("fail", FailingTask)
        
        with pytest.raises(ValueError, match="Task failed"):
            running_kernel.run_task("fail")

    def test_run_task_without_params(self, running_kernel):
        """测试不带参数执行任务"""
        running_kernel.register_task("no_params", DummyTask)
        
        result = running_kernel.run_task("no_params")
        
        assert result["success"] is True
        assert result["data"] == "default"


class TestKernelBatchExecution:
    """测试批量任务执行"""

    def test_run_tasks_batch(self, running_kernel):
        """测试批量运行任务"""
        running_kernel.register_task("batch1", DummyTask)
        running_kernel.register_task("batch2", DummyTask)
        
        results = running_kernel.run_tasks(["batch1", "batch2"], {"test_data": "batch"})
        
        assert len(results) == 2
        assert all(r["success"] for r in results)

    def test_run_tasks_with_one_failing(self, running_kernel):
        """测试批量中有一个失败"""
        running_kernel.register_task("ok", DummyTask)
        running_kernel.register_task("bad", FailingTask)
        
        results = running_kernel.run_tasks(["ok", "bad"])
        
        assert len(results) == 2
        assert results[0]["success"] is True
        assert "error" in results[1]
