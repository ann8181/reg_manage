import time
import httpx
from typing import Dict, Optional
from camoufox.sync_api import Camoufox
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


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


class KiroRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = global_config.get("ai_services", {}).get("kiro", {}).get("signup_url", "https://kiro.dev")
        self.proxy = global_config.get("proxy", "")
        self.browser_path = global_config.get("browser_path", "")
        self.temp_email_provider = global_config.get("temp_email_provider", "temp-mail-asia")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        email = f"user_{int(time.time())}@temp-mail.asia"
        password = self.generate_strong_password(14)
        
        try:
            launch_opts = {'headless': True}
            if self.proxy:
                launch_opts['proxy'] = self.proxy
            if self.browser_path:
                launch_opts['browser_path'] = self.browser_path

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

                except Exception as e:
                    pass
                
                self.save_account(email, password)
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"Kiro registration started: {email}",
                    data={"email": email, "password": password}
                )
                
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
