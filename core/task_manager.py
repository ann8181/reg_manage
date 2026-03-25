import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from .base import TaskConfig, TaskStatus, TaskResult, BaseTask


@dataclass
class CategoryInfo:
    id: str
    name: str
    description: str
    enabled: bool
    groups: List['GroupInfo']


@dataclass
class GroupInfo:
    id: str
    name: str
    description: str
    enabled: bool
    tasks: List[TaskConfig]


class TaskManager:
    def __init__(self, config_path: str, global_config_path: str):
        self.config_path = config_path
        self.global_config = self._load_json(global_config_path)
        self.categories: Dict[str, CategoryInfo] = {}
        self.all_tasks: Dict[str, TaskConfig] = {}
        self._load_tasks_config()
    
    def _load_json(self, path: str) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_tasks_config(self):
        tasks_config = self.global_config.get('categories', {})
        
        for cat_id, cat_data in tasks_config.items():
            groups = []
            for grp_id, grp_data in cat_data.get('groups', {}).items():
                tasks = []
                for task_id, task_data in grp_data.get('tasks', {}).items():
                    task_config = TaskConfig(
                        task_id=task_id,
                        name=task_data.get('name', task_id),
                        description=task_data.get('description', ''),
                        module=task_data.get('module', ''),
                        class_name=task_data.get('class', ''),
                        results_dir=task_data.get('results_dir', f'results/{task_id}'),
                        enabled=task_data.get('enabled', False),
                        config=task_data
                    )
                    tasks.append(task_config)
                    self.all_tasks[task_id] = task_config
                groups.append(GroupInfo(
                    id=grp_id,
                    name=grp_data.get('name', grp_id),
                    description=grp_data.get('description', ''),
                    enabled=grp_data.get('enabled', True),
                    tasks=tasks
                ))
            
            self.categories[cat_id] = CategoryInfo(
                id=cat_id,
                name=cat_data.get('name', cat_id),
                description=cat_data.get('description', ''),
                enabled=cat_data.get('enabled', True),
                groups=groups
            )
    
    def get_enabled_tasks(self) -> List[TaskConfig]:
        enabled = []
        for task in self.all_tasks.values():
            if task.enabled:
                enabled.append(task)
        return enabled
    
    def get_task(self, task_id: str) -> Optional[TaskConfig]:
        return self.all_tasks.get(task_id)
    
    def enable_task(self, task_id: str, enabled: bool = True):
        if task_id in self.all_tasks:
            self.all_tasks[task_id].enabled = enabled
    
    def enable_category(self, cat_id: str, enabled: bool = True):
        if cat_id in self.categories:
            self.categories[cat_id].enabled = enabled
            for grp in self.categories[cat_id].groups:
                grp.enabled = enabled
                for task in grp.tasks:
                    task.enabled = enabled
    
    def enable_group(self, cat_id: str, grp_id: str, enabled: bool = True):
        if cat_id in self.categories:
            cat = self.categories[cat_id]
            for grp in cat.groups:
                if grp.id == grp_id:
                    grp.enabled = enabled
                    for task in grp.tasks:
                        task.enabled = enabled
                    break
    
    def enable_tasks_by_pattern(self, pattern: str, enabled: bool = True):
        for task_id in self.all_tasks.keys():
            if pattern.lower() in task_id.lower():
                self.all_tasks[task_id].enabled = enabled
    
    def disable_all_tasks(self):
        for task in self.all_tasks.values():
            task.enabled = False
    
    def load_task_module(self, task_config: TaskConfig) -> Optional[BaseTask]:
        try:
            module_path = task_config.module.replace('.', '/') + '.py'
            import importlib.util
            spec = importlib.util.spec_from_file_location(task_config.module, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                task_class = getattr(module, task_config.class_name)
                return task_class(task_config, self.global_config)
        except Exception as e:
            print(f"[TaskManager] Failed to load module {task_config.module}: {e}")
        return None
    
    def save_config(self):
        for cat_id, cat in self.categories.items():
            cat_data = self.global_config['categories'].get(cat_id, {})
            cat_data['enabled'] = cat.enabled
            for grp in cat.groups:
                grp_data = cat_data.get('groups', {}).get(grp.id, {})
                grp_data['enabled'] = grp.enabled
                for task in grp.tasks:
                    task_data = grp_data.get('tasks', {}).get(task.task_id, {})
                    task_data['enabled'] = task.enabled
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.global_config, f, indent=4, ensure_ascii=False)
    
    def print_status(self):
        print("\n" + "=" * 60)
        print("任务状态总览")
        print("=" * 60)
        
        for cat_id, cat in self.categories.items():
            cat_symbol = "[x]" if cat.enabled else "[ ]"
            print(f"\n{cat_symbol} {cat.name} ({cat_id})")
            print(f"    {cat.description}")
            
            for grp in cat.groups:
                grp_symbol = "[x]" if grp.enabled else "[ ]"
                print(f"  {grp_symbol} {grp.name}")
                
                for task in grp.tasks:
                    task_symbol = "[x]" if task.enabled else "[ ]"
                    print(f"    {task_symbol} {task.name} ({task.task_id})")
        
        enabled_count = len([t for t in self.all_tasks.values() if t.enabled])
        total_count = len(self.all_tasks)
        print(f"\n已启用任务: {enabled_count}/{total_count}")
        print("=" * 60)
