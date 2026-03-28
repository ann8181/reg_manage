"""
Kernel 配置和生命周期测试
"""
import pytest
import json


class TestKernelConfig:
    """测试配置管理"""

    def test_config_property(self, running_kernel):
        """测试 config 属性返回副本"""
        config = running_kernel.config
        
        assert isinstance(config, dict)

    def test_get_config_exists(self, running_kernel):
        """测试获取存在的配置项"""
        running_kernel._config["test_key"] = "test_value"
        
        value = running_kernel.get_config("test_key")
        
        assert value == "test_value"

    def test_get_config_default(self, running_kernel):
        """测试获取不存在的配置项返回默认值"""
        value = running_kernel.get_config("nonexistent", "default")
        
        assert value == "default"

    def test_get_config_no_default(self, running_kernel):
        """测试获取不存在的配置项无默认值"""
        value = running_kernel.get_config("nonexistent")
        
        assert value is None

    def test_set_config(self, running_kernel):
        """测试设置配置项"""
        running_kernel.set_config("new_key", "new_value")
        
        assert running_kernel.get_config("new_key") == "new_value"


class TestKernelLifecycle:
    """测试生命周期"""

    def test_start_not_running(self, kernel):
        """测试启动内核"""
        kernel.start()
        
        assert kernel._running is True
        kernel.stop()

    def test_start_already_running(self, running_kernel):
        """测试重复启动"""
        initial_running = running_kernel._running
        
        running_kernel.start()
        
        assert running_kernel._running is initial_running

    def test_stop_running(self, running_kernel):
        """测试停止运行中的内核"""
        running_kernel.stop()
        
        assert running_kernel._running is False

    def test_stop_not_running(self, kernel):
        """测试停止未启动的内核"""
        kernel.stop()
        
        assert kernel._running is False


class TestKernelSession:
    """测试数据库会话"""

    def test_get_session(self, running_kernel):
        """测试获取数据库会话"""
        session = running_kernel.get_session()
        
        assert session is not None
        session.close()

    def test_get_logger(self, running_kernel):
        """测试获取日志器"""
        logger = running_kernel.get_logger()
        
        assert logger is not None
        
        named_logger = running_kernel.get_logger("test")
        assert named_logger.name == "kernel.test"
