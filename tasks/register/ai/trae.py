import time
import random
import string
from typing import Dict
from faker import Faker
from core.browser_task import BrowserTask
from core.base import TaskConfig, TaskResult, TaskStatus


class TraeRegister(BrowserTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = global_config.get("ai_services", {}).get("trae", {}).get("signup_url", "https://www.trae.ai/sign-up")
    
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
        
        self.log_action_start("trae_register", f"Registering Trae account: {email}")
        
        try:
            launch_opts = self._setup_browser()
            
            from camoufox.sync_api import Camoufox
            with Camoufox(**launch_opts) as browser:
                self._page = browser.new_page()
                self.logger.browser_logger.set_page(self._page)
                self.logger.perf_metrics.start()
                
                try:
                    self.log_browser_navigate(self.signup_url)
                    self._page.goto(self.signup_url, timeout=30000)
                    self._page.wait_for_load_state("domcontentloaded")
                    time.sleep(2)
                    self.logger.take_screenshot("01_signup_page", self._page)
                    
                    self.log_browser_fill("Email", email, mask=False)
                    self._page.get_by_role("textbox", name="Email").fill(email)
                    self._page.wait_for_timeout(500)
                    self.logger.take_screenshot("02_email_filled", self._page)
                    
                    self.log_browser_click("Send Code")
                    self._page.get_by_text("Send Code").click()
                    time.sleep(2)
                    self.logger.take_screenshot("03_code_sent", self._page)
                    
                except Exception as e:
                    self.logger.error(f"Registration step failed: {str(e)}")
                    self.logger.take_screenshot("error", self._page)
                    raise
                
                self.save_account(email, password)
                self.logger.perf_metrics.end()
                self.log_action_end("trae_register", f"Trae registration started: {email}", True)
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"Trae registration started: {email}",
                    data={"email": email, "password": password}
                )
                
        except Exception as e:
            self.logger.error(f"Trae registration failed: {str(e)}")
            self.logger.perf_metrics.end()
            self.log_action_end("trae_register", str(e), False)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
