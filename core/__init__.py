"""
Auto Register Tasks - Core Module

统一的任务执行框架，整合以下功能：
- Persona System: 身份、代理、账号管理
- Provider System: 14+ 临时邮箱服务
- Browser Task: 浏览器自动化任务
- Logger System: 结构化日志和截图追踪
"""

from .base import BaseTask, TaskConfig, TaskResult, TaskStatus
from .browser_task import BrowserTask, EmailProviderTask
from .task_manager import TaskManager
from .executor import TaskExecutor

__all__ = [
    "BaseTask",
    "TaskConfig",
    "TaskResult", 
    "TaskStatus",
    "BrowserTask",
    "EmailProviderTask",
    "TaskManager",
    "TaskExecutor",
]
