import time
import httpx
from typing import Dict, List, Optional
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class OpenRelayProvider:
    API_URL = "https://openrelay.ai"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def get_models(self) -> List[Dict]:
        try:
            response = self.client.get(f"{self.API_URL}/models")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[OpenRelay] Get models error: {e}")
        return []
    
    def get_status(self) -> Dict:
        try:
            response = self.client.get(f"{self.API_URL}/status")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[OpenRelay] Get status error: {e}")
        return {}
    
    def close(self):
        self.client.close()


class OpenRelayTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = OpenRelayProvider()
            status = self.provider.get_status()
            models = self.provider.get_models()
            
            self.logger.info(f"OpenRelay status: {status}")
            
            self.save_account(
                "openrelay",
                "",
                status=str(status),
                models_count=str(len(models))
            )
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"OpenRelay connected, {len(models)} models available",
                data={"models_count": len(models), "status": status}
            )
            
        except Exception as e:
            self.logger.error(f"OpenRelay error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
