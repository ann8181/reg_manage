"""
配置管理模块
支持 YAML 配置和环境变量
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    browser_path: str = ""
    proxy: str = ""
    bot_protection_wait: int = 12
    max_captcha_retries: int = 2
    concurrent_flows: int = 5
    max_tasks: int = 50
    results_base_dir: str = "results"
    logs_base_dir: str = "logs"
    temp_email_provider: str = "mailtm"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    return Settings()