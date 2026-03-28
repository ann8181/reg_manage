"""
Scheduler Module - 任务调度模块
基于APScheduler的调度功能，注册到内核
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger


class SchedulerModule:
    """
    调度模块
    负责任务的时间调度执行
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.scheduler = BackgroundScheduler()
        self.schedules: Dict[str, Dict] = {}
        self._task_callbacks: Dict[str, Callable] = {}
        self.scheduler.start()
        self.logger = kernel.get_logger("scheduler")
        self.logger.info("SchedulerModule initialized")
    
    def register_task_callback(self, task_id: str, callback: Callable):
        """注册任务回调"""
        self._task_callbacks[task_id] = callback
    
    def add_schedule(
        self,
        name: str,
        task_id: str,
        schedule_type: str = "cron",
        cron_expr: str = "",
        interval_seconds: int = 0,
        batch_size: int = 1,
        batch_delay: int = 0,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        添加调度
        
        Args:
            name: 调度名称
            task_id: 任务ID
            schedule_type: 调度类型 (cron/interval/once/manual)
            cron_expr: Cron表达式
            interval_seconds: 间隔秒数
            batch_size: 批量大小
            batch_delay: 批量间隔
        
        Returns:
            schedule_id
        """
        schedule_id = str(uuid.uuid4())[:8]
        
        schedule = {
            "id": schedule_id,
            "name": name,
            "task_id": task_id,
            "type": schedule_type,
            "cron_expr": cron_expr,
            "interval_seconds": interval_seconds,
            "batch_size": batch_size,
            "batch_delay": batch_delay,
            "max_retries": max_retries,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "next_run": None,
            "run_count": 0,
            **kwargs
        }
        
        self.schedules[schedule_id] = schedule
        self._setup_job(schedule)
        
        self.logger.info(f"Schedule added: {name} ({schedule_id})")
        return schedule_id
    
    def _setup_job(self, schedule: Dict):
        """设置APScheduler job"""
        if not schedule.get("enabled", True):
            return
        
        task_id = schedule["task_id"]
        schedule_type = schedule["type"]
        
        if schedule_type == "cron" and schedule.get("cron_expr"):
            trigger = CronTrigger.from_crontab(schedule["cron_expr"])
        elif schedule_type == "interval" and schedule.get("interval_seconds", 0) > 0:
            trigger = IntervalTrigger(seconds=schedule["interval_seconds"])
        elif schedule_type == "once":
            trigger = DateTrigger(run_date=datetime.now() + timedelta(seconds=5))
        else:
            return
        
        job_id = schedule["id"]
        
        self.scheduler.add_job(
            func=self._execute_schedule,
            trigger=trigger,
            id=job_id,
            args=[schedule["id"]],
            replace_existing=True,
            misfire_grace_time=60
        )
        
        # 更新next_run
        job = self.scheduler.get_job(job_id)
        if job:
            schedule["next_run"] = str(job.next_run_time)
    
    def _execute_schedule(self, schedule_id: str):
        """执行调度"""
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return
        
        schedule["run_count"] += 1
        schedule["last_run"] = datetime.now().isoformat()
        
        callback = self._task_callbacks.get(schedule["task_id"])
        if not callback:
            # 通过kernel执行
            try:
                self.kernel.run_task(schedule["task_id"])
            except Exception as e:
                self.logger.error(f"Schedule {schedule_id} execution error: {e}")
                return
        
        # 批量执行
        batch_size = schedule.get("batch_size", 1)
        batch_delay = schedule.get("batch_delay", 0)
        
        for i in range(batch_size - 1):
            if batch_delay > 0:
                import time
                time.sleep(batch_delay)
            try:
                self.kernel.run_task(schedule["task_id"])
            except Exception as e:
                self.logger.error(f"Batch {i+1} error: {e}")
        
        self.logger.info(f"Schedule {schedule_id} executed")
    
    def pause(self, schedule_id: str):
        """暂停调度"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id]["enabled"] = False
            self.scheduler.pause_job(schedule_id)
            self.logger.info(f"Schedule paused: {schedule_id}")
    
    def resume(self, schedule_id: str):
        """恢复调度"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id]["enabled"] = True
            self.scheduler.resume_job(schedule_id)
            self.logger.info(f"Schedule resumed: {schedule_id}")
    
    def remove(self, schedule_id: str):
        """删除调度"""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            try:
                self.scheduler.remove_job(schedule_id)
            except Exception:
                pass
            self.logger.info(f"Schedule removed: {schedule_id}")
    
    def run_now(self, schedule_id: str):
        """立即执行"""
        schedule = self.schedules.get(schedule_id)
        if schedule:
            self._execute_schedule(schedule_id)
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict]:
        return self.schedules.get(schedule_id)
    
    def list_schedules(self) -> List[Dict]:
        return list(self.schedules.values())
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        self.logger.info("SchedulerModule stopped")
