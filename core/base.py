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


class BaseTask(ABC):
    def __init__(self, config: TaskConfig, global_config: Dict[str, Any]):
        self.config = config
        self.global_config = global_config
        self.results_dir = config.results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        self.result_file = os.path.join(self.results_dir, "accounts.txt")
        
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
    
    def log(self, message: str):
        print(f"[{self.config.task_id}] {message}")
    
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
