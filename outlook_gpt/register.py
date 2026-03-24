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
import httpx
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "Results")
CODEX_TOKENS_DIR = os.path.join(BASE_DIR, "CodexTokens")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CODEX_TOKENS_DIR, exist_ok=True)

CONFIG = {
    "outlook_email": os.getenv("OUTLOOK_EMAIL", ""),
    "outlook_password": os.getenv("OUTLOOK_PASSWORD", ""),
    "headless": os.getenv("HEADLESS", "true").lower() == "true",
    "output_file": os.path.join(RESULTS_DIR, "registered_accounts.txt"),
    "codex_token_dir": CODEX_TOKENS_DIR,
}


def generate_strong_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(chars) for _ in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*" for c in password)):
            return password


def random_email_name(length):
    first_char = random.choice(string.ascii_lowercase)
    other_chars = []
    for _ in range(length - 1):
        if random.random() < 0.07:
            other_chars.append(random.choice(string.digits))
        else:
            other_chars.append(random.choice(string.ascii_lowercase))
    return first_char + ''.join(other_chars)


def save_outlook_account(email, password):
    filename = os.path.join(RESULTS_DIR, "outlook_accounts.txt")
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{email}: {password}\n")
    print(f'[Outlook Account Saved] - {email}')


def save_chatgpt_result(email, password, access_token=None, refresh_token=None):
    with open(CONFIG["output_file"], 'a', encoding='utf-8') as f:
        line = f"{email}:{password}"
        if access_token:
            line += f":{access_token}"
        f.write(line + "\n")

    if access_token and refresh_token:
        token_file = os.path.join(CONFIG["codex_token_dir"], f"{email.replace('@', '_at_')}.json")
        token_data = {
            "email": email,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        with open(token_file, 'w') as f:
            json.dump(token_data, f, indent=2)

        access_file = os.path.join(CONFIG["codex_token_dir"], "access_tokens.txt")
        with open(access_file, 'a') as f:
            f.write(f"{access_token}\n")

        refresh_file = os.path.join(CONFIG["codex_token_dir"], "refresh_tokens.txt")
        with open(refresh_file, 'a') as f:
            f.write(f"{refresh_token}\n")

    print(f'[ChatGPT Result Saved] - {email}')


class OutlookMailClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.client = None
        self.access_token = None
        self.refresh_token = None

    def authenticate(self):
        self.client = httpx.Client(
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

    def get_tokens(self, code, code_verifier, redirect_uri, client_id, scopes):
        token_data = {
            'client_id': client_id,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier,
            'scope': ' '.join(scopes)
        }

        response = self.client.post(
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

    def get_verification_link(self, max_wait=120):
        if not self.access_token:
            return None

        headers = {'Authorization': f'Bearer {self.access_token}'}
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = self.client.get(
                    'https://graph.microsoft.com/v1.0/me/messages',
                    headers=headers
                )

                if response.status_code == 200:
                    messages = response.json().get('value', [])
                    for msg in messages:
                        subject = msg.get('subject', '')
                        if 'Verify' in subject or 'OpenAI' in subject or 'ChatGPT' in subject:
                            msg_id = msg.get('id')
                            detail_response = self.client.get(
                                f'https://graph.microsoft.com/v1.0/me/messages/{msg_id}',
                                headers=headers
                            )
                            if detail_response.status_code == 200:
                                body = detail_response.json().get('body', {}).get('content', '')
                                links = re.findall(r'https?://[^\s<>"\']+', body)
                                for link in links:
                                    if 'openai.com' in link and ('verify' in link.lower() or 'confirm' in link.lower() or 'email-verification' in link.lower()):
                                        return link
            except Exception as e:
                print(f"Error checking mail: {e}")

            time.sleep(5)

        return None

    def get_6digit_code(self, max_wait=120):
        if not self.access_token:
            return None

        headers = {'Authorization': f'Bearer {self.access_token}'}
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = self.client.get(
                    'https://graph.microsoft.com/v1.0/me/messages',
                    headers=headers
                )

                if response.status_code == 200:
                    messages = response.json().get('value', [])
                    for msg in messages:
                        subject = msg.get('subject', '')
                        if 'Verify' in subject or 'code' in subject.lower():
                            msg_id = msg.get('id')
                            detail_response = self.client.get(
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

            time.sleep(5)

        return None

    def close(self):
        if self.client:
            self.client.close()


def outlook_register_sync(proxy=None, headless=True):
    fake = Faker()
    lastname = fake.last_name()
    firstname = fake.first_name()
    year = str(random.randint(1960, 2005))
    month = str(random.randint(1, 12))
    day = str(random.randint(1, 28))

    email_name = random_email_name(random.randint(12, 14))
    email = f"{email_name}@outlook.com"
    password = generate_strong_password(random.randint(11, 15))

    try:
        launch_opts = {'headless': headless}
        if proxy:
            launch_opts['proxy'] = proxy

        with Camoufox(**launch_opts) as browser:
            page = browser.new_page()

            try:
                page.goto("https://signup.live.com/signup?mkt=EN-US&lc=1033", timeout=30000, wait_until="domcontentloaded")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"[Error: IP] - Cannot access registration page: {e}")
                return None, None, False

            try:
                page.get_by_role("textbox", name="Email").wait_for(timeout=15000)
                page.get_by_role("textbox", name="Email").fill(email)
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
                    page.wait_for_url(lambda url: "login.live.com" in url or "outlook.live.com" in url, timeout=30000)
                except:
                    pass

            except Exception as e:
                print(f"[Error: Registration] - {e}")
                return None, None, False

        print(f'[Success: Outlook Registration] - {email}')
        save_outlook_account(email, password)
        return email, password, True

    except Exception as e:
        print(f"[Error] - {e}")
        return None, None, False


def chatgpt_register_with_outlook(email, password, proxy=None, headless=True):
    outlook_client = OutlookMailClient(email, password)

    try:
        auth_url, code_verifier, redirect_uri, client_id, scopes = outlook_client.authenticate()

        launch_opts = {'headless': headless}
        if proxy:
            launch_opts['proxy'] = proxy

        with Camoufox(**launch_opts) as browser:
            page = browser.new_page()

            try:
                page.goto("https://chatgpt.com/auth/login", timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(2000)

                page.get_by_text("Sign up").click()
                page.wait_for_timeout(1000)

                page.get_by_role("textbox", name="Email").fill(email)
                page.get_by_text("Continue").click()
                page.wait_for_timeout(2000)

                ver_link = outlook_client.get_verification_link(max_wait=180)
                if not ver_link:
                    print("[ChatGPT] No verification link received")
                    return False

                page.goto(ver_link)
                page.wait_for_timeout(3000)

                fake = Faker()
                name = f"{fake.first_name()} {fake.last_name()}"
                year = str(random.randint(1985, 2002))
                month = str(random.randint(1, 12))
                day = str(random.randint(1, 28))
                birthdate = f"{month}/{day}/{year}"

                try:
                    name_input = page.locator('[name="name"]').first
                    name_input.fill(name)
                except:
                    page.locator('#firstName').fill(fake.first_name())
                    page.locator('#lastName').fill(fake.last_name())

                page.locator('[name="birthdate"]').fill(birthdate)
                page.get_by_text("Continue").click()
                page.wait_for_timeout(3000)

                print(f"[ChatGPT] Registration completed for {email}")

                tokens = perform_codex_oauth(page, email, password, outlook_client)
                if tokens:
                    save_chatgpt_result(email, password, tokens.get('access_token'), tokens.get('refresh_token'))
                    print(f"[ChatGPT] SUCCESS! Codex token obtained for {email}")
                    return True
                else:
                    save_chatgpt_result(email, password)
                    return True

            except Exception as e:
                print(f"[ChatGPT] Registration error: {e}")
                return False
            finally:
                browser.close()

    finally:
        outlook_client.close()

    return False


def perform_codex_oauth(page, email, password, outlook_client):
    try:
        code_verifier = ''.join(secrets.choice(string.ascii_letters + string.digits + '-._~') for _ in range(128))
        import hashlib
        import base64
        sha256_hash = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(sha256_hash).decode().rstrip('=')
        state = secrets.token_urlsafe(24)

        oauth_params = {
            'response_type': 'code',
            'client_id': 'app_EMoamEEZ73f0CkXaXp7hrann',
            'redirect_uri': 'http://localhost:1455/auth/callback',
            'scope': 'openid profile email offline_access',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': state,
        }

        from urllib.parse import urlencode
        authorize_url = f"https://auth.openai.com/oauth/authorize?{urlencode(oauth_params)}"

        page.goto(authorize_url)
        page.wait_for_timeout(2000)

        try:
            page.locator('#username').fill(email)
            page.get_by_text("Continue").click()
            page.wait_for_timeout(1000)

            page.locator('#password').fill(password)
            page.get_by_text("Continue").click()
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[OAuth] Error filling credentials: {e}")

        if "consent" in page.url.lower() or "authorize" in page.url.lower():
            try:
                page.get_by_text("Consent").click()
                page.wait_for_timeout(2000)
            except:
                try:
                    page.get_by_text("Approve").click()
                    page.wait_for_timeout(2000)
                except:
                    pass

        final_url = page.url
        code = None

        if "code=" in final_url:
            from urllib.parse import parse_qs, urlparse
            code = parse_qs(urlparse(final_url).query).get("code", [None])[0]
        elif "localhost" in final_url:
            from urllib.parse import parse_qs, urlparse
            code = parse_qs(urlparse(final_url).query).get("code", [None])[0]

        if not code:
            print("[OAuth] No code found in URL")
            return None

        token_response = httpx.post(
            'https://auth.openai.com/oauth/token',
            json={
                "grant_type": "authorization_code",
                "client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
                "code": code,
                "redirect_uri": "http://localhost:1455/auth/callback",
                "code_verifier": code_verifier,
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30
        )

        if token_response.status_code == 200:
            return token_response.json()

    except Exception as e:
        print(f"[OAuth] Error: {e}")

    return None


def process_single_flow():
    try:
        email, password, success = outlook_register_sync(headless=CONFIG["headless"])

        if not success or not email:
            return False

        result = chatgpt_register_with_outlook(email, password, headless=CONFIG["headless"])
        return result

    except Exception as e:
        print(f"[Error] - Process error: {e}")
        return False


def main():
    if CONFIG["outlook_email"] and CONFIG["outlook_password"]:
        email = CONFIG["outlook_email"]
        password = CONFIG["outlook_password"]
        result = chatgpt_register_with_outlook(email, password, headless=CONFIG["headless"])
        if result:
            print("[Success] ChatGPT registration with Codex token completed!")
        else:
            print("[Failed] ChatGPT registration failed")
    else:
        print("[Info] No existing Outlook account, registering new one...")
        result = process_single_flow()
        if result:
            print("[Success] Full flow completed!")
        else:
            print("[Failed] Full flow failed")


if __name__ == '__main__':
    main()
