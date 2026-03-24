import os
import time
import json
import random
import string
import secrets
import asyncio
import re
import sys
from faker import Faker
from camoufox.sync_api import Camoufox
from concurrent.futures import ThreadPoolExecutor
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "Results")
TRAE_ACCOUNTS_DIR = os.path.join(BASE_DIR, "TraeAccounts")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(TRAE_ACCOUNTS_DIR, exist_ok=True)

ACCOUNTS_FILE = os.path.join(TRAE_ACCOUNTS_DIR, "accounts.txt")


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


def main(concurrent_flows=5, max_tasks=50):
    task_counter = 0
    succeeded_tasks = 0
    failed_tasks = 0

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
                new_future = executor.submit(process_single_flow)
                running_futures.add(new_future)
                task_counter += 1

            time.sleep(0.5)

    print(f"[Info: Result] - Total: {max_tasks}, Success: {succeeded_tasks}, Failed: {failed_tasks}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            max_tasks = int(sys.argv[1])
            concurrent_flows = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        except ValueError:
            print("Usage: python register.py [total] [concurrency]")
            sys.exit(1)
    else:
        max_tasks = 50
        concurrent_flows = 5

    main(concurrent_flows, max_tasks)
