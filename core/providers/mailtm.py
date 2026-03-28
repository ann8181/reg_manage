"""
Mail.tm Provider 实现
"""

import httpx
from typing import List, Tuple, Optional
from .base import (
    EmailProvider,
    EmailMessage,
    APIError,
    RateLimitError,
    EmailNotFoundError
)


class MailTmProvider(EmailProvider):
    DOMAINS_CACHE = None
    
    def __init__(self, api_url: str = "https://api.mail.tm", timeout: int = 30):
        super().__init__(api_url, timeout)
        self._token = None
        self._email = None
        self._password = None
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.api_url, timeout=self.timeout)
    
    def _get_domains(self) -> List[str]:
        if self.DOMAINS_CACHE is None:
            client = self._get_client()
            try:
                response = client.get("/domains")
                if response.status_code == 200:
                    data = response.json()
                    self.DOMAINS_CACHE = [
                        d["domain"] for d in data.get("hydra:member", [])
                        if d.get("isActive")
                    ]
                else:
                    self.DOMAINS_CACHE = ["mail.tm", "coolmail.tm"]
            except Exception:
                self.DOMAINS_CACHE = ["mail.tm", "coolmail.tm"]
            finally:
                client.close()
        return self.DOMAINS_CACHE
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        import string
        
        domains = self._get_domains()
        if not domains:
            raise APIError("MailTm", 500, "No domains available")
        
        domain = domains[0]
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        username = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        email = f"{username}@{domain}"
        
        client = self._get_client()
        try:
            response = client.post("/accounts", json={
                "address": email,
                "password": password
            })
            
            if response.status_code == 201:
                self._email = email
                self._password = password
                
                token_response = client.post("/token", json={
                    "address": email,
                    "password": password
                })
                
                if token_response.status_code == 200:
                    self._token = token_response.json().get("token")
                
                return email, password
            else:
                error = response.json().get("hydra:description", "Unknown error")
                raise APIError("MailTm", response.status_code, error)
        finally:
            client.close()
    
    def get_messages(self, email: str) -> List[EmailMessage]:
        if not self._token:
            self._reauthorize(email)
        
        client = self._get_client()
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        
        try:
            response = client.get("/messages", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                messages = []
                for msg in data.get("hydra:member", []):
                    messages.append(EmailMessage(
                        id=msg.get("id", ""),
                        from_addr=msg.get("from", {}).get("address", ""),
                        to_addr=msg.get("to", [{}])[0].get("address", email),
                        subject=msg.get("subject", ""),
                        body=msg.get("intro", ""),
                        html=msg.get("html", [None])[0] if msg.get("html") else None,
                        timestamp=msg.get("createdAt"),
                        read=msg.get("seen", False)
                    ))
                return messages
            elif response.status_code == 401:
                self._reauthorize(email)
                return self.get_messages(email)
            else:
                raise APIError("MailTm", response.status_code, response.text)
        finally:
            client.close()
    
    def get_message(self, email: str, message_id: str) -> Optional[EmailMessage]:
        if not self._token:
            self._reauthorize(email)
        
        client = self._get_client()
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        
        try:
            response = client.get(f"/messages/{message_id}", headers=headers)
            
            if response.status_code == 200:
                msg = response.json()
                return EmailMessage(
                    id=msg.get("id", ""),
                    from_addr=msg.get("from", {}).get("address", ""),
                    to_addr=msg.get("to", [{}])[0].get("address", email),
                    subject=msg.get("subject", ""),
                    body=msg.get("text", ""),
                    html=msg.get("html", [None])[0] if msg.get("html") else None,
                    timestamp=msg.get("createdAt"),
                    read=msg.get("seen", False)
                )
            elif response.status_code == 404:
                return None
            else:
                raise APIError("MailTm", response.status_code, response.text)
        finally:
            client.close()
    
    def get_verification_code(
        self,
        email: str,
        subject_contains: str = "",
        max_wait: int = 120,
        poll_interval: int = 3
    ) -> Optional[str]:
        import time
        import re
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            
            for msg in messages:
                if subject_contains and subject_contains.lower() not in msg.subject.lower():
                    continue
                
                text = msg.body or ""
                if msg.html:
                    text += re.sub('<[^>]+>', '', msg.html)
                
                codes = re.findall(r'\b\d{6}\b', text)
                if codes:
                    return codes[0]
                
                codes = re.findall(r'\b\d{4}\b', text)
                if codes:
                    return codes[0]
            
            time.sleep(poll_interval)
        
        return None
    
    def get_domain(self) -> str:
        domains = self._get_domains()
        return domains[0] if domains else "mail.tm"
    
    def _reauthorize(self, email: str = None):
        if not email and self._email:
            email = self._email
        if not email or not self._password:
            raise EmailNotFoundError("No email/password available for reauthorization")
        
        client = self._get_client()
        try:
            response = client.post("/token", json={
                "address": email,
                "password": self._password
            })
            
            if response.status_code == 200:
                self._token = response.json().get("token")
            else:
                raise APIError("MailTm", response.status_code, "Reauthorization failed")
        finally:
            client.close()
    
    def close(self):
        self._token = None
        self._email = None
        self._password = None
