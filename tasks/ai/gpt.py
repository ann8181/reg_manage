import time
import httpx
from typing import Dict, Optional
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


class GPTWebRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = "https://chat.openai.com/auth/login"
        self.proxy = global_config.get("proxy", "")
        self.browser_path = global_config.get("browser_path", "")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            from faker import Faker
            fake = Faker()
            email = fake.email()
            
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
                    time.sleep(2)
                    
                    page.get_by_role("button", name="Log in").click()
                    time.sleep(1)
                    
                    page.get_by_role("textbox", name="Email").fill(email)
                    page.get_by_role("button", name="Continue").click()
                    time.sleep(2)
                    
                except Exception as e:
                    pass
                
                self.save_account(email, "")
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"GPT registration started: {email}",
                    data={"email": email}
                )
                
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
