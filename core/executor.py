import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Callable, Optional
from .base import TaskConfig, TaskResult, TaskStatus, BaseTask
from .task_manager import TaskManager


class TaskExecutor:
    def __init__(self, task_manager: TaskManager, max_workers: int = 5):
        self.task_manager = task_manager
        self.max_workers = max_workers
        self.results: List[TaskResult] = []
        self.running_tasks: int = 0
    
    def execute_single_task(self, task_config: TaskConfig, task_instance: BaseTask) -> TaskResult:
        start_time = time.time()
        task_instance.log(f"Starting execution...")
        
        try:
            if not task_instance.validate():
                return TaskResult(
                    task_id=task_config.task_id,
                    status=TaskStatus.SKIPPED,
                    message="Validation failed",
                    duration=time.time() - start_time
                )
            
            result = task_instance.execute()
            result.duration = time.time() - start_time
            return result
            
        except Exception as e:
            return TaskResult(
                task_id=task_config.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                duration=time.time() - start_time
            )
    
    def execute_enabled_tasks(self, task_filter: Optional[Callable[[TaskConfig], bool]] = None):
        enabled_tasks = self.task_manager.get_enabled_tasks()
        
        if task_filter:
            enabled_tasks = [t for t in enabled_tasks if task_filter(t)]
        
        if not enabled_tasks:
            print("[Executor] No enabled tasks to execute")
            return
        
        print(f"[Executor] Starting {len(enabled_tasks)} tasks with {self.max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures: List[Future] = []
            
            for task_config in enabled_tasks:
                task_instance = self.task_manager.load_task_module(task_config)
                if task_instance:
                    future = executor.submit(self.execute_single_task, task_config, task_instance)
                    futures.append(future)
                else:
                    self.results.append(TaskResult(
                        task_id=task_config.task_id,
                        status=TaskStatus.FAILED,
                        error="Failed to load task module"
                    ))
            
            for future in futures:
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    status_symbol = {
                        TaskStatus.SUCCESS: "[OK]",
                        TaskStatus.FAILED: "[FAIL]",
                        TaskStatus.SKIPPED: "[SKIP]",
                        TaskStatus.RUNNING: "[RUN]",
                        TaskStatus.PENDING: "[WAIT]"
                    }.get(result.status, "[???]")
                    
                    print(f"{status_symbol} {result.task_id}: {result.message or result.error or 'Completed'}")
                    
                except Exception as e:
                    print(f"[ERROR] Task execution error: {e}")
    
    def execute_task_by_id(self, task_id: str) -> Optional[TaskResult]:
        task_config = self.task_manager.get_task(task_id)
        if not task_config:
            print(f"[Executor] Task {task_id} not found")
            return None
        
        task_instance = self.task_manager.load_task_module(task_config)
        if not task_instance:
            print(f"[Executor] Failed to load task {task_id}")
            return None
        
        result = self.execute_single_task(task_config, task_instance)
        self.results.append(result)
        
        status_symbol = {
            TaskStatus.SUCCESS: "[OK]",
            TaskStatus.FAILED: "[FAIL]",
            TaskStatus.SKIPPED: "[SKIP]"
        }.get(result.status, "[???]")
        
        print(f"{status_symbol} {result.task_id}: {result.message or result.error}")
        return result
    
    def execute_category(self, category_id: str):
        def filter_by_category(task: TaskConfig) -> bool:
            return task.task_id.startswith(f"{category_id}.")
        
        self.execute_enabled_tasks(task_filter=filter_by_category)
    
    def execute_group(self, category_id: str, group_id: str):
        def filter_by_group(task: TaskConfig) -> bool:
            parts = task.task_id.split(".")
            return len(parts) >= 2 and parts[0] == category_id and parts[1] == group_id
        
        self.execute_enabled_tasks(task_filter=filter_by_group)
    
    def get_results(self) -> List[TaskResult]:
        return self.results
    
    def print_summary(self):
        success = len([r for r in self.results if r.status == TaskStatus.SUCCESS])
        failed = len([r for r in self.results if r.status == TaskStatus.FAILED])
        skipped = len([r for r in self.results if r.status == TaskStatus.SKIPPED])
        
        print("\n" + "=" * 60)
        print("执行结果汇总")
        print("=" * 60)
        print(f"成功: {success}")
        print(f"失败: {failed}")
        print(f"跳过: {skipped}")
        print(f"总计: {len(self.results)}")
        print("=" * 60)
