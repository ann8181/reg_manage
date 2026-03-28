"""
异步任务执行器
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Callable
from .base import TaskConfig, TaskResult, TaskStatus, BaseTask
from .task_manager import TaskManager
import logging

logger = logging.getLogger(__name__)

class AsyncTaskExecutor:
    def __init__(self, task_manager: TaskManager, max_workers: int = 10):
        self.task_manager = task_manager
        self.max_workers = max_workers
        self.results: List[TaskResult] = []
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def execute_async(self, task_filter: Optional[Callable] = None):
        tasks = self.task_manager.get_enabled_tasks()
        if task_filter:
            tasks = [t for t in tasks if task_filter(t)]
        
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def run_task(task_config):
            async with semaphore:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.executor,
                    self._execute_sync,
                    task_config
                )
        
        results = await asyncio.gather(*[run_task(t) for t in tasks])
        return results
    
    def _execute_sync(self, task_config: TaskConfig) -> TaskResult:
        task_instance = self.task_manager.load_task_module(task_config)
        if not task_instance:
            return TaskResult(
                task_id=task_config.task_id,
                status=TaskStatus.FAILED,
                error="Failed to load task module"
            )
        
        try:
            task_instance.on_task_start()
            if not task_instance.validate():
                return TaskResult(
                    task_id=task_config.task_id,
                    status=TaskStatus.SKIPPED,
                    message="Validation failed"
                )
            result = task_instance.execute()
            task_instance.on_task_end(result)
            return result
        except Exception as e:
            logger.error(f"Task {task_config.task_id} failed: {e}")
            return TaskResult(
                task_id=task_config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            task_instance.close_browser()
    
    def get_results(self) -> List[TaskResult]:
        return self.results