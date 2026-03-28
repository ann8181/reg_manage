"""
Queue Module - 异步任务队列模块
支持 Redis 队列和内存队列，提供任务异步执行
"""

import json
import uuid
import time
import threading
import queue as std_queue
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum


class QueueType(Enum):
    REDIS = "redis"
    MEMORY = "memory"


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """任务定义"""
    id: str
    queue_name: str
    func_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    status: str = JobStatus.PENDING.value
    result: Any = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    completed_at: float = 0
    retries: int = 0
    max_retries: int = 3


class QueueBackend(ABC):
    """队列后端基类"""
    
    @abstractmethod
    def enqueue(self, job: Job) -> bool:
        """入队"""
        pass
    
    @abstractmethod
    def dequeue(self, timeout: float = 0) -> Optional[Job]:
        """出队"""
        pass
    
    @abstractmethod
    def ack(self, job_id: str) -> bool:
        """确认"""
        pass
    
    @abstractmethod
    def nack(self, job_id: str) -> bool:
        """拒绝"""
        pass
    
    @abstractmethod
    def length(self, queue_name: str) -> int:
        """队列长度"""
        pass
    
    @abstractmethod
    def clear(self, queue_name: str) -> bool:
        """清空队列"""
        pass


class MemoryQueue(QueueBackend):
    """内存队列"""
    
    def __init__(self, max_size: int = 10000):
        self._queues: Dict[str, std_queue.PriorityQueue] = {}
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._max_size = max_size
    
    def _get_queue(self, queue_name: str) -> std_queue.PriorityQueue:
        if queue_name not in self._queues:
            self._queues[queue_name] = std_queue.PriorityQueue(maxsize=self._max_size)
        return self._queues[queue_name]
    
    def enqueue(self, job: Job) -> bool:
        with self._lock:
            q = self._get_queue(job.queue_name)
            if q.full():
                return False
            self._jobs[job.id] = job
            q.put((256 - job.priority, job.id))
            return True
    
    def dequeue(self, timeout: float = 0) -> Optional[Job]:
        queue_name = "default"
        q = self._get_queue(queue_name)
        try:
            _, job_id = q.get(block=True, timeout=timeout)
            with self._lock:
                job = self._jobs.get(job_id)
                if job:
                    job.status = JobStatus.RUNNING.value
                    job.started_at = time.time()
                return job
        except std_queue.Empty:
            return None
    
    def dequeue_from(self, queue_names: list, timeout: float = 0) -> Optional[Job]:
        queues = [(self._get_queue(name), name) for name in queue_names]
        deadline = time.time() + timeout if timeout > 0 else None
        
        while True:
            for q, name in queues:
                try:
                    _, job_id = q.get_nowait()
                    with self._lock:
                        job = self._jobs.get(job_id)
                        if job:
                            job.status = JobStatus.RUNNING.value
                            job.started_at = time.time()
                        return job
                except std_queue.Empty:
                    continue
            
            if deadline and time.time() >= deadline:
                return None
            time.sleep(0.01)
    
    def ack(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.COMPLETED.value
                job.completed_at = time.time()
                del self._jobs[job_id]
                return True
            return False
    
    def nack(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                if job.retries < job.max_retries:
                    job.retries += 1
                    job.status = JobStatus.PENDING.value
                    q = self._get_queue(job.queue_name)
                    q.put((256 - job.priority, job.id))
                else:
                    job.status = JobStatus.FAILED.value
                    job.completed_at = time.time()
                return True
            return False
    
    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.CANCELLED.value
                job.completed_at = time.time()
                return True
            return False
    
    def length(self, queue_name: str = "default") -> int:
        q = self._get_queue(queue_name)
        return q.qsize()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)
    
    def clear(self, queue_name: str = "default") -> bool:
        with self._lock:
            if queue_name in self._queues:
                while not self._queues[queue_name].empty():
                    _, job_id = self._queues[queue_name].get_nowait()
                    if job_id in self._jobs:
                        del self._jobs[job_id]
                return True
            return False
    
    def get_pending_jobs(self, queue_name: str = "default") -> list:
        with self._lock:
            return [j for j in self._jobs.values() 
                    if j.queue_name == queue_name and j.status == JobStatus.PENDING.value]


class RedisQueue(QueueBackend):
    """Redis 队列"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: str = None, prefix: str = "queue:"):
        self._prefix = prefix
        self._client = None
        self._connected = False
        
        try:
            import redis
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )
            self._client.ping()
            self._connected = True
        except Exception:
            self._connected = False
    
    def _key(self, queue_name: str) -> str:
        return f"{self._prefix}{queue_name}"
    
    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None
    
    def enqueue(self, job: Job) -> bool:
        if not self.is_connected:
            return False
        
        try:
            import redis
            job_json = json.dumps({
                "id": job.id,
                "queue_name": job.queue_name,
                "func_name": job.func_name,
                "args": job.args,
                "kwargs": job.kwargs,
                "priority": job.priority,
                "status": job.status,
                "created_at": job.created_at
            })
            self._client.zadd(self._key(job.queue_name), {job_json: 256 - job.priority})
            return True
        except Exception:
            return False
    
    def dequeue(self, timeout: float = 0) -> Optional[Job]:
        if not self.is_connected:
            return None
        
        try:
            if timeout > 0:
                result = self._client.bzpopmin(self._key("default"), timeout=timeout)
                if result:
                    _, job_json = result
            else:
                job_json = self._client.zpopmin(self._key("default"), count=1)
                if job_json:
                    job_json = job_json[0][0]
                else:
                    return None
            
            data = json.loads(job_json)
            return Job(**data)
        except Exception:
            return None
    
    def ack(self, job_id: str) -> bool:
        return True
    
    def nack(self, job_id: str) -> bool:
        return True
    
    def length(self, queue_name: str = "default") -> int:
        if not self.is_connected:
            return 0
        
        try:
            return self._client.zcard(self._key(queue_name))
        except Exception:
            return 0
    
    def clear(self, queue_name: str = "default") -> bool:
        if not self.is_connected:
            return False
        
        try:
            self._client.delete(self._key(queue_name))
            return True
        except Exception:
            return False


class QueueModule:
    """
    异步任务队列模块
    提供任务异步执行、延迟任务、任务重试
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self._memory = MemoryQueue()
        self._redis: Optional[RedisQueue] = None
        self._backend = "memory"
        self._functions: Dict[str, Callable] = {}
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._logger = kernel.get_logger("queue")
        self._logger.info("QueueModule initialized with memory backend")
    
    def set_backend(self, backend: str = "memory"):
        """设置队列后端"""
        if backend == "redis":
            self._backend = "redis"
            self._logger.info("Switched to Redis backend")
        else:
            self._backend = "memory"
            self._logger.info("Switched to memory backend")
    
    def set_redis(self, host: str = "localhost", port: int = 6379, db: int = 0, password: str = None):
        """配置 Redis"""
        self._redis = RedisQueue(host, port, db, password)
        if self._redis.is_connected:
            self._logger.info(f"Redis connected: {host}:{port}")
        else:
            self._logger.warning("Redis connection failed, falling back to memory")
    
    @property
    def backend(self) -> QueueBackend:
        """获取当前后端"""
        if self._backend == "redis" and self._redis and self._redis.is_connected:
            return self._redis
        return self._memory
    
    def register_function(self, name: str, func: Callable):
        """注册函数"""
        self._functions[name] = func
        self._logger.info(f"Function registered: {name}")
    
    def enqueue(
        self,
        func_name: str,
        *args,
        queue_name: str = "default",
        priority: int = 0,
        **kwargs
    ) -> Optional[str]:
        """入队"""
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            id=job_id,
            queue_name=queue_name,
            func_name=func_name,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        if self.backend.enqueue(job):
            self._logger.info(f"Job enqueued: {job_id} -> {func_name}")
            return job_id
        return None
    
    def enqueue_delayed(
        self,
        delay: float,
        func_name: str,
        *args,
        queue_name: str = "default",
        priority: int = 0,
        **kwargs
    ) -> Optional[str]:
        """延迟入队"""
        import time
        job_id = str(uuid.uuid4())[:8]
        
        def delayed_call():
            time.sleep(delay)
            self.enqueue(func_name, *args, queue_name=queue_name, priority=priority, **kwargs)
        
        thread = threading.Thread(target=delayed_call, daemon=True)
        thread.start()
        
        return job_id
    
    def dequeue(self, timeout: float = 0) -> Optional[Job]:
        """出队"""
        return self.backend.dequeue(timeout)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """获取任务"""
        return self._memory.get_job(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """取消任务"""
        return self._memory.cancel(job_id)
    
    def ack(self, job_id: str) -> bool:
        """确认任务"""
        return self.backend.ack(job_id)
    
    def nack(self, job_id: str) -> bool:
        """拒绝任务"""
        return self.backend.nack(job_id)
    
    def execute_job(self, job: Job) -> Any:
        """执行任务"""
        if job.func_name not in self._functions:
            raise ValueError(f"Function not registered: {job.func_name}")
        
        func = self._functions[job.func_name]
        try:
            result = func(*job.args, **job.kwargs)
            job.result = result
            job.status = JobStatus.COMPLETED.value
            return result
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED.value
            raise
    
    def start_worker(self, queue_names: list = None, poll_interval: float = 0.1):
        """启动 Worker"""
        if self._running:
            return
        
        self._running = True
        queue_names = queue_names or ["default"]
        
        def worker():
            while self._running:
                job = self.backend.dequeue_from(queue_names, timeout=poll_interval)
                if job:
                    try:
                        self.execute_job(job)
                        self.ack(job.id)
                    except Exception as e:
                        self._logger.error(f"Job {job.id} failed: {e}")
                        self.nack(job.id)
        
        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()
        self._logger.info("Worker started")
    
    def stop_worker(self):
        """停止 Worker"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        self._logger.info("Worker stopped")
    
    def length(self, queue_name: str = "default") -> int:
        """队列长度"""
        return self.backend.length(queue_name)
    
    def clear(self, queue_name: str = "default") -> bool:
        """清空队列"""
        return self.backend.clear(queue_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "backend": self._backend,
            "registered_functions": len(self._functions),
            "pending_default": self.length("default"),
            "pending_high": self.length("high"),
            "pending_low": self.length("low")
        }
    
    def stop(self):
        """停止模块"""
        self.stop_worker()
        self._logger.info("QueueModule stopped")
