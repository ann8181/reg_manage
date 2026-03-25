import time
import httpx
from typing import Dict, List
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class FreeApiHubProvider:
    API_URL = "https://api.free-api-hub.com"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def get_services(self) -> List[Dict]:
        try:
            response = self.client.get(f"{self.API_URL}/services")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[FreeApiHub] Get services error: {e}")
        return []
    
    def get_free_apis(self) -> Dict:
        try:
            response = self.client.get(f"{self.API_URL}/free-apis")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[FreeApiHub] Get free APIs error: {e}")
        return {}
    
    def close(self):
        self.client.close()


class FreeApiHubTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = FreeApiHubProvider()
            apis = self.provider.get_free_apis()
            
            self.logger.info(f"FreeApiHub: {len(apis)} free APIs available")
            
            self.save_account(
                "freeapihub",
                "",
                apis_count=str(len(apis))
            )
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"FreeApiHub: {len(apis)} free APIs available",
                data={"apis_count": len(apis)}
            )
            
        except Exception as e:
            self.logger.error(f"FreeApiHub error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
