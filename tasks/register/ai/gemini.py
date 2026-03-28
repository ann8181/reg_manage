import time
from typing import Dict
from core.browser_task import BrowserTask
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class GeminiRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("ai_services", {}).get("gemini", {}).get("api_url", "https://generativelanguage.googleapis.com")
        self.proxy = global_config.get("proxy", "")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        return TaskResult(
            task_id=self.config.task_id,
            status=TaskStatus.SUCCESS,
            message="Gemini API registration task",
            data={
                "api_endpoint": f"{self.api_url}/v1beta/models",
                "instructions": "Visit https://aistudio.google.com to get your API key"
            }
        )


class GeminiWebRegister(BrowserTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = "https://ai.google.dev"
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        from faker import Faker
        fake = Faker()
        email = fake.email()
        
        self.log_action_start("gemini_register", f"Registering Gemini account: {email}")
        
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
                    self.logger.take_screenshot("01_home_page", self._page)
                    
                    self.log_browser_click("Get API Key")
                    self._page.get_by_role("link", name="Get API Key").click()
                    time.sleep(2)
                    self.logger.take_screenshot("02_api_key_page", self._page)
                    
                except Exception as e:
                    self.logger.error(f"Registration step failed: {str(e)}")
                    self.logger.take_screenshot("error", self._page)
                    raise
                
                self.save_account(email, "")
                self.logger.perf_metrics.end()
                self.log_action_end("gemini_register", f"Gemini registration started: {email}", True)
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"Gemini registration page opened: {email}",
                    data={"email": email}
                )
                
        except Exception as e:
            self.logger.error(f"Gemini registration failed: {str(e)}")
            self.logger.perf_metrics.end()
            self.log_action_end("gemini_register", str(e), False)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
