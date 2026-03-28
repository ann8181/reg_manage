"""
pytest 配置
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_config():
    return {
        "browser_path": "",
        "proxy": "",
        "bot_protection_wait": 12,
        "max_captcha_retries": 2,
        "concurrent_flows": 5,
        "max_tasks": 50,
        "results_base_dir": "results",
        "logs_base_dir": "logs"
    }

@pytest.fixture
def sample_task_config():
    from core.base import TaskConfig
    return TaskConfig(
        task_id="test.task",
        name="Test Task",
        description="A test task",
        module="test_module",
        class_name="TestClass",
        results_dir="results/test",
        enabled=True
    )
