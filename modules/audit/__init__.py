"""
Audit Module - 操作审计模块
记录和查询系统操作日志，支持合规审计需求
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class AuditLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    OTHER = "other"


@dataclass
class AuditLog:
    """审计日志条目"""
    id: str
    timestamp: float = field(default_factory=time.time)
    level: str = AuditLevel.INFO.value
    action: str = AuditAction.OTHER.value
    resource: str = ""
    resource_id: str = ""
    user_id: str = ""
    user_name: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    status: str = "success"
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "level": self.level,
            "action": self.action,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message
        }


class AuditModule:
    """
    操作审计模块
    记录系统操作日志，支持查询和过滤
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self._logs: List[AuditLog] = []
        self._max_logs = 10000
        self._logger = kernel.get_logger("audit")
        self._logger.info("AuditModule initialized")
    
    def log(
        self,
        action: str,
        resource: str = "",
        resource_id: str = "",
        level: str = AuditLevel.INFO.value,
        user_id: str = "",
        user_name: str = "",
        details: Dict[str, Any] = None,
        ip_address: str = "",
        user_agent: str = "",
        status: str = "success",
        error_message: str = ""
    ) -> str:
        """记录审计日志"""
        log_id = str(uuid.uuid4())[:8]
        
        audit_log = AuditLog(
            id=log_id,
            level=level,
            action=action,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            user_name=user_name,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        
        self._logs.append(audit_log)
        
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
        
        self._logger.info(f"Audit log: {action} {resource} by {user_name}")
        
        return log_id
    
    def log_create(
        self,
        resource: str,
        resource_id: str,
        user_id: str = "",
        user_name: str = "",
        details: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """记录创建操作"""
        return self.log(
            action=AuditAction.CREATE.value,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            user_name=user_name,
            details=details,
            **kwargs
        )
    
    def log_read(
        self,
        resource: str,
        resource_id: str,
        user_id: str = "",
        user_name: str = "",
        details: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """记录读取操作"""
        return self.log(
            action=AuditAction.READ.value,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            user_name=user_name,
            details=details,
            **kwargs
        )
    
    def log_update(
        self,
        resource: str,
        resource_id: str,
        user_id: str = "",
        user_name: str = "",
        details: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """记录更新操作"""
        return self.log(
            action=AuditAction.UPDATE.value,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            user_name=user_name,
            details=details,
            **kwargs
        )
    
    def log_delete(
        self,
        resource: str,
        resource_id: str,
        user_id: str = "",
        user_name: str = "",
        details: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """记录删除操作"""
        return self.log(
            action=AuditAction.DELETE.value,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            user_name=user_name,
            details=details,
            **kwargs
        )
    
    def log_execute(
        self,
        resource: str,
        resource_id: str = "",
        user_id: str = "",
        user_name: str = "",
        details: Dict[str, Any] = None,
        status: str = "success",
        error_message: str = "",
        **kwargs
    ) -> str:
        """记录执行操作"""
        return self.log(
            action=AuditAction.EXECUTE.value,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            user_name=user_name,
            details=details,
            status=status,
            error_message=error_message,
            **kwargs
        )
    
    def log_login(
        self,
        user_id: str,
        user_name: str,
        status: str = "success",
        error_message: str = "",
        **kwargs
    ) -> str:
        """记录登录"""
        return self.log(
            action=AuditAction.LOGIN.value,
            resource="auth",
            user_id=user_id,
            user_name=user_name,
            status=status,
            error_message=error_message,
            **kwargs
        )
    
    def log_logout(
        self,
        user_id: str,
        user_name: str,
        **kwargs
    ) -> str:
        """记录登出"""
        return self.log(
            action=AuditAction.LOGOUT.value,
            resource="auth",
            user_id=user_id,
            user_name=user_name,
            **kwargs
        )
    
    def query(
        self,
        action: str = None,
        resource: str = None,
        resource_id: str = None,
        user_id: str = None,
        user_name: str = None,
        level: str = None,
        status: str = None,
        start_time: float = None,
        end_time: float = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """查询审计日志"""
        results = self._logs
        
        if action:
            results = [r for r in results if r.action == action]
        
        if resource:
            results = [r for r in results if r.resource == resource]
        
        if resource_id:
            results = [r for r in results if r.resource_id == resource_id]
        
        if user_id:
            results = [r for r in results if r.user_id == user_id]
        
        if user_name:
            results = [r for r in results if r.user_name == user_name]
        
        if level:
            results = [r for r in results if r.level == level]
        
        if status:
            results = [r for r in results if r.status == status]
        
        if start_time:
            results = [r for r in results if r.timestamp >= start_time]
        
        if end_time:
            results = [r for r in results if r.timestamp <= end_time]
        
        return results[offset:offset + limit]
    
    def get_log(self, log_id: str) -> Optional[AuditLog]:
        """获取单条日志"""
        for log in self._logs:
            if log.id == log_id:
                return log
        return None
    
    def count(
        self,
        action: str = None,
        resource: str = None,
        user_id: str = None,
        level: str = None,
        status: str = None,
        start_time: float = None,
        end_time: float = None
    ) -> int:
        """统计日志数量"""
        logs = self.query(
            action=action,
            resource=resource,
            user_id=user_id,
            level=level,
            status=status,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        return len(logs)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._logs)
        
        by_action = {}
        by_resource = {}
        by_level = {}
        by_status = {}
        
        for log in self._logs:
            by_action[log.action] = by_action.get(log.action, 0) + 1
            by_resource[log.resource] = by_resource.get(log.resource, 0) + 1
            by_level[log.level] = by_level.get(log.level, 0) + 1
            by_status[log.status] = by_status.get(log.status, 0) + 1
        
        return {
            "total": total,
            "by_action": by_action,
            "by_resource": by_resource,
            "by_level": by_level,
            "by_status": by_status
        }
    
    def clear(self, before_timestamp: float = None) -> int:
        """清除日志"""
        if before_timestamp:
            original_count = len(self._logs)
            self._logs = [l for l in self._logs if l.timestamp >= before_timestamp]
            return original_count - len(self._logs)
        else:
            count = len(self._logs)
            self._logs.clear()
            return count
    
    def export(self, format: str = "json") -> str:
        """导出日志"""
        if format == "json":
            import json
            return json.dumps([log.to_dict() for log in self._logs], indent=2)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            if self._logs:
                writer = csv.DictWriter(output, fieldnames=self._logs[0].to_dict().keys())
                writer.writeheader()
                for log in self._logs:
                    writer.writerow(log.to_dict())
            return output.getvalue()
        return ""
    
    def stop(self):
        """停止模块"""
        self._logger.info("AuditModule stopped")
