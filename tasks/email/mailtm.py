import time
import httpx
from typing import List, Tuple, Dict, Optional
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class MailTmProvider(TempMailProvider):
    def __init__(self, api_url: str = "https://api.mail.tm"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.token = None
        self.current_email = None
    
    def create_email(self) -> Tuple[str, str]:
        try:
            domain_response = self.client.get(f"{self.base_url}/domains")
            if domain_response.status_code != 200:
                return "", ""
            
            domains = domain_response.json().get("hydra:member", [])
            if not domains:
                return "", ""
            
            domain = domains[0].get("domain", "")
            
            from random import random
            username = f"user_{int(time.time())}_{int(random() * 10000)}"
            password = "temppass123"
            
            self.current_email = f"{username}@{domain}"
            
            register_response = self.client.post(
                f"{self.base_url}/accounts",
                json={
                    "address": self.current_email,
                    "password": password
                }
            )
            
            if register_response.status_code != 201:
                return "", ""
            
            token_response = self.client.post(
                f"{self.base_url}/token",
                json={
                    "address": self.current_email,
                    "password": password
                }
            )
            
            if token_response.status_code == 200:
                self.token = token_response.json().get("token")
            
            return self.current_email, password
            
        except Exception as e:
            print(f"[MailTm] Create email error: {e}")
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        if not self.token:
            return []
        
        try:
            response = self.client.get(
                f"{self.base_url}/messages",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("hydra:member", [])
        except Exception as e:
            print(f"[MailTm] Get messages error: {e}")
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
                    detail = self._get_message_detail(msg_id)
                    if detail:
                        code = self._extract_code(detail)
                        if code:
                            return code
            time.sleep(5)
        return None
    
    def _get_message_detail(self, msg_id: str) -> Optional[str]:
        try:
            response = self.client.get(
                f"{self.base_url}/messages/{msg_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code == 200:
                return response.json().get("text", "")
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
        try:
            response = self.client.get(f"{self.base_url}/domains")
            if response.status_code == 200:
                domains = response.json().get("hydra:member", [])
                if domains:
                    return f"@{domains[0].get('domain', '')}"
        except:
            pass
        return "@mail.tm"
    
    def close(self):
        self.client.close()


class MailTmTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("mailtm", {}).get("api_url", "https://api.mail.tm")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = MailTmProvider(self.api_url)
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
