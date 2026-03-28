"""
Kernel 单例测试
"""
import pytest
from kernel import Kernel


class TestKernelSingleton:
    """测试 Kernel 单例模式"""

    def test_singleton_same_instance(self, temp_dir, monkeypatch):
        """测试多次实例化返回同一对象"""
        Kernel._instance = None
        
        monkeypatch.setenv("DATA_DIR", str(temp_dir / "data"))
        monkeypatch.setenv("LOG_DIR", str(temp_dir / "logs"))
        
        k1 = Kernel()
        k2 = Kernel()
        
        assert k1 is k2

    def test_init_called_once(self, temp_dir, monkeypatch):
        """测试 __init__ 只执行一次"""
        Kernel._instance = None
        
        monkeypatch.setenv("DATA_DIR", str(temp_dir / "data"))
        monkeypatch.setenv("LOG_DIR", str(temp_dir / "logs"))
        
        kernel = Kernel()
        kernel.start()
        
        assert kernel._initialized is True


class TestKernelModuleManagement:
    """测试 Kernel 模块管理"""

    def test_register_module(self, running_kernel):
        """测试注册模块"""
        class DummyModule:
            pass
        
        dummy = DummyModule()
        running_kernel.register_module("dummy", dummy)
        
        assert running_kernel.get_module("dummy") is dummy

    def test_get_module_not_found(self, running_kernel):
        """测试获取不存在的模块"""
        result = running_kernel.get_module("nonexistent")
        assert result is None

    def test_module_has_kernel_reference(self, running_kernel):
        """测试模块能访问 kernel 引用"""
        class DummyModule:
            kernel = None
        
        dummy = DummyModule()
        running_kernel.register_module("ref_test", dummy)
        
        assert dummy.kernel is running_kernel


class TestKernelProperties:
    """测试 Kernel 属性访问器"""

    def test_scheduler_property(self, running_kernel):
        """测试 scheduler 属性"""
        scheduler = running_kernel.scheduler
        assert scheduler is not None
        assert scheduler.__class__.__name__ == "SchedulerModule"

    def test_browser_property(self, running_kernel):
        """测试 browser 属性"""
        browser = running_kernel.browser
        assert browser is not None

    def test_workflow_property(self, running_kernel):
        """测试 workflow 属性"""
        workflow = running_kernel.workflow
        assert workflow is not None
        assert workflow.__class__.__name__ == "WorkflowModule"

    def test_user_property(self, running_kernel):
        """测试 user 属性"""
        user = running_kernel.user
        assert user is not None

    def test_provider_property(self, running_kernel):
        """测试 provider 属性"""
        provider = running_kernel.provider
        assert provider is not None

    def test_account_property_returns_module(self, running_kernel):
        """测试 account 属性返回 AccountModule"""
        account = running_kernel.account
        assert account is not None
        assert account.__class__.__name__ == "AccountModule"
