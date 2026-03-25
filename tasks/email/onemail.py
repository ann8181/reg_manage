import time
import httpx
from typing import List, Tuple, Dict, Optional
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class OneSecMailProvider(TempMailProvider):
    DOMAINS = [
        "1secmail.com",
        "1secmail.org", 
        "1secmail.net",
        "secmail.io",
        "secmail.org",
        "secmail.net",
        "ezztt.com",
        "wwjtt.com",
        "muqjwq.com"
    ]
    
    def __init__(self, api_url: str = "https://www.1secmail.com"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
        self.domain = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            self.domain = random.choice(self.DOMAINS)
            response = self.client.get(
                f"{self.base_url}/mailbox/mailboxapi.php",
                params={
                    "domain": self.domain,
                    "action": "create"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.email = data.get("email", "")
                return self.email, ""
                
        except Exception as e:
            print(f"[1SecMail] Create email error: {e}")
        
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            login, domain = email.split("@")
            response = self.client.get(
                f"{self.base_url}/mailbox/mailboxapi.php",
                params={
                    "domain": domain,
                    "login": login,
                    "action": "getMessages"
                }
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[1SecMail] Get messages error: {e}")
        return []
    
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                subject = msg.get("subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                
                msg_id = msg.get("id")
                if msg_id:
                    detail = self._get_message_detail(email, msg_id)
                    if detail:
                        code = self._extract_code(detail)
                        if code:
                            return code
            time.sleep(5)
        return None
    
    def _get_message_detail(self, email: str, msg_id: str) -> Optional[str]:
        try:
            login, domain = email.split("@")
            response = self.client.get(
                f"{self.base_url}/mailbox/mailboxapi.php",
                params={
                    "domain": domain,
                    "login": login,
                    "action": "readMessage",
                    "id": msg_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("body", "")
        except:
            pass
        return None
    
    def _extract_code(self, text: str) -> Optional[str]:
        import re
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None
    
    def get_domain(self) -> str:
        return f"@{self.domain}" if self.domain else "@1secmail.com"
    
    def close(self):
        self.client.close()


import random


class OneSecMailTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("1secmail", {}).get("api_url", "https://www.1secmail.com")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = OneSecMailProvider(self.api_url)
            email, password = self.provider.create_email()
            
            if not email:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to create email"
                )
            
            self.save_account(email, password)
            self.logger.info(f"Email created: {email}")
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"1SecMail created: {email}",
                data={"email": email, "password": password}
            )
            
        except Exception as e:
            self.logger.error(f"1SecMail error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
