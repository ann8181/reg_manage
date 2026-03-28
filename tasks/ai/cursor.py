import time
from typing import Dict
from faker import Faker
from core.browser_task import BrowserTask
from core.base import TaskConfig, TaskResult, TaskStatus


class CursorRegister(BrowserTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = global_config.get("ai_services", {}).get("cursor", {}).get("signup_url", "https://cursor.sh")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        fake = Faker()
        email = fake.email()
        
        self.log_action_start("cursor_register", f"Registering Cursor account: {email}")
        
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
                    
                    self.log_browser_click("Sign Up")
                    self._page.get_by_role("button", name="Sign Up").click()
                    time.sleep(1)
                    self.logger.take_screenshot("02_signup_form", self._page)
                    
                    self.log_browser_fill("Email", email, mask=False)
                    self._page.get_by_role("textbox", name="Email").fill(email)
                    self._page.wait_for_timeout(500)
                    
                    self.log_browser_click("Continue")
                    self._page.get_by_role("button", name="Continue").click()
                    time.sleep(2)
                    self.logger.take_screenshot("03_email_filled", self._page)
                    
                except Exception as e:
                    self.logger.error(f"Registration step failed: {str(e)}")
                    self.logger.take_screenshot("error", self._page)
                    raise
                
                self.save_account(email, "")
                self.logger.perf_metrics.end()
                self.log_action_end("cursor_register", f"Cursor registration started: {email}", True)
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"Cursor registration started: {email}",
                    data={"email": email}
                )
                
        except Exception as e:
            self.logger.error(f"Cursor registration failed: {str(e)}")
            self.logger.perf_metrics.end()
            self.log_action_end("cursor_register", str(e), False)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
