import time
import httpx
from typing import Dict
from core.browser_task import BrowserTask
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class GPTRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("ai_services", {}).get("gpt", {}).get("api_url", "https://api.openai.com")
        self.proxy = global_config.get("proxy", "")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            client = httpx.Client(timeout=30.0)
            
            response = client.get(f"{self.api_url}/v1/models")
            
            if response.status_code == 200:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message="GPT API is accessible",
                    data={"status": "api_available"}
                )
            else:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message=f"GPT API returned status {response.status_code}"
                )
            
            client.close()
                
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )


class GPTWebRegister(BrowserTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = "https://chat.openai.com/auth/login"
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        from faker import Faker
        fake = Faker()
        email = fake.email()
        
        self.log_action_start("gpt_register", f"Registering GPT account: {email}")
        
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
                    self.logger.take_screenshot("01_login_page", self._page)
                    
                    self.log_browser_click("Log in")
                    self._page.get_by_role("button", name="Log in").click()
                    time.sleep(1)
                    self.logger.take_screenshot("02_after_login_click", self._page)
                    
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
                self.log_action_end("gpt_register", f"GPT registration started: {email}", True)
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"GPT registration started: {email}",
                    data={"email": email}
                )
                
        except Exception as e:
            self.logger.error(f"GPT registration failed: {str(e)}")
            self.logger.perf_metrics.end()
            self.log_action_end("gpt_register", str(e), False)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
