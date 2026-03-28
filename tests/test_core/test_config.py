"""
配置测试
"""
import pytest
from core.config import Settings

class TestSettings:
    def test_default_settings(self):
        settings = Settings()
        assert settings.concurrent_flows == 5
        assert settings.max_tasks == 50
        assert settings.results_base_dir == "results"
    
    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("CONCURRENT_FLOWS", "10")
        settings = Settings()
        assert settings.concurrent_flows == 10
