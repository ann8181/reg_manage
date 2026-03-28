import time
import httpx
import re
from typing import List, Dict, Optional, Callable, Tuple
from core.base import TempMailProvider


class Letter:
    def __init__(self, msg_id: str, from_email: str, subject: str, body: str, html: str = ""):
        self.id = msg_id
        self.from_email = from_email
        self.subject = subject
        self.body = body
        self.html = html


class TempMailLol(TempMailProvider):
    def __init__(self):
        self.base_url = "https://api.tempmail.lol"
        self.client = httpx.Client(timeout=30.0)
        self.current_email = None
        self._handlers = []
    
    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.get(f"{self.base_url}/generate")
            if response.status_code == 200:
                data = response.json()
                self.current_email = data.get("email", "")
                return self.current_email, ""
        except Exception as e:
            print(f"[TempMailLol] Create email error: {e}")
        return "", ""
    
    def get_messages(self, email: str = None) -> List[Dict]:
        target = email or self.current_email
        if not target:
            return []
        
        try:
            response = self.client.get(
                f"{self.base_url}/fetch",
                params={"email": target}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[TempMailLol] Get messages error: {e}")
        return []
    
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                subject = msg.get("subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                
                code = self._extract_code(msg.get("body", "") or msg.get("html", ""))
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
        if self.current_email and "@" in self.current_email:
            return self.current_email.split("@")[1]
        return "@tempmail.lol"
    
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
                            body=msg.get("body", ""),
                            html=msg.get("html", "")
                        )
                        handler["func"](letter)
            time.sleep(interval)
    
    def close(self):
        self.client.close()


class TempMailLolTask:
    def __init__(self, config: dict, global_config: dict):
        self.config = config
        self.global_config = global_config
        self.provider = None
    
    def execute(self) -> dict:
        try:
            self.provider = TempMailLol()
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
