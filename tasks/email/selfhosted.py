import time
import httpx
from typing import List, Dict, Optional
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class SelfHostedMailProvider:
    def __init__(self, api_url: str = "http://localhost:8025"):
        self.api_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
    
    def create_email(self, username: str = None) -> tuple:
        try:
            if username is None:
                import random
                username = f"user_{int(time.time())}_{random.randint(1000, 9999)}"
            
            self.email = f"{username}@localhost"
            return self.email, ""
        except Exception as e:
            print(f"[SelfHostedMail] Create email error: {e}")
        return "", ""
    
    def get_messages(self) -> List[Dict]:
        try:
            response = self.client.get(f"{self.api_url}/api/v2/messages")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[SelfHostedMail] Get messages error: {e}")
        return []
    
    def get_verification_code(self, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages()
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
    
    def close(self):
        self.client.close()


class SelfHostedMailTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("selfhosted", {}).get("api_url", "http://localhost:8025")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = SelfHostedMailProvider(self.api_url)
            email, password = self.provider.create_email()
            
            if not email:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to create email - self-hosted server may not be running"
                )
            
            self.save_account(email, password, api_url=self.api_url)
            self.logger.info(f"SelfHostedMail created: {email}")
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"SelfHostedMail created: {email}",
                data={"email": email, "api_url": self.api_url}
            )
            
        except Exception as e:
            self.logger.error(f"SelfHostedMail error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
