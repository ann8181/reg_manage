"""
Base Module - 基础数据模型
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResult:
    """任务执行结果"""
    
    def __init__(
        self,
        task_id: str,
        status: TaskStatus = TaskStatus.PENDING,
        message: str = "",
        error: str = "",
        data: Dict = None,
        **kwargs
    ):
        self.task_id = task_id
        self.status = status
        self.message = message
        self.error = error
        self.data = data or {}
        self.metadata = kwargs
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "message": self.message,
            "error": self.error,
            "data": self.data,
            **{k: v for k, v in self.metadata.items() if not k.startswith("_")}
        }


@dataclass
class TaskConfig:
    """任务配置"""
    task_id: str
    name: str
    description: str = ""
    module: str = ""
    class_name: str = ""
    results_dir: str = "results"
    enabled: bool = True
    timeout: int = 300
    retry: int = 0
    params: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "module": self.module,
            "class_name": self.class_name,
            "results_dir": self.results_dir,
            "enabled": self.enabled,
            "timeout": self.timeout,
            "retry": self.retry,
            "params": self.params,
            "schedule": self.schedule
        }
