"""
GetNada Provider 实现
"""

import httpx
import secrets
import string
import time
from typing import List, Tuple, Optional
from .base import EmailProvider, EmailMessage, APIError


class GetNadaProvider(EmailProvider):
    DOMAINS = ["getnada.com", "dropjar.com", "fakemail.net", "emailtempo.com", "emailondeck.com"]
    
    def __init__(self, api_url: str = "https://getnada.com/api", timeout: int = 30):
        super().__init__(api_url, timeout)
        self._email = None
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.api_url, timeout=self.timeout)
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        username = secrets.token_hex(6)
        domain = self.DOMAINS[0]
        email = f"{username}@{domain}"
        self._email = email
        return email, ""
    
    def get_messages(self, email: str) -> List[EmailMessage]:
        client = self._get_client()
        try:
            username = email.split("@")[0]
            response = client.get(f"/v2/{username}/messages")
            
            if response.status_code == 200:
                data = response.json()
                messages = []
                for msg in data.get("messages", []):
                    messages.append(EmailMessage(
                        id=msg.get("id", ""),
                        from_addr=msg.get("from", ""),
                        to_addr=email,
                        subject=msg.get("subject", ""),
                        body=msg.get("body", ""),
                        html=msg.get("html", ""),
                        timestamp=msg.get("createdAt"),
                        read=False
                    ))
                return messages
            return []
        finally:
            client.close()
    
    def get_message(self, email: str, message_id: str) -> Optional[EmailMessage]:
        client = self._get_client()
        try:
            username = email.split("@")[0]
            response = client.get(f"/v2/{username}/messages/{message_id}")
            
            if response.status_code == 200:
                msg = response.json()
                return EmailMessage(
                    id=msg.get("id", ""),
                    from_addr=msg.get("from", ""),
                    to_addr=email,
                    subject=msg.get("subject", ""),
                    body=msg.get("body", ""),
                    html=msg.get("html", ""),
                    timestamp=msg.get("createdAt"),
                    read=True
                )
            return None
        finally:
            client.close()
    
    def get_verification_code(
        self,
        email: str,
        subject_contains: str = "",
        max_wait: int = 120,
        poll_interval: int = 3
    ) -> Optional[str]:
        import re
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            
            for msg in messages:
                if subject_contains and subject_contains.lower() not in msg.subject.lower():
                    continue
                
                text = msg.body or ""
                codes = re.findall(r'\b\d{6}\b', text)
                if codes:
                    return codes[0]
                codes = re.findall(r'\b\d{4}\b', text)
                if codes:
                    return codes[0]
            
            time.sleep(poll_interval)
        
        return None
    
    def get_domain(self) -> str:
        return self.DOMAINS[0]
    
    def close(self):
        self._email = None
