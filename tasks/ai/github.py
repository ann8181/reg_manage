import time
import random
import string
import secrets
from typing import Dict
from faker import Faker
from core.browser_task import BrowserTask
from core.base import TaskConfig, TaskResult, TaskStatus


class GitHubRegister(BrowserTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = global_config.get("ai_services", {}).get("github", {}).get("signup_url", "https://github.com/signup")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        fake = Faker()
        username = fake.user_name() + str(random.randint(100, 999))
        email = fake.email()
        password = self.generate_strong_password(14)
        
        self.log_action_start("github_register", f"Registering GitHub account: {email}")
        
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
                    
                    self.log_browser_fill("Username", username, mask=False)
                    self._page.get_by_role("textbox", name="Username").fill(username)
                    self._page.wait_for_timeout(500)
                    
                    self.log_browser_fill("Email", email, mask=False)
                    self._page.get_by_role("textbox", name="Email").fill(email)
                    self._page.wait_for_timeout(500)
                    
                    self.log_browser_click("Continue")
                    self._page.get_by_role("button", name="Continue").click()
                    time.sleep(2)
                    self.logger.take_screenshot("02_email_filled", self._page)
                    
                    self.log_browser_fill("Password", password, mask=False)
                    self._page.get_by_role("textbox", name="Password").fill(password)
                    self._page.wait_for_timeout(500)
                    
                    self.log_browser_click("Continue")
                    self._page.get_by_role("button", name="Continue").click()
                    time.sleep(2)
                    self.logger.take_screenshot("03_password_filled", self._page)
                    
                    self._page.get_by_role("textbox", name="Verify").wait_for(timeout=5000)
                    self.logger.take_screenshot("04_verification", self._page)
                    
                except Exception as e:
                    self.logger.error(f"Registration step failed: {str(e)}")
                    self.logger.take_screenshot("error", self._page)
                    raise
                
                self.save_account(email, password, username=username)
                self.logger.perf_metrics.end()
                
                self.log_action_end("github_register", f"GitHub registration started: {email}", True)
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"GitHub registration started: {email}",
                    data={"email": email, "username": username, "password": password}
                )
                
        except Exception as e:
            self.logger.error(f"GitHub registration failed: {str(e)}")
            self.logger.perf_metrics.end()
            self.log_action_end("github_register", str(e), False)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
