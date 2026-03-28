import time
import httpx
import re
from typing import List, Dict, Optional, Callable, Tuple
from enum import Enum
from core.base import TempMailProvider


class TempMailPlusDomains(Enum):
    MAILTO_PLUS = "@mailto.plus"
    MAIL7_PLUS = "@mail7.pl"
    MAIL_7_CC = "@mail7.cc"
    PLAIN_EMAIL = "@plain.email"
    TEMP_MAIL_CC = "@temp-mail.cc"


class Letter:
    def __init__(self, msg_id: str, from_email: str, subject: str, body: str, html: str = ""):
        self.id = msg_id
        self.from_email = from_email
        self.subject = subject
        self.body = body
        self.html = html


class TempMailPlus(TempMailProvider):
    def __init__(self, api_key: str = None):
        self.base_url = "https://api.tempmail.plus/api/v1"
        self.client = httpx.Client(timeout=30.0)
        self.api_key = api_key
        self.current_email = None
        self._handlers = []
    
    def create_email(self, username: str = None, domain: TempMailPlusDomains = TempMailPlusDomains.MAILTO_PLUS) -> Tuple[str, str]:
        try:
            if username:
                self.current_email = f"{username}{domain.value}"
            else:
                import random
                import string
                username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                self.current_email = f"{username}{domain.value}"
            
            return self.current_email, ""
        except Exception as e:
            print(f"[TempMailPlus] Create email error: {e}")
        return "", ""
    
    def get_messages(self, email: str = None) -> List[Dict]:
        target = email or self.current_email
        if not target:
            return []
        
        try:
            response = self.client.get(
                f"{self.base_url}/getMessages",
                params={"email": target}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[TempMailPlus] Get messages error: {e}")
        return []
    
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                subject = msg.get("subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                
                code = self._extract_code(msg.get("body_text", "") or msg.get("body_html", ""))
                if code:
                    return code
            time.sleep(5)
        return None
    
    def _extract_code(self, text: str) -> Optional[str]:
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None
    
    def get_domain(self) -> str:
        return TempMailPlusDomains.MAILTO_PLUS.value
    
    def letter_handler(self, from_email: str = None, subject: str = None, re_subject: str = None):
        def decorator(func: Callable):
            self._handlers.append({
                "from_email": from_email,
                "subject": subject,
                "re_subject": re_subject,
                "func": func
            })
            return func
        return decorator
    
    def polling(self, email: str = None, interval: float = 5.0):
        target = email or self.current_email
        if not target:
            return
        
        while True:
            messages = self.get_messages(target)
            for msg in messages:
                for handler in self._handlers:
                    match = True
                    if handler["from_email"] and msg.get("from") != handler["from_email"]:
                        match = False
                    if handler["subject"] and msg.get("subject") != handler["subject"]:
                        match = False
                    if handler["re_subject"] and not re.match(handler["re_subject"], msg.get("subject", "")):
                        match = False
                    
                    if match:
                        letter = Letter(
                            msg_id=msg.get("id", ""),
                            from_email=msg.get("from", ""),
                            subject=msg.get("subject", ""),
                            body=msg.get("body_text", ""),
                            html=msg.get("body_html", "")
                        )
                        handler["func"](letter)
            time.sleep(interval)
    
    def close(self):
        self.client.close()


class TempMailPlusTask:
    def __init__(self, config: dict, global_config: dict):
        self.config = config
        self.global_config = global_config
        self.provider = None
    
    def execute(self) -> dict:
        try:
            self.provider = TempMailPlus()
            email, _ = self.provider.create_email()
            
            if not email:
                return {"status": "failed", "message": "Failed to create email"}
            
            return {
                "status": "success",
                "message": f"Email created: {email}",
                "data": {"email": email}
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        finally:
            if self.provider:
                self.provider.close()
