import os
import sys
import time
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TaskLogger:
    _instances: Dict[str, 'TaskLogger'] = {}
    
    def __init__(self, task_id: str, log_dir: str = "logs"):
        self.task_id = task_id
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), log_dir, task_id)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.log_file = os.path.join(self.log_dir, f"{task_id}_{self._get_date_str()}.log")
        self.screenshot_dir = os.path.join(self.log_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
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
    
    def _write_log(self, level: LogLevel, message: str, exc_info: Optional[Exception] = None):
        timestamp = self._get_time_str()
        log_entry = f"[{timestamp}] [{level.value}] {message}"
        
        if exc_info:
            log_entry += f"\nException: {str(exc_info)}"
            log_entry += f"\nTraceback: {traceback.format_exc()}"
        
        log_entry += "\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            print(f"[{self.task_id}] {log_entry}", file=sys.stderr)
        else:
            print(f"[{self.task_id}] {message}")
        
        return log_entry
    
    def debug(self, message: str):
        return self._write_log(LogLevel.DEBUG, message)
    
    def info(self, message: str):
        return self._write_log(LogLevel.INFO, message)
    
    def warning(self, message: str):
        return self._write_log(LogLevel.WARNING, message)
    
    def error(self, message: str, exc_info: Optional[Exception] = None):
        return self._write_log(LogLevel.ERROR, message, exc_info)
    
    def critical(self, message: str, exc_info: Optional[Exception] = None):
        return self._write_log(LogLevel.CRITICAL, message, exc_info)
    
    def take_screenshot(self, name: str = None, page=None) -> Optional[str]:
        if name is None:
            name = f"screenshot_{self._get_time_str().replace(':', '-').replace(' ', '_')}"
        
        screenshot_path = os.path.join(self.screenshot_dir, f"{name}.png")
        
        try:
            if page:
                page.screenshot(path=screenshot_path, full_page=False)
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
    
    def close(self):
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n=== Task Log Ended at {self._get_time_str()} ===\n")
    
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
