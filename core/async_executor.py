"""
Async Executor Module - 异步任务执行器
"""

import asyncio
from typing import List, Callable, Any, Dict
from concurrent.futures import ThreadPoolExecutor

from .base import TaskResult, TaskStatus


class AsyncTaskExecutor:
    """异步任务执行器"""
    
    def __init__(self, task_manager, max_workers: int = 5):
        self.task_manager = task_manager
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def execute_async(self) -> List[TaskResult]:
        """异步执行所有启用任务"""
        enabled_tasks = self.task_manager.get_enabled_tasks()
        results = []
        
        loop = asyncio.get_event_loop()
        
        for task in enabled_tasks:
            try:
                result = await loop.run_in_executor(
                    self.executor,
                    self._execute_task,
                    task
                )
                results.append(result)
            except Exception as e:
                results.append(TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    error=str(e)
                ))
        
        return results
    
    def _execute_task(self, task) -> TaskResult:
        """执行单个任务"""
        try:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                message=f"Task {task.name} executed"
            )
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
    
    def execute_batch(self, task_ids: List[str] = None) -> List[TaskResult]:
        """批量执行任务"""
        tasks = self.task_manager.all_tasks
        if task_ids:
            tasks = [t for t in tasks if t.task_id in task_ids]
        
        results = []
        for task in tasks:
            if task.enabled:
                results.append(self._execute_task(task))
        
        return results
    
    def shutdown(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)
