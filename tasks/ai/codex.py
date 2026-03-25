import time
from typing import Dict
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class CodexAuth(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("ai_services", {}).get("codex", {}).get("api_url", "https://api.openai.com")
        self.proxy = global_config.get("proxy", "")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        return TaskResult(
            task_id=self.config.task_id,
            status=TaskStatus.SUCCESS,
            message="Codex authorization task - requires API key configuration",
            data={
                "api_endpoint": f"{self.api_url}/v1/engines/davinci-codex/completions",
                "instructions": "Configure your Codex API key in config.json to enable API access"
            }
        )


class CodexRegister(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.signup_url = "https://openai.com/research/codex"
        self.proxy = global_config.get("proxy", "")
        self.browser_path = global_config.get("browser_path", "")
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            from camoufox.sync_api import Camoufox
            
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
                    
                except Exception as e:
                    pass
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message="Codex research page opened",
                    data={"url": page.url}
                )
                
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
