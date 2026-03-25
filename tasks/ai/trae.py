import time
import random
import string
from typing import Dict
from faker import Faker
from camoufox.sync_api import Camoufox
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class TraeRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = global_config.get("ai_services", {}).get("trae", {}).get("signup_url", "https://www.trae.ai/sign-up")
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
    
    def execute(self) -> TaskResult:
        email_username = self._generate_email_username(random.randint(12, 14))
        email = f"{email_username}@outlook.com"
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
                    page.goto(self.signup_url, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    
                    page.get_by_role("textbox", name="Email").fill(email)
                    page.get_by_text("Send Code").click()
                    time.sleep(2)
                    
                except Exception as e:
                    pass
                
                self.save_account(email, password)
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"Trae registration started: {email}",
                    data={"email": email, "password": password}
                )
                
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
