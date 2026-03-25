import time
from typing import Dict
from faker import Faker
from camoufox.sync_api import Camoufox
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class MistralRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = global_config.get("ai_services", {}).get("mistral", {}).get("signup_url", "https://mistral.ai")
        self.proxy = global_config.get("proxy", "")
        self.browser_path = global_config.get("browser_path", "")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        fake = Faker()
        email = fake.email()
        
        try:
            launch_opts = {'headless': True}
            if self.proxy:
                launch_opts['proxy'] = self.proxy
            if self.browser_path:
                launch_opts['browser_path'] = self.browser_path
            
            with Camoufox(**launch_opts) as browser:
                self._page = browser.new_page()
                
                try:
                    self.logger.info("Navigating to Mistral signup page...")
                    self._page.goto(self.signup_url, timeout=30000)
                    self._page.wait_for_load_state("domcontentloaded")
                    time.sleep(2)
                    self.take_screenshot("01_home_page")
                    
                    self._page.get_by_role("link", name="Sign In").click()
                    time.sleep(1)
                    
                    self._page.get_by_role("link", name="Create account").click()
                    time.sleep(1)
                    
                    self._page.get_by_role("textbox", name="Email").fill(email)
                    self._page.get_by_role("button", name="Continue").click()
                    time.sleep(2)
                    self.take_screenshot("02_email_filled")
                    
                except Exception as e:
                    self.logger.error(f"Registration step failed: {str(e)}")
                    self.take_error_screenshot()
                
                self.save_account(email, "")
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"Mistral registration started: {email}",
                    data={"email": email}
                )
                
        except Exception as e:
            self.logger.error(f"Mistral registration failed: {str(e)}", e)
            self.take_error_screenshot()
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            self.close_browser()
