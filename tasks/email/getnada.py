import time
import httpx
from typing import List, Tuple, Dict, Optional
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class GetNadaProvider(TempMailProvider):
    def __init__(self, api_url: str = "https://getnada.com/api"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.get(f"{self.base_url}/v2/domains")
            if response.status_code != 200:
                return "", ""
            
            domains = response.json()
            if not domains:
                return "", ""
            
            domain = domains[0]
            
            username = f"user_{int(time.time())}"
            self.email = f"{username}@{domain}"
            return self.email, ""
            
        except Exception as e:
            print(f"[GetNada] Create email error: {e}")
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            address = email.split("@")[0]
            response = self.client.get(
                f"{self.base_url}/v2/messages/{address}",
                params={"domain": email.split("@")[1]}
            )
            if response.status_code == 200:
                return response.json().get("messages", [])
        except Exception as e:
            print(f"[GetNada] Get messages error: {e}")
        return []
    
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                subject = msg.get("subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                
                msg_id = msg.get("uid")
                if msg_id:
                    detail = self._get_message_detail(email, msg_id)
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
    
    def _get_message_detail(self, email: str, msg_id: str) -> Optional[str]:
        try:
            address = email.split("@")[0]
            response = self.client.get(
                f"{self.base_url}/v2/message/{address}/{msg_id}"
            )
            if response.status_code == 200:
                return response.json().get("body", "")
        except:
            pass
        return None
    
    def get_domain(self) -> str:
        try:
            response = self.client.get(f"{self.base_url}/v2/domains")
            if response.status_code == 200:
                domains = response.json()
                if domains:
                    return f"@{domains[0]}"
        except:
            pass
        return "@getnada.com"
    
    def close(self):
        self.client.close()


class GetNadaTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("getnada", {}).get("api_url", "https://getnada.com/api")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = GetNadaProvider(self.api_url)
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
