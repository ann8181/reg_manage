"""
Trigger - 触发器定义
"""
from apscheduler.triggers.cron import CronTrigger as APSchedulerCronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from typing import Optional


class Trigger:
    """触发器基类"""
    def get_aps_trigger(self):
        raise NotImplementedError


class CronTrigger(Trigger):
    def __init__(self, expression: str):
        self.expression = expression
    
    def get_aps_trigger(self):
        return APSchedulerCronTrigger.from_crontab(self.expression)


class IntervalTrigger(Trigger):
    def __init__(self, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0):
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        self.days = days
    
    def get_aps_trigger(self):
        return IntervalTrigger(
            seconds=self.seconds,
            minutes=self.minutes,
            hours=self.hours,
            days=self.days
        )


class DateTrigger(Trigger):
    def __init__(self, run_date: datetime = None, after_seconds: int = 0):
        if after_seconds > 0:
            self.run_date = datetime.now() + timedelta(seconds=after_seconds)
        else:
            self.run_date = run_date or datetime.now()
    
    def get_aps_trigger(self):
        return DateTrigger(run_date=self.run_date)
