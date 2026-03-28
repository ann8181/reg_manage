"""
Audit 模块测试
"""
import pytest
import time
from modules.audit import (
    AuditModule,
    AuditLog,
    AuditLevel,
    AuditAction
)


class TestAuditLog:
    """测试审计日志"""

    def test_create_log(self):
        """测试创建日志"""
        log = AuditLog(
            id="1",
            action=AuditAction.CREATE.value,
            resource="task",
            resource_id="task-123"
        )
        
        assert log.id == "1"
        assert log.action == AuditAction.CREATE.value

    def test_to_dict(self):
        """测试转字典"""
        log = AuditLog(id="1", action=AuditAction.CREATE.value)
        
        d = log.to_dict()
        
        assert d["id"] == "1"
        assert d["action"] == "create"


class TestAuditModule:
    """测试审计模块"""

    def test_log(self, audit):
        """测试记录日志"""
        log_id = audit.log(
            action="test",
            resource="test_resource",
            user_id="user-1"
        )
        
        assert log_id is not None
        assert len(audit._logs) == 1

    def test_log_create(self, audit):
        """测试记录创建操作"""
        log_id = audit.log_create(
            resource="task",
            resource_id="task-1",
            user_id="user-1"
        )
        
        assert audit._logs[-1].action == AuditAction.CREATE.value

    def test_log_read(self, audit):
        """测试记录读取操作"""
        log_id = audit.log_read(
            resource="task",
            resource_id="task-1",
            user_id="user-1"
        )
        
        assert audit._logs[-1].action == AuditAction.READ.value

    def test_log_update(self, audit):
        """测试记录更新操作"""
        log_id = audit.log_update(
            resource="task",
            resource_id="task-1",
            user_id="user-1"
        )
        
        assert audit._logs[-1].action == AuditAction.UPDATE.value

    def test_log_delete(self, audit):
        """测试记录删除操作"""
        log_id = audit.log_delete(
            resource="task",
            resource_id="task-1",
            user_id="user-1"
        )
        
        assert audit._logs[-1].action == AuditAction.DELETE.value

    def test_log_execute(self, audit):
        """测试记录执行操作"""
        log_id = audit.log_execute(
            resource="workflow",
            resource_id="wf-1",
            user_id="user-1"
        )
        
        assert audit._logs[-1].action == AuditAction.EXECUTE.value

    def test_log_login(self, audit):
        """测试记录登录"""
        log_id = audit.log_login(user_id="user-1", user_name="testuser")
        
        assert audit._logs[-1].action == AuditAction.LOGIN.value

    def test_log_logout(self, audit):
        """测试记录登出"""
        log_id = audit.log_logout(user_id="user-1", user_name="testuser")
        
        assert audit._logs[-1].action == AuditAction.LOGOUT.value

    def test_query_by_action(self, audit):
        """测试按动作查询"""
        audit.log(action="create", resource="r1")
        audit.log(action="read", resource="r1")
        audit.log(action="create", resource="r1")
        
        results = audit.query(action="create")
        
        assert len(results) == 2

    def test_query_by_resource(self, audit):
        """测试按资源查询"""
        audit.log(action="create", resource="task")
        audit.log(action="create", resource="workflow")
        audit.log(action="create", resource="task")
        
        results = audit.query(resource="task")
        
        assert len(results) == 2

    def test_query_by_user(self, audit):
        """测试按用户查询"""
        audit.log(action="create", resource="r1", user_id="user-1")
        audit.log(action="create", resource="r1", user_id="user-2")
        
        results = audit.query(user_id="user-1")
        
        assert len(results) == 1

    def test_query_by_level(self, audit):
        """测试按级别查询"""
        audit.log(action="a1", level=AuditLevel.INFO.value)
        audit.log(action="a2", level=AuditLevel.ERROR.value)
        
        results = audit.query(level=AuditLevel.ERROR.value)
        
        assert len(results) == 1

    def test_query_with_time_range(self, audit):
        """测试时间范围查询"""
        now = time.time()
        audit.log(action="old", resource="r1")
        audit._logs[-1].timestamp = now - 100
        audit.log(action="new", resource="r1")
        audit._logs[-1].timestamp = now
        
        results = audit.query(start_time=now - 10)
        
        assert len(results) == 1

    def test_query_with_limit(self, audit):
        """测试限制返回数量"""
        for i in range(10):
            audit.log(action="test", resource=f"r{i}")
        
        results = audit.query(limit=5)
        
        assert len(results) == 5

    def test_get_log(self, audit):
        """测试获取单条日志"""
        log_id = audit.log(action="test", resource="r1")
        
        log = audit.get_log(log_id)
        
        assert log is not None
        assert log.id == log_id

    def test_count(self, audit):
        """测试统计数量"""
        audit.log(action="create", resource="r1")
        audit.log(action="create", resource="r1")
        audit.log(action="read", resource="r1")
        
        count = audit.count(action="create")
        
        assert count == 2

    def test_get_stats(self, audit):
        """测试获取统计"""
        audit.log(action="create", resource="task")
        audit.log(action="read", resource="task")
        audit.log(action="create", resource="workflow")
        
        stats = audit.get_stats()
        
        assert stats["total"] == 3
        assert stats["by_action"]["create"] == 2

    def test_clear_all(self, audit):
        """测试清空所有日志"""
        audit.log(action="test", resource="r1")
        audit.log(action="test", resource="r1")
        
        count = audit.clear()
        
        assert count == 2
        assert len(audit._logs) == 0

    def test_clear_before_timestamp(self, audit):
        """测试清除指定时间前的日志"""
        now = time.time()
        audit.log(action="old", resource="r1")
        audit._logs[-1].timestamp = now - 100
        audit.log(action="new", resource="r1")
        audit._logs[-1].timestamp = now
        
        count = audit.clear(before_timestamp=now - 10)
        
        assert count == 1
        assert len(audit._logs) == 1


class TestAuditModuleKernelIntegration:
    """测试 AuditModule 与 Kernel 集成"""

    def test_kernel_audit_property(self, running_kernel):
        """测试 kernel.audit 属性"""
        assert running_kernel.audit is not None
        assert running_kernel.audit.__class__.__name__ == "AuditModule"
