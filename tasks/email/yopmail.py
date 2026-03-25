import time
import httpx
from typing import List, Tuple, Dict, Optional
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class YopMailProvider(TempMailProvider):
    def __init__(self, api_url: str = "https://api.yopmail.com"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
    
    def create_email(self) -> Tuple[str, str]:
        try:
            username = f"user_{int(time.time())}"
            self.email = f"{username}@yopmail.com"
            return self.email, ""
        except Exception as e:
            print(f"[YopMail] Create email error: {e}")
        return "", ""
    
    def get_messages(self, email: str) -> List[Dict]:
        try:
            address = email.split("@")[0]
            response = self.client.get(
                f"{self.base_url}/inbox/?b={address}",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                import re
                messages = []
                pattern = r'<div class="messagerie_ligne_01"[^>]*>(.*?)</div>'
                matches = re.findall(pattern, response.text, re.DOTALL)
                for i, match in enumerate(matches):
                    messages.append({
                        "subject": match.strip(),
                        "id": f"msg_{i}"
                    })
                return messages
        except Exception as e:
            print(f"[YopMail] Get messages error: {e}")
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
                    detail = self._get_message_detail(email)
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
    
    def _get_message_detail(self, email: str) -> Optional[str]:
        try:
            address = email.split("@")[0]
            response = self.client.get(
                f"{self.base_url}/mail/{address}?押={int(time.time())}"
            )
            if response.status_code == 200:
                import re
                body_pattern = r'<div id="mailcontent"[^>]*>(.*?)</div>'
                match = re.search(body_pattern, response.text, re.DOTALL)
                if match:
                    return match.group(1)
        except:
            pass
        return None
    
    def get_domain(self) -> str:
        return "@yopmail.com"
    
    def close(self):
        self.client.close()


class YopMailTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("yopmail", {}).get("api_url", "https://api.yopmail.com")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = YopMailProvider(self.api_url)
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
