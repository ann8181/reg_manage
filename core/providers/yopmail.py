"""
YopMail Provider 实现
"""

import httpx
import time
import re
from typing import List, Tuple, Optional
from .base import EmailProvider, EmailMessage, APIError


class YopMailProvider(EmailProvider):
    def __init__(self, api_url: str = "https://api.yopmail.com", timeout: int = 30):
        super().__init__(api_url, timeout)
        self._email = None
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.api_url, timeout=self.timeout)
    
    def create_email(self) -> Tuple[str, str]:
        import secrets
        username = secrets.token_hex(6)
        email = f"{username}@yopmail.com"
        self._email = email
        return email, ""
    
    def get_messages(self, email: str) -> List[EmailMessage]:
        username = email.split("@")[0]
        client = self._get_client()
        try:
            response = client.get(f"/mailpile.php?b={username}")
            
            if response.status_code == 200:
                html = response.text
                messages = []
                ids = re.findall(r'href="m/(.*?)"', html)
                ids = list(set(ids))
                
                for msg_id in ids[:10]:
                    msg_response = client.get(f"/mailpile.php?b={username}&m={msg_id}")
                    if msg_response.status_code == 200:
                        msg_html = msg_response.text
                        subject_match = re.search(r'<p class="subj">(.*?)</p>', msg_html)
                        from_match = re.search(r'<p class="from">(.*?)</p>', msg_html)
                        body_match = re.search(r'<p class="body">(.*?)</p>', msg_html, re.DOTALL)
                        
                        messages.append(EmailMessage(
                            id=msg_id,
                            from_addr=from_match.group(1) if from_match else "",
                            to_addr=email,
                            subject=subject_match.group(1) if subject_match else "",
                            body=body_match.group(1) if body_match else "",
                            html=None,
                            timestamp=None,
                            read=False
                        ))
                
                return messages
            return []
        finally:
            client.close()
    
    def get_message(self, email: str, message_id: str) -> Optional[EmailMessage]:
        username = email.split("@")[0]
        client = self._get_client()
        try:
            response = client.get(f"/mailpile.php?b={username}&m={message_id}")
            
            if response.status_code == 200:
                html = response.text
                subject_match = re.search(r'<p class="subj">(.*?)</p>', html)
                from_match = re.search(r'<p class="from">(.*?)</p>', html)
                body_match = re.search(r'<p class="body">(.*?)</p>', html, re.DOTALL)
                
                return EmailMessage(
                    id=message_id,
                    from_addr=from_match.group(1) if from_match else "",
                    to_addr=email,
                    subject=subject_match.group(1) if subject_match else "",
                    body=body_match.group(1) if body_match else "",
                    html=None,
                    timestamp=None,
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
        return "yopmail.com"
    
    def close(self):
        self._email = None
