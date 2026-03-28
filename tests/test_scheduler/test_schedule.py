"""
Scheduler 调度添加测试
"""
import pytest


class TestSchedulerAddSchedule:
    """测试添加调度"""

    def test_add_schedule_cron(self, scheduler):
        """测试添加 Cron 调度"""
        schedule_id = scheduler.add_schedule(
            name="daily_task",
            task_id="test_task",
            schedule_type="cron",
            cron_expr="0 2 * * *"
        )
        
        assert schedule_id is not None
        assert schedule_id in scheduler.schedules
        
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule["name"] == "daily_task"
        assert schedule["task_id"] == "test_task"
        assert schedule["cron_expr"] == "0 2 * * *"
        assert schedule["enabled"] is True

    def test_add_schedule_interval(self, scheduler):
        """测试添加 Interval 调度"""
        schedule_id = scheduler.add_schedule(
            name="interval_task",
            task_id="test_task",
            schedule_type="interval",
            interval_seconds=3600
        )
        
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule["interval_seconds"] == 3600
        assert schedule["type"] == "interval"

    def test_add_schedule_once(self, scheduler):
        """测试添加一次性调度"""
        schedule_id = scheduler.add_schedule(
            name="once_task",
            task_id="test_task",
            schedule_type="once"
        )
        
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule["type"] == "once"

    def test_add_schedule_with_batch(self, scheduler):
        """测试添加带批量的调度"""
        schedule_id = scheduler.add_schedule(
            name="batch_task",
            task_id="test_task",
            schedule_type="interval",
            interval_seconds=60,
            batch_size=5,
            batch_delay=10
        )
        
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule["batch_size"] == 5
        assert schedule["batch_delay"] == 10

    def test_add_schedule_with_max_retries(self, scheduler):
        """测试添加带重试的调度"""
        schedule_id = scheduler.add_schedule(
            name="retry_task",
            task_id="test_task",
            schedule_type="once",
            max_retries=5
        )
        
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule["max_retries"] == 5


class TestSchedulerList:
    """测试调度列表"""

    def test_list_schedules_empty(self, scheduler):
        """测试空调度列表"""
        schedules = scheduler.list_schedules()
        assert isinstance(schedules, list)

    def test_list_schedules_with_items(self, scheduler):
        """测试有调度时的列表"""
        scheduler.add_schedule(name="task1", task_id="t1", schedule_type="once")
        scheduler.add_schedule(name="task2", task_id="t2", schedule_type="once")
        
        schedules = scheduler.list_schedules()
        assert len(schedules) >= 2

    def test_get_schedule_exists(self, scheduler):
        """测试获取存在的调度"""
        schedule_id = scheduler.add_schedule(
            name="get_test",
            task_id="test",
            schedule_type="once"
        )
        
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule is not None
        assert schedule["name"] == "get_test"

    def test_get_schedule_not_found(self, scheduler):
        """测试获取不存在的调度"""
        schedule = scheduler.get_schedule("nonexistent")
        assert schedule is None
