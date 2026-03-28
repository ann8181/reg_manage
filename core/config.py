"""
Config Module - 配置管理
"""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """应用配置"""
    
    browser_path: str = field(default="")
    proxy: str = field(default="")
    bot_protection_wait: int = 12
    max_captcha_retries: int = 2
    concurrent_flows: int = 5
    max_tasks: int = 50
    results_base_dir: str = "results"
    logs_base_dir: str = "logs"
    database_path: str = "data/kernel.db"
    
    def __post_init__(self):
        for key, value in os.environ.items():
            if key.startswith("AUTO_REG_"):
                config_key = key[9:].lower()
                if hasattr(self, config_key):
                    current_value = getattr(self, config_key)
                    if isinstance(current_value, int):
                        setattr(self, config_key, int(value))
                    elif isinstance(current_value, bool):
                        setattr(self, config_key, value.lower() in ("true", "1", "yes"))
                    else:
                        setattr(self, config_key, value)
    
    def get(self, key: str, default=None):
        return getattr(self, key, default)
    
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
