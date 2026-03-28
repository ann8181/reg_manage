import os
import sys
import time
import json
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import contextmanager


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    timestamp: str
    level: str
    task_id: str
    message: str
    action: Optional[str] = None
    duration_ms: Optional[float] = None
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class StructuredLogWriter:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.json_file = log_file.replace(".log", ".jsonl")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    def write(self, entry: LogEntry):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry.timestamp = timestamp
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            level_indicator = f"[{entry.level}]"
            msg = f"[{timestamp}] {level_indicator} [{entry.task_id}]"
            if entry.action:
                msg += f" [{entry.action}]"
            msg += f" {entry.message}"
            
            if entry.duration_ms is not None:
                msg += f" ({entry.duration_ms:.2f}ms)"
            
            if entry.screenshot_path:
                msg += f"\n  Screenshot: {entry.screenshot_path}"
            
            if entry.error:
                msg += f"\n  Error: {entry.error}"
            
            if entry.traceback:
                msg += f"\n  Traceback: {entry.traceback}"
            
            if entry.extra:
                msg += f"\n  Extra: {json.dumps(entry.extra, ensure_ascii=False)}"
            
            f.write(msg + "\n")
        
        with open(self.json_file, 'a', encoding='utf-8') as f:
            f.write(entry.to_json() + "\n")


class BrowserActionLogger:
    """
    浏览器操作日志记录器
    记录所有浏览器操作并自动截图，便于后期分析和优化
    """
    
    def __init__(self, task_id: str, log_dir: str = "logs"):
        self.task_id = task_id
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), log_dir, task_id)
        self.screenshot_dir = os.path.join(self.base_dir, "screenshots", "browser_actions")
        self.action_log_file = os.path.join(self.base_dir, "browser_actions.jsonl")
        
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        self.action_sequence = 0
        self.current_page = None
        self._request_count = 0
        self._response_count = 0
    
    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _get_date_str(self) -> str:
        return datetime.now().strftime("%Y%m%d")
    
    def _generate_action_id(self) -> str:
        self.action_sequence += 1
        return f"act_{self._get_date_str()}_{self.action_sequence:04d}"
    
    def _sanitize_filename(self, name: str) -> str:
        return name.replace(":", "-").replace(" ", "_").replace("/", "_")
    
    def set_page(self, page):
        """设置当前页面对象"""
        self.current_page = page
    
    def log_action(
        self,
        action: str,
        description: str = "",
        page=None,
        take_screenshot: bool = True,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        记录浏览器操作
        
        Args:
            action: 操作类型 (navigate, click, fill, submit, wait, etc.)
            description: 操作描述
            page: Playwright page对象
            take_screenshot: 是否截图
            metadata: 额外元数据
        
        Returns:
            action_id: 操作ID
        """
        action_id = self._generate_action_id()
        screenshot_path = None
        
        if take_screenshot:
            if page is None:
                page = self.current_page
            
            if page:
                try:
                    filename = f"{action_id}_{self._sanitize_filename(action)}.png"
                    screenshot_path = os.path.join(self.screenshot_dir, filename)
                    page.screenshot(path=screenshot_path, full_page=True)
                except Exception as e:
                    screenshot_path = f"ERROR: {str(e)}"
        
        entry = {
            "action_id": action_id,
            "timestamp": self._get_timestamp(),
            "action": action,
            "description": description,
            "screenshot": screenshot_path,
            "metadata": metadata or {}
        }
        
        with open(self.action_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return action_id
    
    def log_navigate(self, url: str, page=None, wait_until: str = "load") -> str:
        """记录导航操作"""
        return self.log_action(
            action="navigate",
            description=f"Navigate to {url}",
            page=page,
            metadata={"url": url, "wait_until": wait_until}
        )
    
    def log_click(self, selector: str, page=None) -> str:
        """记录点击操作"""
        return self.log_action(
            action="click",
            description=f"Click element: {selector}",
            page=page,
            metadata={"selector": selector}
        )
    
    def log_fill(self, selector: str, value: str, page=None, mask: bool = True) -> str:
        """记录填写操作"""
        display_value = "***MASKED***" if mask and len(value) > 4 else value
        return self.log_action(
            action="fill",
            description=f"Fill {selector} with {display_value}",
            page=page,
            metadata={"selector": selector, "value_length": len(value), "masked": mask}
        )
    
    def log_submit(self, selector: str = None, page=None) -> str:
        """记录提交操作"""
        return self.log_action(
            action="submit",
            description=f"Submit form" + (f" ({selector})" if selector else ""),
            page=page,
            metadata={"selector": selector} if selector else {}
        )
    
    def log_wait(self, selector: str = None, timeout: int = None, page=None) -> str:
        """记录等待操作"""
        return self.log_action(
            action="wait",
            description=f"Wait for {selector or 'timeout'}",
            page=page,
            metadata={"selector": selector, "timeout": timeout}
        )
    
    def log_select(self, selector: str, value: str, page=None) -> str:
        """记录选择操作"""
        return self.log_action(
            action="select",
            description=f"Select {value} in {selector}",
            page=page,
            metadata={"selector": selector, "value": value}
        )
    
    def log_hover(self, selector: str, page=None) -> str:
        """记录悬停操作"""
        return self.log_action(
            action="hover",
            description=f"Hover over {selector}",
            page=page,
            metadata={"selector": selector}
        )
    
    def log_evaluate(self, script: str, page=None) -> str:
        """记录JavaScript执行"""
        return self.log_action(
            action="evaluate",
            description=f"Execute JS: {script[:100]}...",
            page=page,
            metadata={"script_length": len(script)}
        )
    
    def log_request(self, url: str, method: str = "GET", headers: Dict = None) -> str:
        """记录网络请求"""
        self._request_count += 1
        return self.log_action(
            action="request",
            description=f"{method} {url}",
            take_screenshot=False,
            metadata={
                "url": url,
                "method": method,
                "headers": headers,
                "request_number": self._request_count
            }
        )
    
    def log_response(self, url: str, status: int, headers: Dict = None) -> str:
        """记录网络响应"""
        self._response_count += 1
        return self.log_action(
            action="response",
            description=f"Response {status} from {url}",
            take_screenshot=False,
            metadata={
                "url": url,
                "status": status,
                "headers": headers,
                "response_number": self._response_count
            }
        )
    
    def log_error(self, error: str, page=None, take_screenshot: bool = True) -> str:
        """记录错误"""
        return self.log_action(
            action="error",
            description=f"Error: {error}",
            page=page,
            take_screenshot=take_screenshot,
            metadata={"error": error}
        )
    
    def log_page_error(self, error: str, page=None) -> str:
        """记录页面错误"""
        return self.log_action(
            action="page_error",
            description=f"Page Error: {error}",
            page=page,
            take_screenshot=True,
            metadata={"error": error}
        )
    
    def take_screenshot(self, name: str = None, page=None, full_page: bool = True) -> Optional[str]:
        """手动截图"""
        if page is None:
            page = self.current_page
        
        if page is None:
            return None
        
        action_id = self._generate_action_id()
        filename = f"{action_id}_{self._sanitize_filename(name or 'manual')}.png"
        screenshot_path = os.path.join(self.screenshot_dir, filename)
        
        try:
            page.screenshot(path=screenshot_path, full_page=full_page)
            return screenshot_path
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def log_console_message(self, msg_type: str, text: str) -> str:
        """记录控制台消息"""
        return self.log_action(
            action=f"console_{msg_type}",
            description=f"Console {msg_type}: {text}",
            take_screenshot=False,
            metadata={"msg_type": msg_type, "text": text}
        )


class PerformanceMetrics:
    """
    性能指标记录器
    记录任务执行的性能数据
    """
    
    def __init__(self, task_id: str, log_dir: str = "logs"):
        self.task_id = task_id
        self.metrics_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), log_dir, task_id, "metrics")
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        self.metrics_file = os.path.join(self.metrics_dir, "performance.jsonl")
        self.start_time = None
        self.end_time = None
        self.operation_times: Dict[str, List[float]] = {}
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self._log_metric("task_start", {"timestamp": self._get_timestamp()})
    
    def end(self):
        """结束计时"""
        self.end_time = time.time()
        total_duration = (self.end_time - self.start_time) * 1000 if self.start_time else 0
        
        self._log_metric("task_end", {
            "timestamp": self._get_timestamp(),
            "total_duration_ms": total_duration
        })
    
    def record_operation(self, operation: str, duration_ms: float, metadata: Dict = None):
        """记录操作耗时"""
        if operation not in self.operation_times:
            self.operation_times[operation] = []
        self.operation_times[operation].append(duration_ms)
        
        self._log_metric(f"op_{operation}", {
            "operation": operation,
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        })
    
    def record_browser_action(self, action: str, duration_ms: float):
        """记录浏览器操作耗时"""
        self._log_metric(f"browser_{action}", {
            "action": action,
            "duration_ms": duration_ms
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.start_time:
            return {}
        
        total_duration = (time.time() - self.start_time) * 1000
        
        op_summary = {}
        for op, times in self.operation_times.items():
            op_summary[op] = {
                "count": len(times),
                "total_ms": sum(times),
                "avg_ms": sum(times) / len(times) if times else 0,
                "min_ms": min(times) if times else 0,
                "max_ms": max(times) if times else 0
            }
        
        return {
            "task_id": self.task_id,
            "total_duration_ms": total_duration,
            "operations": op_summary,
            "timestamp": self._get_timestamp()
        }
    
    def _log_metric(self, metric_type: str, data: Dict):
        entry = {
            "timestamp": self._get_timestamp(),
            "task_id": self.task_id,
            "metric_type": metric_type,
            **data
        }
        with open(self.metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    @contextmanager
    def measure(self, operation: str, metadata: Dict = None):
        """上下文管理器，用于测量代码块执行时间"""
        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            self.record_operation(operation, duration_ms, metadata)


class TaskLogger:
    _instances: Dict[str, 'TaskLogger'] = {}
    
    def __init__(self, task_id: str, log_dir: str = "logs"):
        self.task_id = task_id
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), log_dir, task_id)
        self.log_dir = self.base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
        self.log_file = os.path.join(self.log_dir, f"{task_id}_{self._get_date_str()}.log")
        self.screenshot_dir = os.path.join(self.log_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        self.json_writer = StructuredLogWriter(self.log_file)
        self.browser_logger = BrowserActionLogger(task_id, log_dir)
        self.perf_metrics = PerformanceMetrics(task_id, log_dir)
        
        self._init_log_file()
    
    def _get_date_str(self) -> str:
        return datetime.now().strftime("%Y%m%d")
    
    def _get_time_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _init_log_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Task Log Started at {self._get_time_str()} ===\n")
                f.write(f"Task ID: {self.task_id}\n")
                f.write("=" * 60 + "\n\n")
    
    def _write_log(self, level: LogLevel, message: str, exc_info: Optional[Exception] = None, 
                   action: str = None, extra: Dict[str, Any] = None):
        entry = LogEntry(
            timestamp=self._get_time_str(),
            level=level.value,
            task_id=self.task_id,
            message=message,
            action=action,
            error=str(exc_info) if exc_info else None,
            traceback=traceback.format_exc() if exc_info else None,
            extra=extra
        )
        
        self.json_writer.write(entry)
        
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            print(f"[{self.task_id}] [{level.value}] {message}", file=sys.stderr)
        else:
            print(f"[{self.task_id}] {message}")
    
    def debug(self, message: str, action: str = None):
        return self._write_log(LogLevel.DEBUG, message, action=action)
    
    def info(self, message: str, action: str = None):
        return self._write_log(LogLevel.INFO, message, action=action)
    
    def warning(self, message: str, action: str = None):
        return self._write_log(LogLevel.WARNING, message, action=action)
    
    def error(self, message: str, exc_info: Optional[Exception] = None, action: str = None):
        return self._write_log(LogLevel.ERROR, message, exc_info, action=action)
    
    def critical(self, message: str, exc_info: Optional[Exception] = None, action: str = None):
        return self._write_log(LogLevel.CRITICAL, message, exc_info, action=action)
    
    def log_action_start(self, action: str, description: str = "", metadata: Dict = None):
        """记录操作开始"""
        self.browser_logger.log_action(action, description, take_screenshot=True, metadata=metadata)
        self.info(f"[ACTION START] {action}: {description}", action=action)
    
    def log_action_end(self, action: str, description: str = "", success: bool = True):
        """记录操作结束"""
        self.browser_logger.log_action(
            action + "_end" if success else action + "_failed",
            description,
            take_screenshot=True
        )
        status = "SUCCESS" if success else "FAILED"
        self.info(f"[ACTION {status}] {action}: {description}", action=action)
    
    def take_screenshot(self, name: str = None, page=None, full_page: bool = True) -> Optional[str]:
        if name is None:
            name = f"screenshot_{self._get_time_str().replace(':', '-').replace(' ', '_')}"
        
        screenshot_path = os.path.join(self.screenshot_dir, f"{name}.png")
        
        try:
            if page:
                page.screenshot(path=screenshot_path, full_page=full_page)
                self.info(f"Screenshot saved: {screenshot_path}")
                return screenshot_path
            else:
                from camoufox.sync_api import Camoufox
                with Camoufox(headless=True) as browser:
                    page = browser.new_page()
                    page.goto("about:blank")
                    page.screenshot(path=screenshot_path)
                    self.info(f"Screenshot saved: {screenshot_path}")
                    return screenshot_path
        except Exception as e:
            self.error(f"Failed to take screenshot: {e}")
            return None
    
    def take_error_screenshot(self, name: str = "error", page=None) -> Optional[str]:
        screenshot_name = f"error_{self._get_time_str().replace(':', '-').replace(' ', '_')}_{name}"
        return self.take_screenshot(screenshot_name, page)
    
    def log_browser_action(self, action: str, description: str = "", page=None, metadata: Dict = None):
        """记录浏览器操作（便捷方法）"""
        return self.browser_logger.log_action(
            action=action,
            description=description,
            page=page,
            take_screenshot=True,
            metadata=metadata
        )
    
    def log_navigate(self, url: str, page=None):
        """记录导航操作"""
        return self.browser_logger.log_navigate(url, page)
    
    def log_click(self, selector: str, page=None):
        """记录点击操作"""
        return self.browser_logger.log_click(selector, page)
    
    def log_fill(self, selector: str, value: str, page=None, mask: bool = True):
        """记录填写操作"""
        return self.browser_logger.log_fill(selector, value, page, mask)
    
    def log_result(self, status: str, message: str, data: Dict[str, Any] = None):
        result = {
            "task_id": self.task_id,
            "status": status,
            "message": message,
            "timestamp": self._get_time_str(),
            "data": data or {}
        }
        
        result_file = os.path.join(self.log_dir, "results.jsonl")
        with open(result_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        self.info(f"Result logged: {status} - {message}")
        return result
    
    def log_performance_summary(self):
        """记录性能摘要"""
        summary = self.perf_metrics.get_summary()
        summary_file = os.path.join(self.perf_metrics.metrics_dir, "summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        self.info(f"Performance summary saved")
        return summary
    
    @contextmanager
    def measure_time(self, operation: str):
        """上下文管理器，用于测量代码块执行时间"""
        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            self.perf_metrics.record_operation(operation, duration_ms)
            self.debug(f"{operation} took {duration_ms:.2f}ms", action=operation)
    
    def close(self):
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n=== Task Log Ended at {self._get_time_str()} ===\n")
        
        self.log_performance_summary()
    
    @classmethod
    def get_logger(cls, task_id: str, log_dir: str = "logs") -> 'TaskLogger':
        if task_id not in cls._instances:
            cls._instances[task_id] = cls(task_id, log_dir)
        return cls._instances[task_id]
    
    @classmethod
    def close_all(cls):
        for logger in cls._instances.values():
            logger.close()
        cls._instances.clear()


class GlobalLogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.global_log_file = os.path.join(self.log_dir, f"global_{self._get_date_str()}.log")
        self._init_global_log()
    
    def _get_date_str(self) -> str:
        return datetime.now().strftime("%Y%m%d")
    
    def _get_time_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _init_global_log(self):
        if not os.path.exists(self.global_log_file):
            with open(self.global_log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Global Log Started at {self._get_time_str()} ===\n")
                f.write("=" * 60 + "\n\n")
    
    def log(self, level: LogLevel, source: str, message: str, exc_info: Optional[Exception] = None):
        timestamp = self._get_time_str()
        log_entry = f"[{timestamp}] [{level.value}] [{source}] {message}"
        
        if exc_info:
            log_entry += f"\nException: {str(exc_info)}"
            log_entry += f"\nTraceback: {traceback.format_exc()}"
        
        log_entry += "\n"
        
        with open(self.global_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"[{source}] {message}")
        
        return log_entry
    
    def debug(self, source: str, message: str):
        return self.log(LogLevel.DEBUG, source, message)
    
    def info(self, source: str, message: str):
        return self.log(LogLevel.INFO, source, message)
    
    def warning(self, source: str, message: str):
        return self.log(LogLevel.WARNING, source, message)
    
    def error(self, source: str, message: str, exc_info: Optional[Exception] = None):
        return self.log(LogLevel.ERROR, source, message, exc_info)
    
    def critical(self, source: str, message: str, exc_info: Optional[Exception] = None):
        return self.log(LogLevel.CRITICAL, source, message, exc_info)
    
    def get_task_logger(self, task_id: str) -> TaskLogger:
        return TaskLogger.get_logger(task_id, self.log_dir)


def get_global_logger() -> GlobalLogger:
    return GlobalLogger()


def get_task_logger(task_id: str) -> TaskLogger:
    return TaskLogger.get_logger(task_id)
