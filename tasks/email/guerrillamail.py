import time
import httpx
from typing import List, Tuple, Dict, Optional
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class GuerrillaMailProvider(TempMailProvider):
    def __init__(self, api_url: str = "https://api.guerrillamail.com"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
        self.token = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.get(f"{self.base_url}/api/v2/get_email_address/")
            if response.status_code == 200:
                data = response.json()
                self.email = data.get("email_addr", "")
                self.token = data.get("token", "")
                return self.email, ""
        except Exception as e:
            print(f"[GuerrillaMail] Create email error: {e}")
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            if not self.token:
                return []
            response = self.client.get(
                f"{self.base_url}/api/v2/get_email_list/",
                params={"token": self.token, "seq": 0}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("list", [])
        except Exception as e:
            print(f"[GuerrillaMail] Get messages error: {e}")
        return []
    
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                subject = msg.get("mail_subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                mail_id = msg.get("mail_id")
                if mail_id:
                    detail = self._get_email_detail(mail_id)
                    if detail:
                        import re
                        codes = re.findall(r'\b\d{6}\b', detail)
                        if codes:
                            return codes[0]
                        codes = re.findall(r'\b\d{4}\b', detail)
                        if codes:
                            return codes[0]
            time.sleep(5)
        return None
    
    def _get_email_detail(self, mail_id: int) -> Optional[str]:
        try:
            response = self.client.get(
                f"{self.base_url}/api/v2/fetch_email/",
                params={"token": self.token, "id": mail_id}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("mail_body", "")
        except:
            pass
        return None
    
    def get_domain(self) -> str:
        return "@guerrillamailblock.com"
    
    def close(self):
        self.client.close()


class GuerrillaMailTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("guerrillamail", {}).get("api_url", "https://api.guerrillamail.com")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = GuerrillaMailProvider(self.api_url)
            email, password = self.provider.create_email()
            
            if not email:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to create email"
                )
            
            self.save_account(email, password)
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"Email created: {email}",
                data={"email": email, "password": password}
            )
            
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
