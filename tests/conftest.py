"""
pytest 配置
"""
import pytest
import sys
import os
import tempfile
from pathlib import Path

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


@pytest.fixture
def temp_dir():
    """提供临时目录，测试后自动清理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def kernel(temp_dir, monkeypatch):
    """提供隔离的 Kernel 实例"""
    from kernel import Kernel

    monkeypatch.setenv("DATA_DIR", str(temp_dir / "data"))
    monkeypatch.setenv("LOG_DIR", str(temp_dir / "logs"))

    Kernel._instance = None

    kernel_instance = Kernel()
    yield kernel_instance

    if kernel_instance._running:
        kernel_instance.stop()
    Kernel._instance = None


@pytest.fixture
def running_kernel(kernel):
    """提供已启动的 Kernel 实例"""
    kernel.start()
    yield kernel
    kernel.stop()


@pytest.fixture
def scheduler(kernel):
    """提供 SchedulerModule 实例"""
    from modules.scheduler import SchedulerModule
    scheduler = SchedulerModule(kernel)
    yield scheduler
    try:
        scheduler.stop()
    except Exception:
        pass


@pytest.fixture
def workflow(kernel):
    """提供 WorkflowModule 实例"""
    from modules.workflow import WorkflowModule

    wf_module = WorkflowModule(kernel)
    yield wf_module
    wf_module.stop()


@pytest.fixture
def account(kernel):
    """提供 AccountModule 实例"""
    from modules.account import AccountModule
    account_module = AccountModule(kernel)
    yield account_module
    account_module.stop()


@pytest.fixture
def notification(kernel):
    """提供 NotificationModule 实例"""
    from modules.notification import NotificationModule
    notif_module = NotificationModule(kernel)
    yield notif_module
    notif_module.stop()


@pytest.fixture
def sample_workflow(workflow):
    """提供示例工作流"""
    from modules.workflow import WorkflowStep

    wf = workflow.create_workflow("test_workflow", "for testing")

    step1 = WorkflowStep(id="step1", name="Start", step_type="task", task_id="task1")
    step2 = WorkflowStep(id="step2", name="End", step_type="task", task_id="task2")

    workflow.add_step(wf.id, step1)
    workflow.add_step(wf.id, step2)
    workflow.add_edge(wf.id, "step1", "step2")

    return wf
