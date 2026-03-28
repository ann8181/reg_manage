import time
import httpx
import random
import string
import json
import re
from typing import List, Dict, Optional, Tuple
from core.base import TempMailProvider, TaskConfig, BaseTask, TaskResult, TaskStatus


class TempMailAsiaProvider(TempMailProvider):
    def __init__(self, api_url: str = "https://www.v3.temp-mail.asia"):
        self.base_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.email = ""
        self.session_token = ""

    def _random_string(self, length: int = 10) -> str:
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.post(
                f"{self.base_url}/random-email",
                json={}
            )

            if response.status_code == 200:
                data = response.json()
                self.email = data.get("email", "")
                self.session_token = data.get("token", "")
                return self.email, ""

            response = self.client.get(f"{self.base_url}/")
            csrf_match = re.search(r'name="csrf-token" content="([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                response = self.client.post(
                    f"{self.base_url}/api/new",
                    headers={"X-CSRF-Token": csrf_token},
                    json={"email": f"user_{self._random_string()}@{self._get_domain()}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    self.email = data.get("email", "")
                    return self.email, ""

        except Exception as e:
            print(f"[TempMailAsia] Create email error: {e}")
        return "", ""

    def _get_domain(self) -> str:
        try:
            response = self.client.get(f"{self.base_url}/domains")
            if response.status_code == 200:
                domains = response.json()
                if domains:
                    return domains[0]
        except:
            pass
        return "temp-mail.asia"

    def get_messages(self, email: str) -> List[Dict]:
        try:
            address = email.split("@")[0]
            response = self.client.get(
                f"{self.base_url}/email/{address}",
                headers={"Accept": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                messages = data.get("list", []) if isinstance(data, dict) else data
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
            print(f"[TempMailAsia] Get messages error: {e}")
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
            response = self.client.get(
                f"{self.base_url}/email/{address}/{msg_id}",
                headers={"Accept": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("body", "") or data.get("text", "")

        except Exception as e:
            print(f"[TempMailAsia] Get message detail error: {e}")
        return None

    def _extract_code(self, text: str) -> Optional[str]:
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None

    def get_domain(self) -> str:
        return f"@{self._get_domain()}"

    def close(self):
        self.client.close()


class TempMailAsiaTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("temp-mail-asia", {}).get(
            "api_url", "https://www.v3.temp-mail.asia"
        )
        self.provider = None

    def validate(self) -> bool:
        return True

    def execute(self) -> TaskResult:
        try:
            self.provider = TempMailAsiaProvider(self.api_url)
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
