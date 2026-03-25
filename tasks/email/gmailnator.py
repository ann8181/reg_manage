import time
import httpx
from typing import List, Tuple, Dict, Optional
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class GmailnatorProvider(TempMailProvider):
    API_URL = "https://www.gmailnator.com/api/v1"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
        self.session_id = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.post(
                self.API_URL,
                json={
                    "action": "generate",
                    "mail_type": ["@gmailnator.com", "@gmail.com", "@googlemail.com"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.email = data.get("email", "")
                self.session_id = data.get("session_id", "")
                return self.email, ""
                
        except Exception as e:
            print(f"[Gmailnator] Create email error: {e}")
        
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            response = self.client.post(
                self.API_URL,
                json={
                    "action": "fetch",
                    "session_id": self.session_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("messages", [])
        except Exception as e:
            print(f"[Gmailnator] Get messages error: {e}")
        return []
    
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                subject = msg.get("subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                
                body = msg.get("body", "")
                if body:
                    code = self._extract_code(body)
                    if code:
                        return code
            time.sleep(5)
        return None
    
    def _extract_code(self, text: str) -> Optional[str]:
        import re
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None
    
    def get_domain(self) -> str:
        return "@gmailnator.com"
    
    def close(self):
        self.client.close()


class GmailnatorTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = GmailnatorProvider()
            email, password = self.provider.create_email()
            
            if not email:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to create email"
                )
            
            self.save_account(email, password)
            self.logger.info(f"Gmailnator created: {email}")
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"Gmailnator created: {email}",
                data={"email": email, "password": password}
            )
            
        except Exception as e:
            self.logger.error(f"Gmailnator error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
