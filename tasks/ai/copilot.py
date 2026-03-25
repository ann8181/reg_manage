import time
from typing import Dict
from faker import Faker
from camoufox.sync_api import Camoufox
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class CopilotRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = global_config.get("ai_services", {}).get("copilot", {}).get("signup_url", "https://github.com/features/copilot")
        self.proxy = global_config.get("proxy", "")
        self.browser_path = global_config.get("browser_path", "")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
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
                    time.sleep(2)
                    
                    page.get_by_role("link", name="Sign up for Copilot").click()
                    time.sleep(2)
                    
                    page.wait_for_url("**/copilot**", timeout=10000)
                    
                except Exception as e:
                    pass
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message="Copilot registration page opened",
                    data={"url": page.url}
                )
                
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
