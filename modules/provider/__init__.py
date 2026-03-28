"""
Provider Module - 服务提供商模块
统一管理所有Provider (邮箱、短信等)
"""

import httpx
from typing import Dict, List, Optional, Tuple


class Provider:
    """Provider基类"""
    
    def __init__(self, name: str, api_url: str = ""):
        self.name = name
        self.api_url = api_url
        self.timeout = 30
    
    def create_email(self) -> Tuple[str, str]:
        raise NotImplementedError
    
    def get_messages(self, email: str) -> List[Dict]:
        raise NotImplementedError
    
    def get_verification_code(self, email: str, **kwargs) -> Optional[str]:
        raise NotImplementedError
    
    def close(self):
        pass


class MailTmProvider(Provider):
    """Mail.tm Provider"""
    
    def __init__(self, api_url: str = "https://api.mail.tm"):
        super().__init__("mailtm", api_url)
        self._token = None
        self._client = httpx.Client(timeout=self.timeout)
    
    def create_email(self) -> Tuple[str, str]:
        # 获取域名
        resp = self._client.get(f"{self.api_url}/domains")
        if resp.status_code != 200:
            return "", ""
        
        domains = resp.json().get("hydra:member", [])
        if not domains:
            return "", ""
        
        domain = domains[0].get("domain", "mail.tm")
        import secrets
        username = secrets.token_hex(6)
        email = f"{username}@{domain}"
        password = "temppass123"
        
        # 注册
        reg_resp = self._client.post(f"{self.api_url}/accounts", json={
            "address": email,
            "password": password
        })
        
        if reg_resp.status_code != 201:
            return "", ""
        
        # 获取token
        token_resp = self._client.post(f"{self.api_url}/token", json={
            "address": email,
            "password": password
        })
        
        if token_resp.status_code == 200:
            self._token = token_resp.json().get("token")
        
        return email, password
    
    def get_messages(self, email: str) -> List[Dict]:
        if not self._token:
            return []
        
        headers = {"Authorization": f"Bearer {self._token}"}
        resp = self._client.get(f"{self.api_url}/messages", headers=headers)
        
        if resp.status_code == 200:
            return resp.json().get("hydra:member", [])
        return []
    
    def get_verification_code(self, email: str, **kwargs) -> Optional[str]:
        import time
        import re
        
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
                    detail_resp = self._client.get(
                        f"{self.api_url}/messages/{msg_id}",
                        headers={"Authorization": f"Bearer {self._token}"}
                    )
                    if detail_resp.status_code == 200:
                        body = detail_resp.json().get("text", "")
                        codes = re.findall(r'\b\d{6}\b', body)
                        if codes:
                            return codes[0]
                        codes = re.findall(r'\b\d{4}\b', body)
                        if codes:
                            return codes[0]
            
            time.sleep(poll_interval)
        
        return None
    
    def close(self):
        self._client.close()


class GuerrillaMailProvider(Provider):
    """GuerrillaMail Provider"""
    
    def __init__(self, api_url: str = "https://api.guerrillamail.com"):
        super().__init__("guerrilla", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._token = ""
    
    def create_email(self) -> Tuple[str, str]:
        resp = self._client.get(f"{self.api_url}/api/v2/get_email_address/")
        if resp.status_code == 200:
            data = resp.json()
            self._email = data.get("email_addr", "")
            self._token = data.get("token", "")
            return self._email, ""
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        if not self._token:
            return []
        
        resp = self._client.get(
            f"{self.api_url}/api/v2/get_email_list/",
            params={"token": self._token, "seq": 0}
        )
        
        if resp.status_code == 200:
            return resp.json().get("list", [])
        return []
    
    def close(self):
        self._client.close()


class ProviderModule:
    """
    Provider模块
    统一管理所有服务提供商
    """
    
    _providers = {
        "mailtm": MailTmProvider,
        "guerrilla": GuerrillaMailProvider,
    }
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.active_providers: Dict[str, Provider] = {}
        self.logger = kernel.get_logger("provider")
        self.logger.info("ProviderModule initialized")
    
    def register_provider(self, name: str, provider_class):
        """注册Provider"""
        self._providers[name] = provider_class
        self.logger.info(f"Provider registered: {name}")
    
    def get_provider(self, name: str) -> Provider:
        """获取Provider实例"""
        if name not in self.active_providers:
            provider_class = self._providers.get(name)
            if provider_class:
                self.active_providers[name] = provider_class()
        return self.active_providers.get(name)
    
    def create_email(self, provider: str = "mailtm") -> Tuple[str, str]:
        """创建临时邮箱"""
        p = self.get_provider(provider)
        if p:
            return p.create_email()
        return "", ""
    
    def get_messages(self, email: str, provider: str = "mailtm") -> List[Dict]:
        """获取邮件"""
        p = self.get_provider(provider)
        if p:
            return p.get_messages(email)
        return []
    
    def get_verification_code(self, email: str, provider: str = "mailtm", **kwargs) -> Optional[str]:
        """获取验证码"""
        p = self.get_provider(provider)
        if p:
            return p.get_verification_code(email, **kwargs)
        return None
    
    def list_providers(self) -> List[str]:
        """列出所有Provider"""
        return list(self._providers.keys())
    
    def close_all(self):
        """关闭所有Provider"""
        for p in self.active_providers.values():
            p.close()
        self.active_providers.clear()
    
    def stop(self):
        self.close_all()
        self.logger.info("ProviderModule stopped")
