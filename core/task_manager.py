"""
Task Manager Module - 任务管理
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class TaskDef:
    """任务定义"""
    task_id: str
    name: str
    description: str = ""
    module: str = ""
    class_name: str = ""
    enabled: bool = True
    params: Dict = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TaskGroup:
    """任务组"""
    name: str
    tasks: List[TaskDef] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []


@dataclass
class TaskCategory:
    """任务分类"""
    name: str
    groups: List[TaskGroup] = None
    
    def __post_init__(self):
        if self.groups is None:
            self.groups = []


class TaskManager:
    """任务管理器"""
    
    def __init__(self, config_path: str, global_config_path: str = ""):
        self.config_path = Path(config_path)
        self.global_config_path = Path(global_config_path) if global_config_path else None
        self.categories: Dict[str, TaskCategory] = {}
        self.all_tasks: List[TaskDef] = []
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._parse_config(data)
    
    def _parse_config(self, data: Dict):
        """解析配置"""
        self.categories = {}
        self.all_tasks = []
        
        for cat_id, cat_data in data.get("categories", {}).items():
            groups = []
            for grp_data in cat_data.get("groups", []):
                tasks = []
                for task_data in grp_data.get("tasks", []):
                    task = TaskDef(
                        task_id=task_data.get("task_id", ""),
                        name=task_data.get("name", ""),
                        description=task_data.get("description", ""),
                        module=task_data.get("module", ""),
                        class_name=task_data.get("class_name", ""),
                        enabled=task_data.get("enabled", True),
                        params=task_data.get("params", {})
                    )
                    tasks.append(task)
                    self.all_tasks.append(task)
                grp = TaskGroup(name=grp_data.get("name", ""), tasks=tasks)
                groups.append(grp)
            self.categories[cat_id] = TaskCategory(name=cat_data.get("name", ""), groups=groups)
    
    def get_enabled_tasks(self) -> List[TaskDef]:
        """获取已启用的任务"""
        return [t for t in self.all_tasks if t.enabled]
    
    def enable_task(self, task_id: str, enabled: bool = True):
        """启用/禁用任务"""
        for task in self.all_tasks:
            if task.task_id == task_id:
                task.enabled = enabled
                break
    
    def save_config(self):
        """保存配置"""
        data = {"categories": {}}
        for cat_id, cat in self.categories.items():
            data["categories"][cat_id] = {
                "name": cat.name,
                "groups": [
                    {
                        "name": grp.name,
                        "tasks": [asdict(t) for t in grp.tasks]
                    }
                    for grp in cat.groups
                ]
            }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
