"""
MailTm Provider - Mail.tm 邮箱服务提供商
"""

import secrets
import re
import time
from typing import Tuple, List, Dict, Optional

from .factory import BaseProvider


class MailTmProvider(BaseProvider):
    """Mail.tm 临时邮箱提供商"""
    
    def __init__(self, api_url: str = "https://api.mail.tm"):
        super().__init__("mailtm", api_url)
        self._email = None
        self._token = None
    
    def create_email(self) -> Tuple[str, str]:
        """创建临时邮箱"""
        try:
            resp = self._client.get(f"{self.api_url}/domains")
            if resp.status_code != 200:
                return "", ""
            
            domains = resp.json().get("hydra:member", [])
            if not domains:
                return "", ""
            
            domain = domains[0].get("domain", "mail.tm")
            username = secrets.token_hex(6)
            email = f"{username}@{domain}"
            password = "temppass123"
            
            reg_resp = self._client.post(f"{self.api_url}/accounts", json={
                "address": email,
                "password": password
            })
            
            if reg_resp.status_code != 201:
                return "", ""
            
            token_resp = self._client.post(f"{self.api_url}/token", json={
                "address": email,
                "password": password
            })
            
            if token_resp.status_code == 200:
                self._token = token_resp.json().get("token")
                self._email = email
            
            return email, password
        except Exception:
            return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        """获取邮件列表"""
        if not self._token:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self._token}"}
            resp = self._client.get(f"{self.api_url}/messages", headers=headers)
            
            if resp.status_code == 200:
                return resp.json().get("hydra:member", [])
        except Exception:
            pass
        return []
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """获取单封邮件详情"""
        if not self._token:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self._token}"}
            resp = self._client.get(
                f"{self.api_url}/messages/{message_id}",
                headers=headers
            )
            
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None
    
    def get_verification_code(self, email: str, **kwargs) -> Optional[str]:
        """获取验证码"""
        max_wait = kwargs.get("max_wait", 120)
        poll_interval = kwargs.get("poll_interval", 5)
        subject_contains = kwargs.get("subject_contains", "")
        
        start = time.time()
        while time.time() - start < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                if subject_contains and subject_contains.lower() not in msg.get("subject", "").lower():
                    continue
                
                msg_id = msg.get("id")
                if msg_id:
                    detail = self.get_message(msg_id)
                    if detail:
                        body = detail.get("text", "")
                        codes = re.findall(r'\b\d{6}\b', body)
                        if codes:
                            return codes[0]
                        codes = re.findall(r'\b\d{4}\b', body)
                        if codes:
                            return codes[0]
            
            time.sleep(poll_interval)
        
        return None
    
    def close(self):
        """关闭连接"""
        self._client.close()
