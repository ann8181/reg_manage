import time
import httpx
from typing import List, Tuple, Dict, Optional
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class TempMailOrgProvider(TempMailProvider):
    def __init__(self, api_url: str = "https://temp-mail.org/en/api/v2"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
        self.token = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.get(f"{self.base_url}/new/domaintest")
            if response.status_code == 200:
                data = response.json()
                self.email = data.get("mail", "")
                self.token = data.get("token", "")
                return self.email, ""
        except Exception as e:
            print(f"[TempMailOrg] Create email error: {e}")
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            response = self.client.get(
                f"{self.base_url}/get inbox",
                params={"token": self.token}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
        except Exception as e:
            print(f"[TempMailOrg] Get messages error: {e}")
        return []
    
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                subject = msg.get("mail_subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                
                mail_text = msg.get("mail_text", "")
                if mail_text:
                    code = self._extract_code(mail_text)
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
        return "@temp-mail.org"
    
    def close(self):
        self.client.close()


class TempMailOrgTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("tempmailorg", {}).get("api_url", "https://temp-mail.org/en/api/v2")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = TempMailOrgProvider(self.api_url)
            email, password = self.provider.create_email()
            
            if not email:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to create email"
                )
            
            self.save_account(email, password)
            self.logger.info(f"TempMailOrg created: {email}")
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"TempMailOrg created: {email}",
                data={"email": email, "password": password}
            )
            
        except Exception as e:
            self.logger.error(f"TempMailOrg error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
