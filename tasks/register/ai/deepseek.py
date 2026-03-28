import time
from typing import Dict
from faker import Faker
from core.browser_task import BrowserTask
from core.base import TaskConfig, TaskResult, TaskStatus


class DeepSeekRegister(BrowserTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = global_config.get("ai_services", {}).get("deepseek", {}).get("signup_url", "https://platform.deepseek.com")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        fake = Faker()
        email = fake.email()
        
        self.log_action_start("deepseek_register", f"Registering DeepSeek account: {email}")
        
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
                    
                    self.log_browser_click("Sign In")
                    self._page.get_by_role("link", name="Sign In").click()
                    time.sleep(1)
                    self.logger.take_screenshot("02_signin_page", self._page)
                    
                    self.log_browser_click("Sign up")
                    self._page.get_by_role("link", name="Sign up").click()
                    time.sleep(1)
                    self.logger.take_screenshot("03_signup_page", self._page)
                    
                    self.log_browser_fill("Email", email, mask=False)
                    self._page.get_by_role("textbox", name="Email").fill(email)
                    self._page.wait_for_timeout(500)
                    
                    self.log_browser_click("Continue")
                    self._page.get_by_role("button", name="Continue").click()
                    time.sleep(2)
                    self.logger.take_screenshot("04_email_filled", self._page)
                    
                except Exception as e:
                    self.logger.error(f"Registration step failed: {str(e)}")
                    self.logger.take_screenshot("error", self._page)
                    raise
                
                self.save_account(email, "")
                self.logger.perf_metrics.end()
                self.log_action_end("deepseek_register", f"DeepSeek registration started: {email}", True)
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"DeepSeek registration started: {email}",
                    data={"email": email}
                )
                
        except Exception as e:
            self.logger.error(f"DeepSeek registration failed: {str(e)}")
            self.logger.perf_metrics.end()
            self.log_action_end("deepseek_register", str(e), False)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
