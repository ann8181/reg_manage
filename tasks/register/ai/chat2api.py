import time
import httpx
from typing import Dict, List
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class Chat2ApiProvider:
    API_URL = "https://api.chat2api.cn"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def get_available_models(self) -> List[str]:
        try:
            response = self.client.get(f"{self.API_URL}/models")
            if response.status_code == 200:
                return response.json().get("models", [])
        except Exception as e:
            print(f"[Chat2Api] Get models error: {e}")
        return []
    
    def get_status(self) -> Dict:
        try:
            response = self.client.get(f"{self.API_URL}/status")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[Chat2Api] Get status error: {e}")
        return {}
    
    def close(self):
        self.client.close()


class Chat2ApiTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = Chat2ApiProvider()
            models = self.provider.get_available_models()
            status = self.provider.get_status()
            
            self.logger.info(f"Chat2Api: {len(models)} models available")
            
            self.save_account(
                "chat2api",
                "",
                models_count=str(len(models)),
                status=str(status)
            )
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"Chat2Api: {len(models)} models available",
                data={"models_count": len(models), "status": status}
            )
            
        except Exception as e:
            self.logger.error(f"Chat2Api error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
