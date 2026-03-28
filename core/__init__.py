"""
Core Module - 核心基础模块
提供任务配置、异步执行器、服务提供商等基础组件
"""

from .base import TaskConfig, TaskResult
from .config import Settings
from .task_manager import TaskManager
from .async_executor import AsyncTaskExecutor
from .providers.factory import ProviderFactory
from .providers.chain import ProviderChain

__all__ = [
    "TaskConfig",
    "TaskResult",
    "Settings",
    "TaskManager",
    "AsyncTaskExecutor",
    "ProviderFactory",
    "ProviderChain",
]
