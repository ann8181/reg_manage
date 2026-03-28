"""
Scheduler 调度控制测试
"""
import pytest


class TestSchedulerControl:
    """测试调度控制"""

    def test_pause_schedule(self, scheduler):
        """测试暂停调度"""
        schedule_id = scheduler.add_schedule(
            name="pause_test",
            task_id="test_task",
            schedule_type="once"
        )
        
        scheduler.pause(schedule_id)
        
        assert scheduler.get_schedule(schedule_id)["enabled"] is False

    def test_resume_schedule(self, scheduler):
        """测试恢复调度"""
        schedule_id = scheduler.add_schedule(
            name="resume_test",
            task_id="test_task",
            schedule_type="once"
        )
        
        scheduler.pause(schedule_id)
        scheduler.resume(schedule_id)
        
        assert scheduler.get_schedule(schedule_id)["enabled"] is True

    def test_remove_schedule(self, scheduler):
        """测试删除调度"""
        schedule_id = scheduler.add_schedule(
            name="remove_test",
            task_id="test_task",
            schedule_type="once"
        )
        
        scheduler.remove(schedule_id)
        
        assert scheduler.get_schedule(schedule_id) is None

    def test_remove_nonexistent_schedule(self, scheduler):
        """测试删除不存在的调度"""
        scheduler.remove("nonexistent")


class TestSchedulerExecution:
    """测试调度执行"""

    def test_run_now(self, scheduler, kernel, mocker):
        """测试立即执行调度"""
        schedule_id = scheduler.add_schedule(
            name="run_now_test",
            task_id="test_task",
            schedule_type="once"
        )
        
        mock_run_task = mocker.patch.object(kernel, 'run_task', return_value={"success": True})
        scheduler.run_now(schedule_id)
        
        mock_run_task.assert_called_once_with("test_task")

    def test_run_now_noop_for_missing_schedule(self, scheduler, kernel, mocker):
        """测试对不存在的调度立即执行无效果"""
        mock_run_task = mocker.patch.object(kernel, 'run_task')
        scheduler.run_now("nonexistent")
        
        mock_run_task.assert_not_called()


class TestSchedulerCallbacks:
    """测试任务回调"""

    def test_register_task_callback(self, scheduler):
        """测试注册任务回调"""
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        scheduler.register_task_callback("test_task", callback)
        
        assert scheduler._task_callbacks["test_task"] is callback

    def test_callback_override(self, scheduler):
        """测试回调覆盖"""
        def callback1():
            pass
        
        def callback2():
            pass
        
        scheduler.register_task_callback("task", callback1)
        scheduler.register_task_callback("task", callback2)
        
        assert scheduler._task_callbacks["task"] is callback2


class TestSchedulerStop:
    """测试调度器停止"""

    def test_stop_scheduler(self, scheduler):
        """测试停止调度器"""
        scheduler.stop()
        
        assert scheduler.scheduler.running is False
