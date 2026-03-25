import os
import time
import json
import random
import string
import secrets
import asyncio
import re
import sys
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple
from faker import Faker
from camoufox.sync_api import Camoufox
from concurrent.futures import ThreadPoolExecutor
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "Results")
TRAE_ACCOUNTS_DIR = os.path.join(BASE_DIR, "TraeAccounts")
KIRO_ACCOUNTS_DIR = os.path.join(BASE_DIR, "KiroAccounts")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(TRAE_ACCOUNTS_DIR, exist_ok=True)
os.makedirs(KIRO_ACCOUNTS_DIR, exist_ok=True)

ACCOUNTS_FILE = os.path.join(TRAE_ACCOUNTS_DIR, "accounts.txt")
KIRO_ACCOUNTS_FILE = os.path.join(KIRO_ACCOUNTS_DIR, "accounts.txt")


class TempMailProvider(ABC):
    @abstractmethod
    def create_email(self) -> Tuple[str, str]:
        pass

    @abstractmethod
    def get_messages(self, email: str) -> List[Dict]:
        pass

    @abstractmethod
    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        pass

    @abstractmethod
    def get_domain(self) -> str:
        pass

    def close(self):
        pass


class TempMailAsiaProvider(TempMailProvider):
    def __init__(self):
        self.base_url = "https://www.v3.temp-mail.asia"
        self.client = httpx.Client(timeout=30.0)

    def create_email(self) -> Tuple[str, str]:
        try:
            response = self.client.post(f"{self.base_url}/random-email")
            if response.status_code == 200:
                data = response.json()
                return data.get("email", ""), data.get("password", "")
        except Exception as e:
            print(f"[TempMailAsia] Create email error: {e}")
        return "", ""

    def get_messages(self, email: str) -> List[Dict]:
        try:
            response = self.client.get(f"{self.base_url}/messages")
            if response.status_code == 200:
                return response.json().get("messages", [])
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
                body = msg.get("body", "")
                codes = re.findall(r'\b\d{6}\b', body)
                if codes:
                    return codes[0]
                codes = re.findall(r'\b\d{4}\b', body)
                if codes:
                    return codes[0]
            time.sleep(5)
        return None

    def get_domain(self) -> str:
        return "@temp-mail.asia"

    def close(self):
        self.client.close()


class TempMailAwslProvider(TempMailProvider):
    def __init__(self, worker_url: str = "https://temp-mail.awsl.uk", jwt_password: str = ""):
        self.worker_url = worker_url
        self.jwt_password = jwt_password
        self.address = ""
        self.client = httpx.Client(timeout=30.0)

    def create_email(self) -> Tuple[str, str]:
        try:
            headers = {"Content-Type": "application/json"}
            if self.jwt_password:
                headers["Authorization"] = f"Bearer {self.jwt_password}"

            address_name = random_email(random.randint(10, 15))
            domain = self._get_domain()
            self.address = f"{address_name}{domain}"

            return self.address, ""
        except Exception as e:
            print(f"[TempMailAwsl] Create email error: {e}")
        return "", ""

    def _get_domain(self) -> str:
        try:
            response = self.client.get(
                f"{self.worker_url}/open_api/settings",
                headers={"x-custom-auth": self.jwt_password} if self.jwt_password else {}
            )
            if response.status_code == 200:
                data = response.json()
                domains = data.get("domains", [])
                if domains:
                    return f"@{domains[0]}"
        except:
            pass
        return "@awsl.uk"

    def get_messages(self, email: str) -> List[Dict]:
        try:
            headers = {"Content-Type": "application/json"}
            if self.jwt_password:
                headers["Authorization"] = f"Bearer {self.jwt_password}"

            address = email.split("@")[0] if "@" in email else email
            response = self.client.get(
                f"{self.worker_url}/api/mails",
                headers=headers,
                params={"limit": 20, "offset": 0, "address": address}
            )
            if response.status_code == 200:
                return response.json().get("emails", [])
        except Exception as e:
            print(f"[TempMailAwsl] Get messages error: {e}")
        return []

    def get_verification_code(self, email: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)
            for msg in messages:
                subject = msg.get("subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                body = msg.get("body", "")
                if not body:
                    continue
                codes = re.findall(r'\b\d{6}\b', body)
                if codes:
                    return codes[0]
                codes = re.findall(r'\b\d{4}\b', body)
                if codes:
                    return codes[0]
            time.sleep(5)
        return None

    def get_domain(self) -> str:
        return self._get_domain()

    def close(self):
        self.client.close()


class GuerrillaMailProvider(TempMailProvider):
    def __init__(self):
        self.base_url = "https://api.guerrillamail.com"
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


class MailDropProvider(TempMailProvider):
    def __init__(self):
        self.base_url = "https://api.maildrop.cc"
        self.client = httpx.Client(timeout=30.0)
        self.email = ""

    def create_email(self) -> Tuple[str, str]:
        address_name = random_email(random.randint(10, 15))
        self.email = f"{address_name}@maildrop.cc"
        return self.email, ""

    def get_messages(self, email: str) -> List[Dict]:
        try:
            address = email.split("@")[0] if "@" in email else email
            response = self.client.get(
                f"{self.base_url}/api/messages/{address}"
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[MailDrop] Get messages error: {e}")
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
                    body = self._get_email_body(email.split("@")[0], msg_id)
                    if body:
                        codes = re.findall(r'\b\d{6}\b', body)
                        if codes:
                            return codes[0]
                        codes = re.findall(r'\b\d{4}\b', body)
                        if codes:
                            return codes[0]
            time.sleep(5)
        return None

    def _get_email_body(self, address: str, msg_id: str) -> Optional[str]:
        try:
            response = self.client.get(
                f"{self.base_url}/api/messages/{address}/{msg_id}"
            )
            if response.status_code == 200:
                return response.json().get("body", "")
        except:
            pass
        return None

    def get_domain(self) -> str:
        return "@maildrop.cc"

    def close(self):
        self.client.close()


def create_temp_mail_provider(provider_type: str, **kwargs) -> TempMailProvider:
    providers = {
        "temp-mail-asia": TempMailAsiaProvider,
        "temp-mail-awsl": TempMailAwslProvider,
        "guerrilla-mail": GuerrillaMailProvider,
        "maildrop": MailDropProvider,
    }
    provider_class = providers.get(provider_type.lower(), TempMailAsiaProvider)
    return provider_class(**kwargs)


class KiroAuthClient:
    def __init__(self):
        self.client_id = "kiro-cli"
        self.redirect_uri = "http://localhost:8765"
        self.base_url = "https://auth.kiro.dev"
        self.client = httpx.Client(timeout=30.0)

    def get_device_code(self):
        try:
            response = self.client.post(
                f"{self.base_url}/oauth/device/code",
                data={
                    "client_id": self.client_id,
                    "redirect_uri": self.redirect_uri,
                    "scope": "openid profile email"
                }
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[Kiro] Get device code error: {e}")
        return None

    def poll_for_token(self, device_code: str, interval: int = 5):
        try:
            while True:
                response = self.client.post(
                    f"{self.base_url}/oauth/token",
                    data={
                        "client_id": self.client_id,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                    }
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 400:
                    data = response.json()
                    error = data.get("error", "")
                    if error == "authorization_pending":
                        time.sleep(interval)
                        continue
                    elif error == "expired_token":
                        return None
                else:
                    break
        except Exception as e:
            print(f"[Kiro] Poll token error: {e}")
        return None

    def get_user_info(self, access_token: str):
        try:
            response = self.client.get(
                f"{self.base_url}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[Kiro] Get user info error: {e}")
        return None

    def close(self):
        self.client.close()


def kiro_register_sync(email: str, password: str, proxy: str, temp_provider: TempMailProvider = None):
    try:
        launch_opts = {'headless': True}
        if proxy:
            launch_opts['proxy'] = proxy

        with Camoufox(**launch_opts) as browser:
            page = browser.new_page()

            try:
                page.goto("https://kiro.dev", timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)

                page.goto("https://auth.kiro.dev/signup", timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)

                page.get_by_role("button", name="Continue with Email").click()
                time.sleep(1)

                page.get_by_role("textbox", name="Email").fill(email)
                page.get_by_role("button", name="Continue").click()
                time.sleep(3)

                if temp_provider:
                    verification_code = temp_provider.get_verification_code(
                        email,
                        subject_contains="kiro",
                        max_wait=120
                    )
                else:
                    verification_code = None

                if not verification_code:
                    print("[Kiro] No verification code received")
                    return False

                page.get_by_role("textbox", name="Code").fill(verification_code)
                page.get_by_role("button", name="Verify").click()
                time.sleep(3)

                page.get_by_role("textbox", name="Create a password").fill(password)
                page.get_by_role("button", name="Create account").click()
                time.sleep(5)

                page.wait_for_load_state("domcontentloaded")

                print(f"[Kiro] Registration successful - {email}")
                save_kiro_account(email, password)
                return True

            except Exception as e:
                print(f"[Kiro] Registration error: {e}")
                return False

    except Exception as e:
        print(f"[Kiro] Browser error: {e}")
        return False


def kiro_register_with_oauth_sync(email: str, password: str, proxy: str):
    try:
        launch_opts = {'headless': True}
        if proxy:
            launch_opts['proxy'] = proxy

        kiro_auth = KiroAuthClient()
        device_data = kiro_auth.get_device_code()

        if not device_data:
            print("[Kiro OAuth] Failed to get device code")
            kiro_auth.close()
            return False

        device_code = device_data.get("device_code")
        user_code = device_data.get("user_code")
        verification_uri = device_data.get("verification_uri")

        with Camoufox(**launch_opts) as browser:
            page = browser.new_page()

            try:
                page.goto(verification_uri, timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)

                page.get_by_role("textbox", name="Enter code").fill(user_code)
                page.get_by_role("button", name="Verify").click()
                time.sleep(2)

                page.get_by_role("textbox", name="Email").fill(email)
                page.get_by_role("button", name="Continue").click()
                time.sleep(3)

                page.get_by_role("textbox", name="Code").fill("000000")
                page.get_by_role("button", name="Verify").click()
                time.sleep(2)

                page.get_by_role("textbox", name="Create a password").fill(password)
                page.get_by_role("button", name="Create account").click()
                time.sleep(5)

                print(f"[Kiro OAuth] Started registration - {email}")

            except Exception as e:
                print(f"[Kiro OAuth] Browser error: {e}")
            finally:
                kiro_auth.close()

        token_data = kiro_auth.poll_for_token(device_code)
        if token_data:
            access_token = token_data.get("access_token")
            if access_token:
                user_info = kiro_auth.get_user_info(access_token)
                if user_info:
                    print(f"[Kiro OAuth] Registration successful - {email}")
                    save_kiro_account(email, password)
                    return True

        return False

    except Exception as e:
        print(f"[Kiro OAuth] Error: {e}")
        return False


def save_kiro_account(email: str, password: str):
    write_header = not os.path.exists(KIRO_ACCOUNTS_FILE) or os.path.getsize(KIRO_ACCOUNTS_FILE) == 0
    with open(KIRO_ACCOUNTS_FILE, "a", encoding="utf-8") as f:
        if write_header:
            f.write("Email    Password\n")
        f.write(f"{email}    {password}\n")
    print(f'[Kiro Account Saved] - {email}')


def generate_strong_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(chars) for _ in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*" for c in password)):
            return password


def random_email(length):
    first_char = random.choice(string.ascii_lowercase)
    other_chars = []
    for _ in range(length - 1):
        if random.random() < 0.07:
            other_chars.append(random.choice(string.digits))
        else:
            other_chars.append(random.choice(string.ascii_lowercase))
    return first_char + ''.join(other_chars)


def load_config():
    config_path = os.path.join(BASE_DIR, "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_outlook_account(email, password):
    filename = os.path.join(RESULTS_DIR, "outlook_accounts.txt")
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{email}@outlook.com: {password}\n")
    print(f'[Outlook Account Saved] - {email}@outlook.com')


def save_trae_account(email, password):
    write_header = not os.path.exists(ACCOUNTS_FILE) or os.path.getsize(ACCOUNTS_FILE) == 0
    with open(ACCOUNTS_FILE, "a", encoding="utf-8") as f:
        if write_header:
            f.write("Email    Password\n")
        f.write(f"{email}    {password}\n")
    print(f'[Trae Account Saved] - {email}')


class OutlookMailClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.client = None
        self.access_token = None
        self.refresh_token = None

    async def authenticate(self):
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

        from urllib.parse import urlencode
        auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(auth_params)}"
        return auth_url, code_verifier, redirect_uri, client_id, scopes

    async def get_tokens(self, code, code_verifier, redirect_uri, client_id, scopes):
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

    async def get_verification_code(self, max_wait=120):
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
                        if 'Trae' in subject or 'trae' in subject or 'verification' in subject.lower():
                            msg_id = msg.get('id')
                            detail_response = await self.client.get(
                                f'https://graph.microsoft.com/v1.0/me/messages/{msg_id}',
                                headers=headers
                            )
                            if detail_response.status_code == 200:
                                body = detail_response.json().get('body', {}).get('content', '')
                                codes = re.findall(r'\b\d{6}\b', body)
                                if codes:
                                    return codes[0]
            except Exception as e:
                print(f"Error checking mail: {e}")

            await asyncio.sleep(5)

        return None

    async def close(self):
        if self.client:
            await self.client.aclose()


def outlook_register_sync(proxy, bot_protection_wait, max_captcha_retries):
    fake = Faker()
    lastname = fake.last_name()
    firstname = fake.first_name()
    year = str(random.randint(1960, 2005))
    month = str(random.randint(1, 12))
    day = str(random.randint(1, 28))

    email = random_email(random.randint(12, 14))
    password = generate_strong_password(random.randint(11, 15))

    try:
        launch_opts = {'headless': True}
        if proxy:
            launch_opts['proxy'] = proxy

        with Camoufox(**launch_opts) as browser:
            page = browser.new_page()

            try:
                page.goto("https://signup.live.com/signup?mkt=EN-US&lc=1033", timeout=30000, wait_until="domcontentloaded")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"[Error: IP] - 无法进入注册界面: {e}")
                return None, None, None, False

            try:
                # 英文页面: Enter your email address
                page.get_by_role("textbox", name="Email").wait_for(timeout=15000)
                page.get_by_role("textbox", name="Email").fill(email)
                page.get_by_text("Next").click()
                page.wait_for_timeout(3000)
                
                # 输入密码页面
                page.locator('[type="password"]').wait_for(timeout=10000)
                page.locator('[type="password"]').fill(password)
                page.get_by_text("Next").click()
                page.wait_for_timeout(3000)
                
                # 生日页面
                page.locator('[name="BirthYear"]').fill(year)
                page.locator('[name="BirthMonth"]').select_option(value=month)
                page.wait_for_timeout(500)
                page.locator('[name="BirthDay"]').select_option(value=day)
                page.wait_for_timeout(500)
                page.get_by_text("Next").click()
                page.wait_for_timeout(3000)
                
                # 名字页面
                page.locator('#lastNameInput').fill(lastname)
                page.locator('#firstNameInput').fill(firstname)
                page.get_by_text("Next").click()
                page.wait_for_timeout(5000)
                
                # 等待最终完成
                try:
                    page.wait_for_url(lambda url: "https://login.live.com/" in url or "https://outlook.live.com/" in url, timeout=30000)
                except:
                    pass

            except Exception as e:
                print(f"[Error: Registration] - {e}")
                return None, None, None, False

        print(f'[Success: Outlook Registration] - {email}@outlook.com: {password}')
        save_outlook_account(email, password)

        return f"{email}@outlook.com", password, None, True

    except Exception as e:
        print(f"[Error] - {e}")
        return None, None, None, False


def trae_register_sync(email, password, proxy):
    try:
        launch_opts = {'headless': True}
        if proxy:
            launch_opts['proxy'] = proxy

        with Camoufox(**launch_opts) as browser:
            page = browser.new_page()

            try:
                page.goto("https://www.trae.ai/sign-up", timeout=30000)
                page.wait_for_load_state("domcontentloaded")

                page.get_by_role("textbox", name="Email").fill(email)
                page.get_by_text("Send Code").click()
                print(f"[Trae] Verification code sent to {email}")

                outlook_client = OutlookMailClient(email.replace("@outlook.com", ""), password)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    auth_url, code_verifier, redirect_uri, client_id, scopes = loop.run_until_complete(outlook_client.authenticate())

                    code_received = asyncio.Event()

                    def handle_request(request):
                        if redirect_uri in request.url and 'code=' in request.url:
                            code_match = re.search(r'code=([^&]+)', request.url)
                            if code_match and not code_received.is_set():
                                code_received.set()
                                return code_match.group(1)
                        return None

                    page.goto(auth_url)

                    try:
                        code = asyncio.wait_for(code_received.wait(), timeout=60)
                        if code:
                            success = loop.run_until_complete(outlook_client.get_tokens(code, code_verifier, redirect_uri, client_id, scopes))
                            if success:
                                verification_code = loop.run_until_complete(outlook_client.get_verification_code(max_wait=120))
                    except asyncio.TimeoutError:
                        print("[Trae] OAuth timeout, waiting for email...")
                        verification_code = None
                        for i in range(24):
                            time.sleep(5)
                            verification_code = loop.run_until_complete(outlook_client.get_verification_code(max_wait=10))
                            if verification_code:
                                break
                            print(f"[Trae] Still waiting for email... ({i+1}/24)")

                finally:
                    loop.run_until_complete(outlook_client.close())
                    loop.close()

                if not verification_code:
                    print("[Trae] No verification code received")
                    return False

                page.get_by_role("textbox", name="Verification code").fill(verification_code)
                page.get_by_role("textbox", name="Password").fill(password)

                signup_btns = page.get_by_text("Sign Up")
                if signup_btns.count() > 1:
                    signup_btns.nth(1).click()
                else:
                    signup_btns.click()

                time.sleep(2)

                try:
                    page.wait_for_url(lambda url: "/sign-up" not in url, timeout=20000)
                    print("[Trae] Registration successful - page redirected")
                except:
                    print("[Trae] Registration completed (timeout)")

                save_trae_account(email, password)
                return True

            except Exception as e:
                print(f"[Trae] Registration error: {e}")
                return False

    except Exception as e:
        print(f"[Error] - Browser error: {e}")
        return False


def process_single_flow():
    try:
        config = load_config()
        proxy = config.get('proxy', '')
        bot_protection_wait = config.get('Bot_protection_wait', 12) * 1000
        max_captcha_retries = config.get('max_captcha_retries', 2)

        outlook_email, outlook_password, _, success = outlook_register_sync(
            proxy, bot_protection_wait, max_captcha_retries
        )

        if not success or not outlook_email:
            return False

        result = trae_register_sync(outlook_email, outlook_password, proxy)
        return result

    except Exception as e:
        print(f"[Error] - Process error: {e}")
        return False


def process_kiro_flow():
    try:
        config = load_config()
        proxy = config.get('proxy', '')
        provider_type = config.get('temp_email_provider', 'temp-mail-asia')

        provider_kwargs = {}
        if provider_type == 'temp-mail-awsl':
            provider_kwargs['worker_url'] = config.get('temp_mail_awsl_url', 'https://temp-mail.awsl.uk')
            provider_kwargs['jwt_password'] = config.get('temp_mail_awsl_jwt', '')

        temp_provider = create_temp_mail_provider(provider_type, **provider_kwargs)

        email, _ = temp_provider.create_email()
        if not email:
            print("[Error] Failed to create temp email")
            temp_provider.close()
            return False

        password = generate_strong_password(random.randint(11, 15))
        print(f"[Kiro] Using temp email: {email}")

        result = kiro_register_sync(email, password, proxy, temp_provider)
        temp_provider.close()
        return result

    except Exception as e:
        print(f"[Error] - Kiro process error: {e}")
        return False


def main(register_type='trae', concurrent_flows=5, max_tasks=50):
    task_counter = 0
    succeeded_tasks = 0
    failed_tasks = 0

    def get_flow_func():
        if register_type == 'kiro':
            return process_kiro_flow
        else:
            return process_single_flow

    flow_func = get_flow_func()

    with ThreadPoolExecutor(max_workers=concurrent_flows) as executor:
        running_futures = set()

        while task_counter < max_tasks or len(running_futures) > 0:
            done_futures = {f for f in running_futures if f.done()}
            for future in done_futures:
                try:
                    result = future.result()
                    if result:
                        succeeded_tasks += 1
                    else:
                        failed_tasks += 1
                except Exception as e:
                    failed_tasks += 1
                    print(e)
                running_futures.remove(future)

            while len(running_futures) < concurrent_flows and task_counter < max_tasks:
                time.sleep(0.2)
                new_future = executor.submit(flow_func)
                running_futures.add(new_future)
                task_counter += 1

            time.sleep(0.5)

    print(f"[Info: Result] - Type: {register_type}, Total: {max_tasks}, Success: {succeeded_tasks}, Failed: {failed_tasks}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        register_type = sys.argv[1].lower()
        if register_type not in ['trae', 'kiro', 'all']:
            print("Usage: python register.py [trae|kiro|all] [total] [concurrency]")
            sys.exit(1)

        try:
            max_tasks = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            concurrent_flows = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        except ValueError:
            print("Usage: python register.py [trae|kiro|all] [total] [concurrency]")
            sys.exit(1)
    else:
        register_type = 'trae'
        max_tasks = 50
        concurrent_flows = 5

    if register_type == 'all':
        print("[Info] Starting all registrations: Trae + Kiro")
        main('trae', concurrent_flows, max_tasks)
        main('kiro', concurrent_flows, max_tasks)
    else:
        main(register_type, concurrent_flows, max_tasks)
