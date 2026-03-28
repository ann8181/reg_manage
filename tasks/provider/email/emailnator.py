import time
import httpx
import random
import string
import json
import re
from typing import List, Dict, Optional, Tuple
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class EmailnatorProvider(TempMailProvider):
    def __init__(self, api_url: str = "https://emailnator.com"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
        self.session_id = ""

    def _random_string(self, length: int = 10) -> str:
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.post(
                f"{self.base_url}/generate-email",
                json={
                    "email": {
                        "emailType": "random",
                        "domain": "emailnator.com"
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.email = data.get("email", {}).get("email", "")
                self.session_id = data.get("session_id", "")
                return self.email, ""

            return "", ""

        except Exception as e:
            print(f"[Emailnator] Create email error: {e}")
        return "", ""

    def get_messages(self, email: str) -> List[Dict]:
        try:
            response = self.client.post(
                f"{self.base_url}/getMessages",
                json={
                    "session_id": self.session_id
                }
            )

            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                result = []
                for msg in messages:
                    result.append({
                        "id": msg.get("id", ""),
                        "subject": msg.get("subject", ""),
                        "from": msg.get("from", ""),
                        "date": msg.get("date", "")
                    })
                return result

        except Exception as e:
            print(f"[Emailnator] Get messages error: {e}")
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
            response = self.client.post(
                f"{self.base_url}/getMessage",
                json={
                    "session_id": self.session_id,
                    "message_id": msg_id
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("text", "") or data.get("body", "")

        except Exception as e:
            print(f"[Emailnator] Get message detail error: {e}")
        return None

    def _extract_code(self, text: str) -> Optional[str]:
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None

    def get_domain(self) -> str:
        return "@emailnator.com"

    def close(self):
        self.client.close()


class EmailnatorTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("emailnator", {}).get(
            "api_url", "https://emailnator.com"
        )
        self.provider = None

    def validate(self) -> bool:
        return True

    def execute(self) -> TaskResult:
        try:
            self.provider = EmailnatorProvider(self.api_url)
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
