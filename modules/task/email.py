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


class OutlookRegisterTask(EmailTask):
    """Outlook 注册任务"""
    
    def execute(self) -> Dict[str, Any]:
        import httpx
        from datetime import datetime
        
        browser = self.kernel.browser
        result = browser.create_browser()
        if not result:
            return {"success": False, "error": "Failed to create browser"}
        
        browser_id = result.get("browser_id")
        try:
            browser.navigate(browser_id, "https://signup.live.com/")
            browser.wait_for_selector(browser_id, "input[name='Email']", timeout=30)
            browser.fill(browser_id, "input[name='Email']", self.email)
            browser.click(browser_id, "button[type='submit']")
            browser.wait(2)
            
            return {
                "success": True,
                "email": self.email,
                "message": "Outlook registration initiated"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            browser.close_browser(browser_id)


class GmailReceiveTask(EmailTask):
    """Gmail 收取任务"""
    
    def execute(self) -> Dict[str, Any]:
        browser = self.kernel.browser
        result = browser.create_browser()
        if not result:
            return {"success": False, "error": "Failed to create browser"}
        
        browser_id = result.get("browser_id")
        try:
            browser.navigate(browser_id, "https://mail.google.com/")
            browser.wait(3)
            
            if self.params.get("login"):
                browser.fill(browser_id, "input[type='email']", self.email)
                browser.click(browser_id, "button[type='submit']")
                browser.wait(2)
            
            messages = []
            for i in range(5):
                msg_selector = f".zA:nth-child({i+1})"
                try:
                    subject = browser.text(browser_id, f"{msg_selector} .zD")
                    sender = browser.text(browser_id, f"{msg_selector} .zF")
                    if subject:
                        messages.append({"subject": subject, "from": sender})
                except Exception:
                    pass
            
            return {
                "success": True,
                "email": self.email,
                "messages": messages
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            browser.close_browser(browser_id)


class TempMailConvertTask(EmailTask):
    """TempMail 转换任务"""
    
    def execute(self) -> Dict[str, Any]:
        import httpx
        client = httpx.Client(timeout=30)
        try:
            resp = client.get("https://temp-mail.org/en/option/change/")
            import re
            email_match = re.search(r'value="([^"]+@[^"]+)"', resp.text)
            if email_match:
                return {
                    "success": True,
                    "email": email_match.group(1),
                    "provider": "tempmail"
                }
            return {"success": False, "error": "Failed to get email"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            client.close()


class MailTmReceiveTask(EmailTask):
    """Mail.tm 邮件收取任务"""
    
    def execute(self) -> Dict[str, Any]:
        from core.providers.mailtm import MailTMProvider
        
        provider = MailTMProvider()
        try:
            provider._email = self.email
            if self.params.get("token"):
                provider._token = self.params.get("token")
            
            messages = provider.get_messages(self.email)
            return {
                "success": True,
                "email": self.email,
                "count": len(messages),
                "messages": messages
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            provider.close()
