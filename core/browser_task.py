"""
BrowserTask - 浏览器自动化任务基类
统一管理浏览器操作和日志
"""

import time
from typing import Dict, Optional, Callable
from abc import ABC
from faker import Faker
from core.base import BaseTask, TaskConfig, TaskResult, TaskStatus


class BrowserTask(BaseTask, ABC):
    """
    浏览器自动化任务基类
    提供统一的浏览器操作和日志记录
    """
    
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = ""
        self.fake = Faker()
    
    def validate(self) -> bool:
        return True
    
    def _setup_browser(self) -> Dict:
        """设置浏览器启动参数"""
        launch_opts = {'headless': True}
        
        persona_proxy = getattr(self, '_proxy', None) or self.get_proxy()
        if persona_proxy:
            proxy_host = persona_proxy.get("proxy", {}).get("host")
            proxy_port = persona_proxy.get("proxy", {}).get("port")
            proxy_protocol = persona_proxy.get("proxy", {}).get("protocol", "http")
            if proxy_host:
                proxy_auth = persona_proxy.get("proxy", {}).get("auth")
                if proxy_auth:
                    proxy_url = f"{proxy_protocol}://{proxy_auth.get('username')}:{proxy_auth.get('password')}@{proxy_host}:{proxy_port}"
                else:
                    proxy_url = f"{proxy_protocol}://{proxy_host}:{proxy_port}"
                launch_opts['proxy'] = proxy_url
        
        global_proxy = self.global_config.get('proxy', '')
        if global_proxy and not persona_proxy:
            launch_opts['proxy'] = global_proxy
        
        browser_path = self.global_config.get('browser_path', '')
        if browser_path:
            launch_opts['browser_path'] = browser_path
        
        return launch_opts
    
    def _generate_identity(self) -> Dict:
        """生成假身份信息"""
        return {
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "email": self.fake.email(),
            "username": self.fake.user_name() + str(time.time())[-3:],
            "password": self.generate_strong_password(14),
            "phone": self.fake.phone_number(),
            "address": self.fake.address(),
            "city": self.fake.city(),
            "state": self.fake.state(),
            "country": self.fake.country(),
            "postcode": self.fake.postcode(),
        }
    
    def navigate_and_screenshot(self, url: str, name: str = "navigate", timeout: int = 30000) -> bool:
        """导航到URL并截图"""
        try:
            self.log_browser_navigate(url)
            self._page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            self._page.wait_for_timeout(2000)
            self.logger.take_screenshot(f"{name}_page", self._page)
            return True
        except Exception as e:
            self.log_browser_error(f"Navigation failed: {e}")
            return False
    
    def click_and_screenshot(self, selector: str, name: str = "click", timeout: int = 10000) -> bool:
        """点击元素并截图"""
        try:
            self._page.locator(selector).wait_for(timeout=timeout)
            self.log_browser_click(selector)
            self._page.locator(selector).click()
            self._page.wait_for_timeout(1000)
            self.logger.take_screenshot(f"{name}_after", self._page)
            return True
        except Exception as e:
            self.log_browser_error(f"Click failed on {selector}: {e}")
            return False
    
    def fill_and_screenshot(self, selector: str, value: str, name: str = "fill", mask: bool = False) -> bool:
        """填写表单并截图"""
        try:
            self._page.locator(selector).wait_for(timeout=10000)
            self.log_browser_fill(selector, value, mask)
            self._page.locator(selector).fill(value)
            self._page.wait_for_timeout(500)
            self.logger.take_screenshot(f"{name}_after", self._page)
            return True
        except Exception as e:
            self.log_browser_error(f"Fill failed on {selector}: {e}")
            return False
    
    def select_and_screenshot(self, selector: str, value: str, name: str = "select") -> bool:
        """选择选项并截图"""
        try:
            self._page.locator(selector).wait_for(timeout=10000)
            self.log_browser_select(selector, value)
            self._page.locator(selector).select_option(value=value)
            self._page.wait_for_timeout(500)
            self.logger.take_screenshot(f"{name}_after", self._page)
            return True
        except Exception as e:
            self.log_browser_error(f"Select failed on {selector}: {e}")
            return False
    
    def wait_for_url(self, pattern: str, timeout: int = 30000) -> bool:
        """等待URL变化"""
        try:
            self._page.wait_for_url(pattern, timeout=timeout)
            return True
        except Exception:
            return False
    
    def wait_and_screenshot(self, timeout: int = 3000, name: str = "wait") -> bool:
        """等待并截图"""
        try:
            self._page.wait_for_timeout(timeout)
            self.logger.take_screenshot(f"{name}_after", self._page)
            return True
        except Exception as e:
            self.log_browser_error(f"Wait failed: {e}")
            return False


class EmailProviderTask(BrowserTask, ABC):
    """
    使用邮箱的注册任务基类
    提供邮箱创建和验证码获取
    """
    
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.temp_email_provider = global_config.get("temp_email_provider", "mailtm")
        self.provider = None
    
    def create_temp_email(self) -> tuple:
        """创建临时邮箱"""
        from core.providers.factory import ProviderFactory
        
        try:
            self.provider = ProviderFactory.create(self.temp_email_provider)
            email, password = self.provider.create_email()
            self.logger.info(f"Created temp email: {email} using {self.temp_email_provider}")
            return email, password
        except Exception as e:
            self.logger.error(f"Failed to create temp email: {e}")
            return "", ""
    
    def wait_for_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        """等待验证码"""
        if not self.provider:
            self.logger.error("No email provider initialized")
            return None
        
        try:
            self.logger.info(f"Waiting for verification code for {email}")
            code = self.provider.get_verification_code(email, subject_contains, max_wait)
            if code:
                self.logger.info(f"Got verification code: {code}")
            else:
                self.logger.warning(f"Timeout waiting for verification code")
            return code
        except Exception as e:
            self.logger.error(f"Failed to get verification code: {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        if self.provider:
            try:
                self.provider.close()
            except:
                pass
            self.provider = None
