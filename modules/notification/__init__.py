"""
Notification Module - 通知模块
支持邮件、钉钉、飞书、Slack 等通知渠道
"""

import json
import smtplib
import asyncio
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from enum import Enum


class ChannelType(Enum):
    EMAIL = "email"
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    SLACK = "slack"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class NotificationResult:
    """通知结果"""
    def __init__(self, success: bool, channel: str, message: str = "", error: str = ""):
        self.success = success
        self.channel = channel
        self.message = message
        self.error = error
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "channel": self.channel,
            "message": self.message,
            "error": self.error
        }


class NotificationChannel(ABC):
    """通知渠道基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    def send(self, message: str, title: str = "", **kwargs) -> NotificationResult:
        """发送通知"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置"""
        pass


class EmailChannel(NotificationChannel):
    """邮件通知渠道"""
    
    def __init__(self, name: str = "email", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.smtp_host = self.config.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.smtp_user = self.config.get("smtp_user", "")
        self.smtp_password = self.config.get("smtp_password", "")
        self.from_addr = self.config.get("from_addr", self.smtp_user)
        self.use_tls = self.config.get("use_tls", True)
    
    def validate_config(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)
    
    def send(self, message: str, title: str = "", to_addrs: List[str] = None, **kwargs) -> NotificationResult:
        if not to_addrs:
            to_addrs = self.config.get("to_addrs", [])
        
        if not to_addrs:
            return NotificationResult(False, self.name, error="No recipients specified")
        
        if not self.validate_config():
            return NotificationResult(False, self.name, error="SMTP configuration incomplete")
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = title or "Notification"
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(to_addrs)
            
            text_part = MIMEText(message, "plain", "utf-8")
            html_part = MIMEText(f"<html><body><pre>{message}</pre></body></html>", "html", "utf-8")
            msg.attach(text_part)
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_addr, to_addrs, msg.as_string())
            
            return NotificationResult(True, self.name, message=f"Sent to {len(to_addrs)} recipients")
        except Exception as e:
            return NotificationResult(False, self.name, error=str(e))


class DingTalkChannel(NotificationChannel):
    """钉钉通知渠道"""
    
    def __init__(self, name: str = "dingtalk", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.webhook_url = self.config.get("webhook_url", "")
        self.secret = self.config.get("secret", "")
        self.at_mobiles = self.config.get("at_mobiles", [])
        self.at_all = self.config.get("at_all", False)
    
    def validate_config(self) -> bool:
        return bool(self.webhook_url)
    
    def _generate_sign(self) -> str:
        """生成签名"""
        if not self.secret:
            return ""
        import hmac
        import hashlib
        import base64
        import urlencode
        import time
        
        timestamp = str(int(time.time() * 1000))
        secret_enc = self.secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")
        return urlencode({"sign": sign, "timestamp": timestamp})
    
    def send(self, message: str, title: str = "", **kwargs) -> NotificationResult:
        if not self.validate_config():
            return NotificationResult(False, self.name, error="Webhook URL not configured")
        
        try:
            import requests
            
            sign_params = self._generate_sign()
            url = f"{self.webhook_url}?{sign_params}" if sign_params else self.webhook_url
            
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n{message}" if title else message
                },
                "at": {
                    "atMobiles": self.at_mobiles,
                    "isAtAll": self.at_all
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return NotificationResult(True, self.name, message="Sent successfully")
            else:
                return NotificationResult(False, self.name, error=result.get("errmsg", "Unknown error"))
        except Exception as e:
            return NotificationResult(False, self.name, error=str(e))


class FeishuChannel(NotificationChannel):
    """飞书通知渠道"""
    
    def __init__(self, name: str = "feishu", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.webhook_url = self.config.get("webhook_url", "")
    
    def validate_config(self) -> bool:
        return bool(self.webhook_url)
    
    def send(self, message: str, title: str = "", **kwargs) -> NotificationResult:
        if not self.validate_config():
            return NotificationResult(False, self.name, error="Webhook URL not configured")
        
        try:
            import requests
            
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"{title}\n{message}" if title else message
                }
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            result = response.json()
            
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                return NotificationResult(True, self.name, message="Sent successfully")
            else:
                return NotificationResult(False, self.name, error=result.get("msg", "Unknown error"))
        except Exception as e:
            return NotificationResult(False, self.name, error=str(e))


class SlackChannel(NotificationChannel):
    """Slack 通知渠道"""
    
    def __init__(self, name: str = "slack", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.webhook_url = self.config.get("webhook_url", "")
        self.channel = self.config.get("channel", "")
        self.username = self.config.get("username", "Notification Bot")
        self.icon_emoji = self.config.get("icon_emoji", ":bell:")
    
    def validate_config(self) -> bool:
        return bool(self.webhook_url)
    
    def send(self, message: str, title: str = "", **kwargs) -> NotificationResult:
        if not self.validate_config():
            return NotificationResult(False, self.name, error="Webhook URL not configured")
        
        try:
            import requests
            
            payload = {
                "text": f"*{title}*\n{message}" if title else message,
                "username": self.username,
                "icon_emoji": self.icon_emoji
            }
            if self.channel:
                payload["channel"] = self.channel
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return NotificationResult(True, self.name, message="Sent successfully")
            else:
                return NotificationResult(False, self.name, error=f"HTTP {response.status_code}")
        except Exception as e:
            return NotificationResult(False, self.name, error=str(e))


class WebhookChannel(NotificationChannel):
    """通用 Webhook 通知渠道"""
    
    def __init__(self, name: str = "webhook", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.webhook_url = self.config.get("webhook_url", "")
        self.method = self.config.get("method", "POST")
        self.headers = self.config.get("headers", {"Content-Type": "application/json"})
        self.secret = self.config.get("secret", "")
    
    def validate_config(self) -> bool:
        return bool(self.webhook_url)
    
    def send(self, message: str, title: str = "", **kwargs) -> NotificationResult:
        if not self.validate_config():
            return NotificationResult(False, self.name, error="Webhook URL not configured")
        
        try:
            import requests
            
            payload = {
                "title": title,
                "message": message,
                "timestamp": kwargs.get("timestamp", ""),
                "extra": kwargs.get("extra", {})
            }
            
            headers = self.headers.copy()
            if self.secret:
                import hmac
                import hashlib
                sign = hmac.new(self.secret.encode(), json.dumps(payload).encode(), hashlib.sha256).hexdigest()
                headers["X-Signature"] = sign
            
            response = requests.request(
                self.method,
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.ok:
                return NotificationResult(True, self.name, message=f"HTTP {response.status_code}")
            else:
                return NotificationResult(False, self.name, error=f"HTTP {response.status_code}")
        except Exception as e:
            return NotificationResult(False, self.name, error=str(e))


class NotificationModule:
    """
    通知模块
    统一管理多种通知渠道
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.channels: Dict[str, NotificationChannel] = {}
        self.default_channel: Optional[str] = None
        self.logger = kernel.get_logger("notification")
        self.logger.info("NotificationModule initialized")
    
    def register_channel(self, channel: NotificationChannel, set_default: bool = False) -> bool:
        """注册通知渠道"""
        if not channel.validate_config():
            self.logger.warning(f"Channel {channel.name} configuration invalid")
            return False
        
        self.channels[channel.name] = channel
        if set_default or not self.default_channel:
            self.default_channel = channel.name
        
        self.logger.info(f"Channel registered: {channel.name}")
        return True
    
    def register_email(
        self,
        name: str = "email",
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_addr: str = "",
        to_addrs: List[str] = None,
        set_default: bool = False
    ) -> bool:
        """注册邮件渠道"""
        config = {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_user": smtp_user,
            "smtp_password": smtp_password,
            "from_addr": from_addr,
            "to_addrs": to_addrs or []
        }
        channel = EmailChannel(name, config)
        return self.register_channel(channel, set_default)
    
    def register_dingtalk(
        self,
        name: str = "dingtalk",
        webhook_url: str = "",
        secret: str = "",
        at_mobiles: List[str] = None,
        at_all: bool = False,
        set_default: bool = False
    ) -> bool:
        """注册钉钉渠道"""
        config = {
            "webhook_url": webhook_url,
            "secret": secret,
            "at_mobiles": at_mobiles or [],
            "at_all": at_all
        }
        channel = DingTalkChannel(name, config)
        return self.register_channel(channel, set_default)
    
    def register_feishu(
        self,
        name: str = "feishu",
        webhook_url: str = "",
        set_default: bool = False
    ) -> bool:
        """注册飞书渠道"""
        config = {"webhook_url": webhook_url}
        channel = FeishuChannel(name, config)
        return self.register_channel(channel, set_default)
    
    def register_slack(
        self,
        name: str = "slack",
        webhook_url: str = "",
        channel: str = "",
        username: str = "Notification Bot",
        icon_emoji: str = ":bell:",
        set_default: bool = False
    ) -> bool:
        """注册 Slack 渠道"""
        config = {
            "webhook_url": webhook_url,
            "channel": channel,
            "username": username,
            "icon_emoji": icon_emoji
        }
        channel = SlackChannel(name, config)
        return self.register_channel(channel, set_default)
    
    def register_webhook(
        self,
        name: str = "webhook",
        webhook_url: str = "",
        method: str = "POST",
        headers: Dict = None,
        secret: str = "",
        set_default: bool = False
    ) -> bool:
        """注册通用 Webhook 渠道"""
        config = {
            "webhook_url": webhook_url,
            "method": method,
            "headers": headers or {"Content-Type": "application/json"},
            "secret": secret
        }
        channel = WebhookChannel(name, config)
        return self.register_channel(channel, set_default)
    
    def send(
        self,
        message: str,
        title: str = "",
        channel_name: str = None,
        **kwargs
    ) -> NotificationResult:
        """发送通知"""
        channel_name = channel_name or self.default_channel
        
        if not channel_name:
            return NotificationResult(False, "unknown", error="No channel configured")
        
        channel = self.channels.get(channel_name)
        if not channel:
            return NotificationResult(False, channel_name, error=f"Channel {channel_name} not found")
        
        result = channel.send(message, title, **kwargs)
        
        if result.success:
            self.logger.info(f"Notification sent via {channel_name}")
        else:
            self.logger.error(f"Notification failed via {channel_name}: {result.error}")
        
        return result
    
    def send_all(
        self,
        message: str,
        title: str = "",
        **kwargs
    ) -> List[NotificationResult]:
        """向所有渠道发送通知"""
        results = []
        for name in self.channels:
            result = self.send(message, title, name, **kwargs)
            results.append(result)
        return results
    
    def get_channel(self, name: str) -> Optional[NotificationChannel]:
        """获取渠道"""
        return self.channels.get(name)
    
    def list_channels(self) -> List[str]:
        """列出所有渠道"""
        return list(self.channels.keys())
    
    def remove_channel(self, name: str) -> bool:
        """移除渠道"""
        if name in self.channels:
            del self.channels[name]
            if self.default_channel == name:
                self.default_channel = next(iter(self.channels.keys()), None)
            self.logger.info(f"Channel removed: {name}")
            return True
        return False
    
    def stop(self):
        """停止模块"""
        self.logger.info("NotificationModule stopped")
