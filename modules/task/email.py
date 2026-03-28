"""
Email Task Module - 邮件任务模块
提供邮件相关任务实现
"""

from typing import Dict, Any, Optional


class EmailTask:
    """邮件任务基类"""
    
    def __init__(self, kernel, **kwargs):
        self.kernel = kernel
        self.params = kwargs
        self.email = kwargs.get("email", "")
        self.provider = kwargs.get("provider", "mailtm")
    
    def execute(self) -> Dict[str, Any]:
        """执行任务"""
        raise NotImplementedError


class CreateEmailTask(EmailTask):
    """创建临时邮箱任务"""
    
    def execute(self) -> Dict[str, Any]:
        email, password = self.kernel.provider.create_email(self.provider)
        return {
            "success": bool(email),
            "email": email,
            "password": password,
            "provider": self.provider
        }


class GetMessagesTask(EmailTask):
    """获取邮件任务"""
    
    def execute(self) -> Dict[str, Any]:
        messages = self.kernel.provider.get_messages(self.email, self.provider)
        return {
            "success": True,
            "email": self.email,
            "count": len(messages),
            "messages": messages
        }


class GetVerificationCodeTask(EmailTask):
    """获取验证码任务"""
    
    def execute(self) -> Dict[str, Any]:
        subject = self.params.get("subject_contains", "")
        max_wait = self.params.get("max_wait", 120)
        
        code = self.kernel.provider.get_verification_code(
            self.email,
            self.provider,
            subject_contains=subject,
            max_wait=max_wait
        )
        
        return {
            "success": bool(code),
            "code": code,
            "email": self.email
        }
