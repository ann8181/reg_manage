import os
import time
import random
import string
import secrets
import asyncio
import re
import sys
from typing import Dict, Optional, Tuple
from faker import Faker
from camoufox.sync_api import Camoufox
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class OutlookRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.bot_protection_wait = global_config.get("bot_protection_wait", 12)
        self.max_captcha_retries = global_config.get("max_captcha_retries", 2)
        self.proxy = global_config.get("proxy", "")
        self.browser_path = global_config.get("browser_path", "")
    
    def validate(self) -> bool:
        return True
    
    def _generate_email_username(self, length: int) -> str:
        first_char = random.choice(string.ascii_lowercase)
        other_chars = []
        for _ in range(length - 1):
            if random.random() < 0.07:
                other_chars.append(random.choice(string.digits))
            else:
                other_chars.append(random.choice(string.ascii_lowercase))
        return first_char + ''.join(other_chars)
    
    def _generate_strong_password(self, length: int = 16) -> str:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(chars) for _ in range(length))
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and any(c.isdigit() for c in password)
                    and any(c in "!@#$%^&*" for c in password)):
                return password
    
    def _extract_verification_code(self, text: str) -> Optional[str]:
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None
    
    def execute(self) -> TaskResult:
        fake = Faker()
        lastname = fake.last_name()
        firstname = fake.first_name()
        year = str(random.randint(1960, 2005))
        month = str(random.randint(1, 12))
        day = str(random.randint(1, 28))

        email_username = self._generate_email_username(random.randint(12, 14))
        password = self._generate_strong_password(random.randint(11, 15))

        try:
            launch_opts = {'headless': True}
            if self.proxy:
                launch_opts['proxy'] = self.proxy
            if self.browser_path:
                launch_opts['browser_path'] = self.browser_path

            with Camoufox(**launch_opts) as browser:
                page = browser.new_page()

                try:
                    page.goto("https://signup.live.com/signup?mkt=EN-US&lc=1033", timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(2000)

                    page.get_by_role("textbox", name="Email").wait_for(timeout=15000)
                    page.get_by_role("textbox", name="Email").fill(email_username)
                    page.get_by_text("Next").click()
                    page.wait_for_timeout(3000)
                    
                    page.locator('[type="password"]').wait_for(timeout=10000)
                    page.locator('[type="password"]').fill(password)
                    page.get_by_text("Next").click()
                    page.wait_for_timeout(3000)
                    
                    page.locator('[name="BirthYear"]').fill(year)
                    page.locator('[name="BirthMonth"]').select_option(value=month)
                    page.wait_for_timeout(500)
                    page.locator('[name="BirthDay"]').select_option(value=day)
                    page.wait_for_timeout(500)
                    page.get_by_text("Next").click()
                    page.wait_for_timeout(3000)
                    
                    page.locator('#lastNameInput').fill(lastname)
                    page.locator('#firstNameInput').fill(firstname)
                    page.get_by_text("Next").click()
                    page.wait_for_timeout(5000)
                    
                    try:
                        page.wait_for_url(lambda url: "https://login.live.com/" in url or "https://outlook.live.com/" in url, timeout=30000)
                    except:
                        pass

                except Exception as e:
                    return TaskResult(
                        task_id=self.config.task_id,
                        status=TaskStatus.FAILED,
                        error=f"Registration error: {str(e)}"
                    )

            full_email = f"{email_username}@outlook.com"
            self.save_account(full_email, password)
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"Outlook registered: {full_email}",
                data={"email": full_email, "password": password}
            )

        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )


class OutlookMailClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.client = None
        self.access_token = None
        self.refresh_token = None
    
    async def authenticate(self):
        import httpx
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            timeout=30.0,
            follow_redirects=True
        )

        client_id = "4f057656-d3de-4d2f-ba4e-95493d189b38"
        redirect_uri = "http://localhost:53682"

        code_verifier = ''.join(secrets.choice(string.ascii_letters + string.digits + '-._~') for _ in range(128))

        import hashlib
        import base64
        sha256_hash = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(sha256_hash).decode().rstrip('=')

        scopes = [
            "offline_access",
            "https://graph.microsoft.com/Mail.ReadWrite",
            "https://graph.microsoft.com/Mail.Send",
            "https://graph.microsoft.com/User.Read"
        ]

        from urllib.parse import urlencode
        auth_params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'response_mode': 'query',
            'prompt': 'select_account',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }

        auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(auth_params)}"
        return auth_url, code_verifier, redirect_uri, client_id, scopes
    
    async def get_tokens(self, code: str, code_verifier: str, redirect_uri: str, client_id: str, scopes: list):
        import httpx
        token_data = {
            'client_id': client_id,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier,
            'scope': ' '.join(scopes)
        }

        response = await self.client.post(
            'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')
            return True
        return False
    
    async def get_verification_code(self, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        if not self.access_token:
            return None

        headers = {'Authorization': f'Bearer {self.access_token}'}
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = await self.client.get(
                    'https://graph.microsoft.com/v1.0/me/messages',
                    headers=headers
                )

                if response.status_code == 200:
                    messages = response.json().get('value', [])
                    for msg in messages:
                        subject = msg.get('subject', '')
                        if subject_contains and subject_contains.lower() not in subject.lower():
                            continue
                        msg_id = msg.get('id')
                        detail_response = await self.client.get(
                            f'https://graph.microsoft.com/v1.0/me/messages/{msg_id}',
                            headers=headers
                        )
                        if detail_response.status_code == 200:
                            body = detail_response.json().get('body', {}).get('content', '')
                            code = self._extract_verification_code(body)
                            if code:
                                return code
            except Exception as e:
                print(f"Error checking mail: {e}")

            await asyncio.sleep(5)

        return None
    
    def _extract_verification_code(self, text: str) -> Optional[str]:
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', text)
        return codes[0] if codes else None
    
    async def close(self):
        if self.client:
            await self.client.aclose()
