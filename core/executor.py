import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Callable, Optional
from .base import TaskConfig, TaskResult, TaskStatus, BaseTask
from .task_manager import TaskManager
from .logger import get_global_logger


class TaskExecutor:
    def __init__(self, task_manager: TaskManager, max_workers: int = 5):
        self.task_manager = task_manager
        self.max_workers = max_workers
        self.results: List[TaskResult] = []
        self.running_tasks: int = 0
        self.logger = get_global_logger()
    
    def execute_single_task(self, task_config: TaskConfig, task_instance: BaseTask) -> TaskResult:
        start_time = time.time()
        task_instance.logger.info(f"Starting execution...")
        self.logger.info("Executor", f"Starting task: {task_config.task_id}")
        
        try:
            task_instance.on_task_start()
            
            if not task_instance.validate():
                result = TaskResult(
                    task_id=task_config.task_id,
                    status=TaskStatus.SKIPPED,
                    message="Validation failed",
                    duration=time.time() - start_time
                )
                task_instance.on_task_end(result)
                return result
            
            result = task_instance.execute()
            result.duration = time.time() - start_time
            
            if result.status == TaskStatus.FAILED and result.error:
                task_instance.log_error(result.error)
                self.logger.error("Executor", f"Task failed: {task_config.task_id} - {result.error}")
            
            task_instance.on_task_end(result)
            return result
            
        except Exception as e:
            self.logger.error("Executor", f"Task exception: {task_config.task_id}", e)
            task_instance.log_error(f"Task exception: {str(e)}", e)
            result = TaskResult(
                task_id=task_config.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                duration=time.time() - start_time
            )
            task_instance.on_task_end(result)
            return result
    
    def execute_enabled_tasks(self, task_filter: Optional[Callable[[TaskConfig], bool]] = None):
        enabled_tasks = self.task_manager.get_enabled_tasks()
        
        if task_filter:
            enabled_tasks = [t for t in enabled_tasks if task_filter(t)]
        
        if not enabled_tasks:
            print("[Executor] No enabled tasks to execute")
            self.logger.warning("Executor", "No enabled tasks to execute")
            return
        
        self.logger.info("Executor", f"Starting {len(enabled_tasks)} tasks with {self.max_workers} workers")
        print(f"[Executor] Starting {len(enabled_tasks)} tasks with {self.max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures: List[Future] = []
            
            for task_config in enabled_tasks:
                task_instance = self.task_manager.load_task_module(task_config)
                if task_instance:
                    future = executor.submit(self.execute_single_task, task_config, task_instance)
                    futures.append(future)
                else:
                    result = TaskResult(
                        task_id=task_config.task_id,
                        status=TaskStatus.FAILED,
                        error="Failed to load task module"
                    )
                    self.results.append(result)
                    self.logger.error("Executor", f"Failed to load module: {task_config.task_id}")
            
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
                    
                    if result.screenshot_path:
                        print(f"  Screenshot: {result.screenshot_path}")
                    
                except Exception as e:
                    self.logger.error("Executor", f"Task execution error: {e}")
                    print(f"[ERROR] Task execution error: {e}")
    
    def execute_task_by_id(self, task_id: str) -> Optional[TaskResult]:
        task_config = self.task_manager.get_task(task_id)
        if not task_config:
            print(f"[Executor] Task {task_id} not found")
            self.logger.error("Executor", f"Task not found: {task_id}")
            return None
        
        task_instance = self.task_manager.load_task_module(task_config)
        if not task_instance:
            print(f"[Executor] Failed to load task {task_id}")
            self.logger.error("Executor", f"Failed to load task: {task_id}")
            return None
        
        result = self.execute_single_task(task_config, task_instance)
        self.results.append(result)
        
        status_symbol = {
            TaskStatus.SUCCESS: "[OK]",
            TaskStatus.FAILED: "[FAIL]",
            TaskStatus.SKIPPED: "[SKIP]"
        }.get(result.status, "[???]")
        
        print(f"{status_symbol} {result.task_id}: {result.message or result.error}")
        
        if result.screenshot_path:
            print(f"  Screenshot: {result.screenshot_path}")
        
        return result
    
    def execute_category(self, category_id: str):
        def filter_by_category(task: TaskConfig) -> bool:
            return task.task_id.startswith(f"{category_id}.")
        
        self.logger.info("Executor", f"Executing category: {category_id}")
        self.execute_enabled_tasks(task_filter=filter_by_category)
    
    def execute_group(self, category_id: str, group_id: str):
        def filter_by_group(task: TaskConfig) -> bool:
            parts = task.task_id.split(".")
            return len(parts) >= 2 and parts[0] == category_id and parts[1] == group_id
        
        self.logger.info("Executor", f"Executing group: {category_id}.{group_id}")
        self.execute_enabled_tasks(task_filter=filter_by_group)
    
    def get_results(self) -> List[TaskResult]:
        return self.results
    
    def print_summary(self):
        success = len([r for r in self.results if r.status == TaskStatus.SUCCESS])
        failed = len([r for r in self.results if r.status == TaskStatus.FAILED])
        skipped = len([r for r in self.results if r.status == TaskStatus.SKIPPED])
        
        self.logger.info("Executor", f"Summary: Success={success}, Failed={failed}, Skipped={skipped}")
        
        print("\n" + "=" * 60)
        print("执行结果汇总")
        print("=" * 60)
        print(f"成功: {success}")
        print(f"失败: {failed}")
        print(f"跳过: {skipped}")
        print(f"总计: {len(self.results)}")
        print("=" * 60)
        
        if failed > 0:
            print("\n失败任务详情:")
            for r in self.results:
                if r.status == TaskStatus.FAILED:
                    print(f"  - {r.task_id}: {r.error}")
                    if r.screenshot_path:
                        print(f"    Screenshot: {r.screenshot_path}")
