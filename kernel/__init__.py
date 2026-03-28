"""
Auto Register - 一体化内核架构

核心理念：
1. 单一内核 (Kernel) - 所有功能的核心入口点
2. 模块注册制 - 功能模块向内核注册
3. 事件驱动 - 模块间通过事件通信
4. 统一资源管理 - 配置/数据库/日志/插件由内核管理

使用方式：
    from kernel import Kernel
    
    kernel = Kernel()
    kernel.start()
    
    # 注册任务
    kernel.register_task("github", GitHubTask)
    
    # 执行任务
    kernel.run_task("github", {"email": "test@mail.com"})
    
    # 调度任务
    kernel.schedule.add("github", cron="0 2 * * *")
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

__version__ = "3.0.0"

class Kernel:
    """
    统一内核
    所有功能的单一入口点
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._running = False
        
        # 基础路径
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.log_dir = self.data_dir / "logs"
        self.config_dir = self.base_dir / "config"
        
        # 创建目录
        self.data_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # 核心组件
        self._config: Dict[str, Any] = {}
        self._tasks: Dict[str, Callable] = {}
        self._modules: Dict[str, Any] = {}
        self._hooks: Dict[str, List[Callable]] = {}
        self._events: Dict[str, List[Callable]] = {}
        
        # 初始化基础组件
        self._init_logging()
        self._init_config()
        self._init_database()
        
        self.logger.info(f"Kernel {__version__} initialized")
    
    def _init_logging(self):
        """初始化日志"""
        self.logger = logging.getLogger("kernel")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_dir / "kernel.log")
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s"
            ))
            self.logger.addHandler(handler)
    
    def _init_config(self):
        """初始化配置"""
        import json
        
        config_file = self.base_dir / "config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                self._config = json.load(f)
        
        # 环境变量覆盖
        for key in ["proxy", "browser_path", "database_path"]:
            env_val = os.environ.get(key.upper(), None)
            if env_val:
                self._config[key] = env_val
    
    def _init_database(self):
        """初始化数据库"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker, declarative_base
        
        db_path = self._config.get("database_path", "data/kernel.db")
        
        # 如果路径包含 :// 说明是完整URL，直接使用
        if "://" in db_path:
            self.engine = create_engine(db_path)
        else:
            # 否则当作相对路径处理
            actual_path = self.data_dir / db_path
            actual_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{actual_path}"
            self.engine = create_engine(db_url)
        
        self.Base = declarative_base()
        self.Session = sessionmaker(bind=self.engine)
        self.Base.metadata.create_all(self.engine)
    
    # ==================== 模块管理 ====================
    
    def register_module(self, name: str, module: Any) -> None:
        """注册功能模块"""
        self._modules[name] = module
        if hasattr(module, 'kernel'):
            module.kernel = self
        self.logger.info(f"Module registered: {name}")
    
    def get_module(self, name: str) -> Optional[Any]:
        """获取模块"""
        return self._modules.get(name)
    
    @property
    def scheduler(self):
        """调度模块"""
        return self._modules.get("scheduler")
    
    @property
    def browser(self):
        """浏览器模块"""
        return self._modules.get("browser")
    
    @property
    def workflow(self):
        """工作流模块"""
        return self._modules.get("workflow")
    
    @property
    def user(self):
        """用户模块"""
        return self._modules.get("user")
    
    @property
    def provider(self):
        """Provider模块"""
        return self._modules.get("provider")
    
    @property
    def account(self):
        """账号模块"""
        return self._modules.get("account")
    
    @property
    def notification(self):
        """通知模块"""
        return self._modules.get("notification")
    
    @property
    def cache(self):
        """缓存模块"""
        return self._modules.get("cache")
    
    @property
    def metrics(self):
        """指标模块"""
        return self._modules.get("metrics")
    
    @property
    def webhook(self):
        """Webhook 模块"""
        return self._modules.get("webhook")
    
    @property
    def queue(self):
        """队列模块"""
        return self._modules.get("queue")
    
    # ==================== 任务管理 ====================
    
    def register_task(self, task_id: str, task_class: Callable) -> None:
        """注册任务"""
        self._tasks[task_id] = task_class
        self.logger.info(f"Task registered: {task_id}")
    
    def get_task(self, task_id: str) -> Optional[Callable]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def list_tasks(self) -> List[str]:
        """列出所有任务"""
        return list(self._tasks.keys())
    
    def run_task(self, task_id: str, params: Dict = None) -> Any:
        """运行任务"""
        task_class = self._tasks.get(task_id)
        if not task_class:
            raise ValueError(f"Task not found: {task_id}")
        
        params = params or {}
        
        # 触发前置钩子
        self._trigger_hook("pre_task", task_id, params)
        
        try:
            task = task_class(kernel=self, **params)
            result = task.execute()
            
            # 触发后置钩子
            self._trigger_hook("post_task", task_id, result)
            
            return result
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {e}")
            self._trigger_hook("task_error", task_id, e)
            raise
    
    def run_tasks(self, task_ids: List[str], params: Dict = None) -> List[Any]:
        """批量运行任务"""
        results = []
        for task_id in task_ids:
            try:
                result = self.run_task(task_id, params)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results
    
    # ==================== 生命周期 ====================
    
    def start(self) -> None:
        """启动内核"""
        if self._running:
            return
        
        self._running = True
        self.logger.info("Kernel starting...")
        
        # 加载内置模块
        self._load_modules()
        
        # 触发启动钩子
        self._trigger_hook("start")
        
        self.logger.info("Kernel started")
    
    def stop(self) -> None:
        """停止内核"""
        if not self._running:
            return
        
        self._running = False
        self.logger.info("Kernel stopping...")
        
        # 触发停止钩子
        self._trigger_hook("stop")
        
        # 停止所有模块
        for name, module in self._modules.items():
            if hasattr(module, 'stop'):
                try:
                    module.stop()
                except Exception as e:
                    self.logger.error(f"Error stopping module {name}: {e}")
        
        self.logger.info("Kernel stopped")
    
    def _load_modules(self) -> None:
        """加载内置模块"""
        from modules.scheduler import SchedulerModule
        from modules.browser import BrowserModule
        from modules.workflow import WorkflowModule
        from modules.user import UserModule
        from modules.provider import ProviderModule
        from modules.account import AccountModule
        from modules.notification import NotificationModule
        from modules.cache import CacheModule
        from modules.metrics import MetricsModule
        from modules.webhook import WebhookModule
        from modules.queue import QueueModule
        
        self.register_module("scheduler", SchedulerModule(self))
        self.register_module("browser", BrowserModule(self))
        self.register_module("workflow", WorkflowModule(self))
        self.register_module("user", UserModule(self))
        self.register_module("provider", ProviderModule(self))
        self.register_module("account", AccountModule(self))
        self.register_module("notification", NotificationModule(self))
        self.register_module("cache", CacheModule(self))
        self.register_module("metrics", MetricsModule(self))
        self.register_module("webhook", WebhookModule(self))
        self.register_module("queue", QueueModule(self))
    
    # ==================== 钩子系统 ====================
    
    def add_hook(self, event: str, callback: Callable) -> None:
        """添加钩子"""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
    
    def _trigger_hook(self, event: str, *args, **kwargs) -> None:
        """触发钩子"""
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Hook {event} error: {e}")
    
    # ==================== 事件系统 ====================
    
    def on(self, event: str, callback: Callable) -> None:
        """监听事件"""
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(callback)
    
    def emit(self, event: str, data: Any = None) -> None:
        """触发事件"""
        for callback in self._events.get(event, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Event {event} error: {e}")
    
    # ==================== 资源访问 ====================
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config.copy()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置项"""
        self._config[key] = value
        self.save_config()
    
    def save_config(self) -> None:
        """保存配置"""
        import json
        config_file = self.base_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """获取日志器"""
        if name:
            return logging.getLogger(f"kernel.{name}")
        return self.logger


# 全局内核实例
_kernel: Optional[Kernel] = None


def get_kernel() -> Kernel:
    """获取内核实例"""
    global _kernel
    if _kernel is None:
        _kernel = Kernel()
        _kernel.start()
    return _kernel


def create_kernel() -> Kernel:
    """创建新内核"""
    global _kernel
    _kernel = Kernel()
    _kernel.start()
    return _kernel
