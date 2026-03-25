import time
import httpx
import random
import string
from typing import List, Dict, Optional, Tuple
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class MailsacProvider(TempMailProvider):
    DOMAINS = ["mailsac.com", "mailsac.net"]

    def __init__(self, api_key: str = "", domain: str = "mailsac.com"):
        self.base_url = "https://mailsac.com/api"
        self.api_key = api_key
        self.domain = domain
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
        self.username = ""

    def _random_string(self, length: int = 12) -> str:
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def create_email(self) -> Tuple[str, str]:
        try:
            self.username = f"user_{int(time.time())}_{self._random_string(8)}"
            self.email = f"{self.username}@{self.domain}"

            headers = {}
            if self.api_key:
                headers["Mailsac-Key"] = self.api_key

            response = self.client.get(
                f"{self.base_url}/addresses/{self.email}/messages",
                headers=headers
            )

            if response.status_code in [200, 404]:
                return self.email, ""

            return "", ""

        except Exception as e:
            print(f"[Mailsac] Create email error: {e}")
        return "", ""

    def get_messages(self, email: str) -> List[Dict]:
        try:
            address = email.split("@")[0]
            headers = {}
            if self.api_key:
                headers["Mailsac-Key"] = self.api_key

            response = self.client.get(
                f"{self.base_url}/addresses/{address}@{self.domain}/messages",
                headers=headers
            )

            if response.status_code == 200:
                messages = response.json()
                result = []
                for msg in messages:
                    result.append({
                        "id": msg.get("_id", ""),
                        "subject": msg.get("subject", ""),
                        "from": msg.get("from", ""),
                        "date": msg.get("date", "")
                    })
                return result

        except Exception as e:
            print(f"[Mailsac] Get messages error: {e}")
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
            address = email.split("@")[0]
            headers = {}
            if self.api_key:
                headers["Mailsac-Key"] = self.api_key

            response = self.client.get(
                f"{self.base_url}/addresses/{address}@{self.domain}/messages/{msg_id}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("text", "") or data.get("body", "")

        except Exception as e:
            print(f"[Mailsac] Get message detail error: {e}")
        return None

    def _extract_code(self, text: str) -> Optional[str]:
        import re
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None

    def get_domain(self) -> str:
        return f"@{self.domain}"

    def close(self):
        self.client.close()


class MailsacTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_key = global_config.get("email_providers", {}).get("mailsac", {}).get("api_key", "")
        self.domain = global_config.get("email_providers", {}).get("mailsac", {}).get("domain", "mailsac.com")
        self.provider = None

    def validate(self) -> bool:
        return True

    def execute(self) -> TaskResult:
        try:
            self.provider = MailsacProvider(api_key=self.api_key, domain=self.domain)
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
