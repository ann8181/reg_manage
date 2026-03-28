"""
Scheduler - 统一任务调度器
支持定时、间隔、Cron表达式、批量调度
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger as APSchedulerCronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    ONCE = "once"           # 单次执行
    CRON = "cron"           # Cron表达式
    INTERVAL = "interval"   # 间隔执行
    MANUAL = "manual"        # 手动触发


@dataclass
class TaskSchedule:
    id: str
    name: str
    task_id: str
    schedule_type: ScheduleType
    enabled: bool = True
    
    # Cron配置
    cron_expr: str = ""           # "*/5 * * * *"
    
    # 间隔配置
    interval_seconds: int = 0
    
    # 批量配置
    batch_size: int = 1
    batch_delay: int = 0
    
    # 执行配置
    max_retries: int = 3
    retry_delay: int = 60
    timeout: int = 300
    
    # 元数据
    created_at: str = ""
    updated_at: str = ""
    last_run: str = ""
    next_run: str = ""
    run_count: int = 0
    description: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class Scheduler:
    """
    统一任务调度器
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.scheduler = BackgroundScheduler()
        self.jobs: Dict[str, Dict] = {}
        self.schedules: Dict[str, TaskSchedule] = {}
        self._task_callbacks: Dict[str, Callable] = {}
        self._running_tasks: Dict[str, bool] = {}
        
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def add_task_callback(self, task_id: str, callback: Callable):
        """注册任务回调函数"""
        self._task_callbacks[task_id] = callback
    
    def create_schedule(
        self,
        name: str,
        task_id: str,
        schedule_type: ScheduleType,
        cron_expr: str = "",
        interval_seconds: int = 0,
        batch_size: int = 1,
        **kwargs
    ) -> TaskSchedule:
        """创建调度计划"""
        schedule = TaskSchedule(
            id=str(uuid.uuid4())[:8],
            name=name,
            task_id=task_id,
            schedule_type=schedule_type,
            cron_expr=cron_expr,
            interval_seconds=interval_seconds,
            batch_size=batch_size,
            **kwargs
        )
        
        self.schedules[schedule.id] = schedule
        self._setup_job(schedule)
        
        logger.info(f"Created schedule: {schedule.id} for task {task_id}")
        return schedule
    
    def _setup_job(self, schedule: TaskSchedule):
        """设置APScheduler job"""
        if schedule.schedule_type == ScheduleType.CRON and schedule.cron_expr:
            trigger = APSchedulerCronTrigger.from_crontab(schedule.cron_expr)
        elif schedule.schedule_type == ScheduleType.INTERVAL:
            trigger = IntervalTrigger(seconds=schedule.interval_seconds)
        elif schedule.schedule_type == ScheduleType.ONCE:
            trigger = DateTrigger(run_date=datetime.now() + timedelta(seconds=5))
        else:
            return
        
        job_id = f"{schedule.id}"
        
        self.scheduler.add_job(
            func=self._execute_schedule,
            trigger=trigger,
            id=job_id,
            args=[schedule.id],
            replace_existing=True,
            misfire_grace_time=60
        )
        
        schedule.next_run = str(self.scheduler.get_job(job_id).next_run_time)
    
    def _execute_schedule(self, schedule_id: str):
        """执行调度任务"""
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return
        
        self._running_tasks[schedule_id] = True
        schedule.run_count += 1
        schedule.last_run = datetime.now().isoformat()
        
        try:
            callback = self._task_callbacks.get(schedule.task_id)
            if callback:
                for i in range(schedule.batch_size):
                    if not self._running_tasks.get(schedule_id):
                        break
                    
                    callback(schedule.task_id)
                    
                    if schedule.batch_delay > 0 and i < schedule.batch_size - 1:
                        import time
                        time.sleep(schedule.batch_delay)
            
            logger.info(f"Schedule {schedule_id} executed successfully")
        except Exception as e:
            logger.error(f"Schedule {schedule_id} execution failed: {e}")
        finally:
            self._running_tasks[schedule_id] = False
    
    def pause_schedule(self, schedule_id: str):
        """暂停调度"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].enabled = False
            self.scheduler.pause_job(schedule_id)
    
    def resume_schedule(self, schedule_id: str):
        """恢复调度"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].enabled = True
            self.scheduler.resume_job(schedule_id)
    
    def remove_schedule(self, schedule_id: str):
        """删除调度"""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            self.scheduler.remove_job(schedule_id)
    
    def run_now(self, schedule_id: str):
        """立即执行"""
        schedule = self.schedules.get(schedule_id)
        if schedule:
            self._execute_schedule(schedule_id)
    
    def get_schedule(self, schedule_id: str) -> Optional[TaskSchedule]:
        return self.schedules.get(schedule_id)
    
    def list_schedules(self, task_id: str = None) -> List[TaskSchedule]:
        if task_id:
            return [s for s in self.schedules.values() if s.task_id == task_id]
        return list(self.schedules.values())
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_schedules": len(self.schedules),
            "enabled": sum(1 for s in self.schedules.values() if s.enabled),
            "running_tasks": sum(1 for v in self._running_tasks.values() if v),
            "jobs": len(self.scheduler.get_jobs())
        }


def get_scheduler() -> Scheduler:
    return Scheduler()
