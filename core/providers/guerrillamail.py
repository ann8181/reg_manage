"""
GuerrillaMail Provider 实现
"""

import httpx
import secrets
import string
import time
from typing import List, Tuple, Optional
from .base import EmailProvider, EmailMessage, APIError


class GuerrillaMailProvider(EmailProvider):
    def __init__(self, api_url: str = "https://api.guerrillamail.com", timeout: int = 30):
        super().__init__(api_url, timeout)
        self._email = None
        self._password = None
        self._session_id = None
        self._alias = None
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.api_url, timeout=self.timeout)
    
    def create_email(self) -> Tuple[str, str]:
        client = self.get_client()
        try:
            response = client.get("/php/fetch.php", params={
                "lang": "en",
                "check": "getemailaddress"
            })
            
            if response.status_code == 200:
                data = response.json()
                email = data.get("email_addr", "")
                if email:
                    self._email = email
                    self._session_id = data.get("sid_token", "")
                    return email, ""
            
            raise APIError("GuerrillaMail", response.status_code, "Failed to create email")
        finally:
            client.close()
    
    def get_messages(self, email: str) -> List[EmailMessage]:
        client = self.get_client()
        try:
            response = client.get("/php/fetch.php", params={
                "lang": "en",
                "check": "getinbox",
                "sid_token": self._session_id or ""
            })
            
            if response.status_code == 200:
                data = response.json()
                messages = []
                for msg in data.get("list", []):
                    messages.append(EmailMessage(
                        id=str(msg.get("mail_id", "")),
                        from_addr=msg.get("mail_from", ""),
                        to_addr=email,
                        subject=msg.get("mail_subject", ""),
                        body=msg.get("mail_excerpt", ""),
                        html=None,
                        timestamp=msg.get("mail_timestamp"),
                        read=False
                    ))
                return messages
            return []
        finally:
            client.close()
    
    def get_message(self, email: str, message_id: str) -> Optional[EmailMessage]:
        client = self.get_client()
        try:
            response = client.get("/php/fetch.php", params={
                "lang": "en",
                "check": "read_message",
                "sid_token": self._session_id or "",
                "mail_id": message_id
            })
            
            if response.status_code == 200:
                data = response.json()
                msg = data.get("mail_body", {})
                return EmailMessage(
                    id=str(msg.get("mail_id", "")),
                    from_addr=msg.get("mail_from", ""),
                    to_addr=email,
                    subject=msg.get("mail_subject", ""),
                    body=msg.get("mail_body", ""),
                    html=None,
                    timestamp=msg.get("mail_timestamp"),
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
                
                text = msg.body
                codes = re.findall(r'\b\d{6}\b', text)
                if codes:
                    return codes[0]
                codes = re.findall(r'\b\d{4}\b', text)
                if codes:
                    return codes[0]
            
            time.sleep(poll_interval)
        
        return None
    
    def get_domain(self) -> str:
        return "guerrillamail.com"
    
    def get_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.api_url, timeout=self.timeout)
    
    def close(self):
        self._email = None
        self._session_id = None
