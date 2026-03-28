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


class GetnadaProvider(Provider):
    """Getnada Provider - 临时邮箱服务"""
    
    def __init__(self, api_url: str = "https://getnada.com"):
        super().__init__("getnada", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        username = secrets.token_hex(6)
        self._email = f"{username}@getnada.com"
        return self._email, "temp1234"
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            resp = self._client.get(f"{self.api_url}/api/v1/messages/{email}")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("messages", [])
        except Exception:
            pass
        return []
    
    def get_verification_code(self, email: str, **kwargs) -> Optional[str]:
        import time
        import re
        
        max_wait = kwargs.get("max_wait", 120)
        poll_interval = kwargs.get("poll_interval", 5)
        
        start = time.time()
        while time.time() - start < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                body = msg.get("text", "")
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


class TenMinuteMailProvider(Provider):
    """10MinuteMail Provider"""
    
    def __init__(self, api_url: str = "https://10minutemail.com"):
        super().__init__("10minutemail", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            resp = self._client.post(f"{self.api_url}/address/api/react")
            if resp.status_code == 200:
                data = resp.json()
                self._email = data.get("email", "")
                return self._email, data.get("password", "")
        except Exception:
            pass
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            resp = self._client.get(f"{self.api_url}/mailbox/api/messages/{email}")
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []
    
    def get_verification_code(self, email: str, **kwargs) -> Optional[str]:
        import time
        import re
        
        max_wait = kwargs.get("max_wait", 120)
        poll_interval = kwargs.get("poll_interval", 5)
        
        start = time.time()
        while time.time() - start < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                body = msg.get("body_text", "")
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


class YopMailProvider(Provider):
    """YopMail Provider - 一次性临时邮箱"""
    
    def __init__(self, api_url: str = "https://yopmail.com"):
        super().__init__("yopmail", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
        self._inbox_id = ""
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        username = secrets.token_hex(6)
        self._email = f"{username}@yopmail.com"
        self._inbox_id = username
        return self._email, ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            inbox_id = email.split("@")[0]
            resp = self._client.get(
                f"{self.api_url}/mailbox.php?b={inbox_id}",
                headers={"Accept": "text/html"}
            )
            if resp.status_code == 200:
                import re
                mail_ids = re.findall(r'mail=(\w+)&r=', resp.text)
                messages = []
                for mid in mail_ids[:10]:
                    messages.append({"id": mid, "subject": "New message"})
                return messages
        except Exception:
            pass
        return []
    
    def close(self):
        self._client.close()


class TempMailProvider(Provider):
    """TempMail Provider"""
    
    def __init__(self, api_url: str = "https://temp-mail.org"):
        super().__init__("tempmail", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            resp = self._client.get(f"{self.api_url}/en/option/change/")
            if resp.status_code == 200:
                import re
                email_match = re.search(r'value="([^"]+@[^"]+)"', resp.text)
                if email_match:
                    self._email = email_match.group(1)
                    return self._email, ""
        except Exception:
            pass
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            resp = self._client.get(f"{self.api_url}/en/option/mailbox/{email}/")
            if resp.status_code == 200:
                import re
                messages = []
                subjects = re.findall(r'class="mail-subject">([^<]+)<', resp.text)
                for i, subject in enumerate(subjects[:10]):
                    messages.append({"id": str(i), "subject": subject.strip()})
                return messages
        except Exception:
            pass
        return []
    
    def close(self):
        self._client.close()


class ThrowAwayMailProvider(Provider):
    """ThrowAwayMail Provider - 一次性临时邮箱"""
    
    def __init__(self, api_url: str = "https://www.throwawaymail.com"):
        super().__init__("throwawaymail", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
        self._session_id = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            resp = self._client.get(f"{self.api_url}/email-generator")
            if resp.status_code == 200:
                import re
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', resp.text)
                if email_match:
                    self._email = email_match.group(1)
                    return self._email, ""
        except Exception:
            pass
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            resp = self._client.get(f"{self.api_url}/email/{email.split('@')[0]}")
            if resp.status_code == 200:
                import re
                messages = []
                subjects = re.findall(r'<td[^>]*class="[^"]*subject[^"]*"[^>]*>([^<]+)<', resp.text)
                for i, subject in enumerate(subjects[:10]):
                    messages.append({"id": str(i), "subject": subject.strip()})
                return messages
        except Exception:
            pass
        return []
    
    def close(self):
        self._client.close()


class MaildropProvider(Provider):
    """Maildrop Provider - 临时邮箱"""
    
    def __init__(self, api_url: str = "https://api.maildrop.cc"):
        super().__init__("maildrop", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        username = secrets.token_hex(8)
        self._email = f"{username}@maildrop.cc"
        return self._email, ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            inbox_id = email.split("@")[0]
            resp = self._client.get(f"{self.api_url}/api/v1/{inbox_id}", headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("messages", [])
        except Exception:
            pass
        return []
    
    def close(self):
        self._client.close()


class FakeEmailGeneratorProvider(Provider):
    """FakeEmailGenerator Provider"""
    
    def __init__(self, api_url: str = "https://www.fakemailgenerator.com"):
        super().__init__("fakemail", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            resp = self._client.get(f"{self.api_url}/")
            if resp.status_code == 200:
                import re
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', resp.text)
                if email_match:
                    self._email = email_match.group(1)
                    return self._email, ""
        except Exception:
            pass
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        return []
    
    def close(self):
        self._client.close()


class MintEmailProvider(Provider):
    """MintEmail Provider - 临时邮箱"""
    
    def __init__(self, api_url: str = "https://www.mintemail.com"):
        super().__init__("mintemail", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            resp = self._client.get(f"{self.api_url}/")
            if resp.status_code == 200:
                import re
                email_match = re.search(r'value="([^"]+@mintemail\.com)"', resp.text)
                if email_match:
                    self._email = email_match.group(1)
                    return self._email, ""
        except Exception:
            pass
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        return []
    
    def close(self):
        self._client.close()


class AirMailProvider(Provider):
    """AirMail Provider - 临时邮箱"""
    
    def __init__(self, api_url: str = "https://airmail.email"):
        super().__init__("airmail", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        username = secrets.token_hex(8)
        self._email = f"{username}@airmail.email"
        return self._email, ""
    
    def get_messages(self, email: str) -> List[Dict]:
        return []
    
    def close(self):
        self._client.close()


class MailnesiaProvider(Provider):
    """Mailnesia Provider - 临时邮箱"""
    
    def __init__(self, api_url: str = "https://mailnesia.com"):
        super().__init__("mailnesia", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        username = secrets.token_hex(8)
        self._email = f"{username}@mailnesia.com"
        return self._email, ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            inbox_id = email.split("@")[0]
            resp = self._client.get(f"{self.api_url}/mailbox/{inbox_id}")
            if resp.status_code == 200:
                import re
                messages = []
                subjects = re.findall(r'<td[^>]*class="[^"]*subject[^"]*"[^>]*>([^<]+)<', resp.text)
                for i, subject in enumerate(subjects[:10]):
                    messages.append({"id": str(i), "subject": subject.strip()})
                return messages
        except Exception:
            pass
        return []
    
    def close(self):
        self._client.close()


class TempInboxProvider(Provider):
    """TempInbox Provider - 临时邮箱"""
    
    def __init__(self, api_url: str = "https://tempinbox.com"):
        super().__init__("tempinbox", api_url)
        self._client = httpx.Client(timeout=self.timeout)
        self._email = ""
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        username = secrets.token_hex(8)
        self._email = f"{username}@tempinbox.com"
        return self._email, ""
    
    def get_messages(self, email: str) -> List[Dict]:
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
        "getnada": GetnadaProvider,
        "10minutemail": TenMinuteMailProvider,
        "yopmail": YopMailProvider,
        "tempmail": TempMailProvider,
        "throwawaymail": ThrowAwayMailProvider,
        "maildrop": MaildropProvider,
        "fakemail": FakeEmailGeneratorProvider,
        "mintemail": MintEmailProvider,
        "airmail": AirMailProvider,
        "mailnesia": MailnesiaProvider,
        "tempinbox": TempInboxProvider,
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
