"""
Kernel 钩子系统测试
"""
import pytest


class TestKernelHooks:
    """测试钩子系统"""

    def test_add_hook(self, running_kernel):
        """测试添加钩子"""
        calls = []
        
        def callback(*args):
            calls.append(args)
        
        running_kernel.add_hook("test_event", callback)
        
        assert "test_event" in running_kernel._hooks
        assert callback in running_kernel._hooks["test_event"]

    def test_trigger_hook_success(self, running_kernel):
        """测试触发钩子成功"""
        calls = []
        
        def callback(*args):
            calls.append(args)
        
        running_kernel.add_hook("test", callback)
        running_kernel._trigger_hook("test", "arg1", "arg2")
        
        assert len(calls) == 1
        assert calls[0] == ("arg1", "arg2")

    def test_trigger_hook_error(self, running_kernel, caplog):
        """测试钩子执行出错"""
        def failing_callback(*args):
            raise ValueError("Hook failed")
        
        running_kernel.add_hook("failing", failing_callback)
        running_kernel._trigger_hook("failing")
        
        assert "Hook failing error" in caplog.text

    def test_trigger_hook_no_hooks(self, running_kernel):
        """测试触发不存在的钩子"""
        running_kernel._trigger_hook("nonexistent")


class TestKernelEvents:
    """测试事件系统"""

    def test_on_event(self, running_kernel):
        """测试监听事件"""
        running_kernel.on("data_event", lambda d: None)
        
        assert "data_event" in running_kernel._events

    def test_emit_event(self, running_kernel):
        """测试发射事件"""
        received = []
        
        def listener(data):
            received.append(data)
        
        running_kernel.on("test_event", listener)
        running_kernel.emit("test_event", {"key": "value"})
        
        assert len(received) == 1
        assert received[0]["key"] == "value"

    def test_emit_event_multiple_listeners(self, running_kernel):
        """测试多个监听器"""
        received1 = []
        received2 = []
        
        running_kernel.on("multi", lambda d: received1.append(d))
        running_kernel.on("multi", lambda d: received2.append(d))
        
        running_kernel.emit("multi", "data")
        
        assert len(received1) == 1
        assert len(received2) == 1

    def test_emit_event_error_handling(self, running_kernel, caplog):
        """测试事件处理错误"""
        def failing_listener(data):
            raise ValueError("Listener failed")
        
        running_kernel.on("failing", failing_listener)
        running_kernel.emit("failing", {})
        
        assert "Event failing error" in caplog.text
