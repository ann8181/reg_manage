"""
Manager - 统一管理系统
整合所有管理功能模块
"""

from .scheduler import Scheduler, TaskSchedule, ScheduleType
from .browser import BrowserManager, BrowserConfig, BrowserType
from .workflow import WorkflowEngine, Workflow, WorkflowStep, StepType
from .user import UserManager, User, UserRole
from .account import AccountManager, Account
from .module import ModuleManager, Module, ModuleVersion

__all__ = [
    # Scheduler
    "Scheduler",
    "TaskSchedule", 
    "ScheduleType",
    # Browser
    "BrowserManager",
    "BrowserConfig",
    "BrowserType",
    # Workflow
    "WorkflowEngine",
    "Workflow",
    "WorkflowStep",
    "StepType",
    # User
    "UserManager",
    "User",
    "UserRole",
    # Account
    "AccountManager",
    "Account",
    # Module
    "ModuleManager",
    "Module",
    "ModuleVersion",
]
