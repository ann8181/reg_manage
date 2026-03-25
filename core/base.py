import os
import json
import time
import random
import string
import secrets
import re
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskConfig:
    task_id: str
    name: str
    description: str
    module: str
    class_name: str
    results_dir: str
    enabled: bool = False
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration: float = 0.0
    screenshot_path: Optional[str] = None


class BaseTask(ABC):
    def __init__(self, config: TaskConfig, global_config: Dict[str, Any]):
        self.config = config
        self.global_config = global_config
        self.results_dir = config.results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        self.result_file = os.path.join(self.results_dir, "accounts.txt")
        
        from .logger import get_task_logger
        self.logger = get_task_logger(config.task_id)
        self._browser = None
        self._page = None
    
    @abstractmethod
    def execute(self) -> TaskResult:
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        pass
    
    def save_account(self, email: str, password: str, **extra_data):
        write_header = not os.path.exists(self.result_file) or os.path.getsize(self.result_file) == 0
        with open(self.result_file, "a", encoding="utf-8") as f:
            if write_header:
                headers = ["Email", "Password"]
                for key in extra_data.keys():
                    headers.append(key)
                f.write("\t".join(headers) + "\n")
            
            values = [email, password]
            for value in extra_data.values():
                values.append(str(value))
            f.write("\t".join(values) + "\n")
        
        self.logger.info(f"Account saved: {email}")
    
    def log(self, message: str):
        self.logger.info(message)
        print(f"[{self.config.task_id}] {message}")
    
    def log_error(self, message: str, exc_info: Optional[Exception] = None):
        self.logger.error(message, exc_info)
        if self._page:
            self.take_screenshot("error")
    
    def log_warning(self, message: str):
        self.logger.warning(message)
    
    def log_debug(self, message: str):
        self.logger.debug(message)
    
    def take_screenshot(self, name: str = None) -> Optional[str]:
        if self._page:
            return self.logger.take_screenshot(name, self._page)
        return None
    
    def take_error_screenshot(self) -> Optional[str]:
        return self.logger.take_error_screenshot(page=self._page)
    
    def get_browser(self):
        if self._browser is None:
            from camoufox.sync_api import Camoufox
            launch_opts = {'headless': True}
            proxy = self.global_config.get('proxy', '')
            if proxy:
                launch_opts['proxy'] = proxy
            browser_path = self.global_config.get('browser_path', '')
            if browser_path:
                launch_opts['browser_path'] = browser_path
            self._browser = Camoufox(**launch_opts)
        return self._browser
    
    def new_page(self):
        browser = self.get_browser()
        self._page = browser.new_page()
        return self._page
    
    def close_browser(self):
        if self._browser:
            try:
                self._browser.close()
            except:
                pass
            self._browser = None
        self._page = None
    
    def generate_strong_password(self, length: int = 16) -> str:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(chars) for _ in range(length))
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and any(c.isdigit() for c in password)
                    and any(c in "!@#$%^&*" for c in password)):
                return password
    
    def random_email_username(self, length: int) -> str:
        first_char = random.choice(string.ascii_lowercase)
        other_chars = []
        for _ in range(length - 1):
            if random.random() < 0.07:
                other_chars.append(random.choice(string.digits))
            else:
                other_chars.append(random.choice(string.ascii_lowercase))
        return first_char + ''.join(other_chars)
    
    def extract_verification_code(self, text: str, length: int = 6) -> Optional[str]:
        if length == 6:
            codes = re.findall(r'\b\d{6}\b', text)
        else:
            codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None
    
    def on_task_start(self):
        self.logger.info(f"Task started: {self.config.name}")
    
    def on_task_end(self, result: TaskResult):
        self.logger.log_result(result.status.value, result.message, result.data)
        self.logger.info(f"Task ended: {result.status.value} - {result.message}")
        self.close_browser()
    
    def __del__(self):
        self.close_browser()


class EmailProvider(ABC):
    @abstractmethod
    def create_email(self) -> Tuple[str, str]:
        pass

    @abstractmethod
    def get_messages(self, email: str) -> List[Dict]:
        pass

    @abstractmethod
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        pass

    @abstractmethod
    def get_domain(self) -> str:
        pass

    def close(self):
        pass


class TempMailProvider(EmailProvider):
    pass
