import time
import httpx
from typing import List, Tuple, Dict, Optional
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class FakeMailProvider(TempMailProvider):
    def __init__(self, api_url: str = "https://fakemail.top"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
        self.token = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.get(f"{self.base_url}/api/temp-mail")
            if response.status_code == 200:
                data = response.json()
                self.email = data.get("email", "")
                self.token = data.get("token", "")
                return self.email, ""
        except Exception as e:
            print(f"[FakeMail] Create email error: {e}")
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            response = self.client.get(
                f"{self.base_url}/api/temp-mail/{email}"
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[FakeMail] Get messages error: {e}")
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
        return "@fakemail.top"
    
    def close(self):
        self.client.close()


class FakeMailTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("fakemail", {}).get("api_url", "https://fakemail.top")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = FakeMailProvider(self.api_url)
            email, password = self.provider.create_email()
            
            if not email:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to create email"
                )
            
            self.save_account(email, password)
            self.logger.info(f"FakeMail created: {email}")
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"FakeMail created: {email}",
                data={"email": email, "password": password}
            )
            
        except Exception as e:
            self.logger.error(f"FakeMail error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
