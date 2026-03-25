import time
import base64
import httpx
from typing import Optional, Dict
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class TwoCaptchaProvider:
    API_URL = "https://2captcha.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(timeout=60.0)
    
    def solve_image(self, image_base64: str) -> Optional[str]:
        try:
            response = self.client.get(
                f"{self.API_URL}/in.php",
                params={
                    "key": self.api_key,
                    "method": "base64",
                    "body": image_base64,
                    "json": 1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    captcha_id = data.get("request")
                    return self._poll_result(captcha_id)
        except Exception as e:
            print(f"[2Captcha] Solve image error: {e}")
        return None
    
    def solve_recaptcha(self, site_key: str, url: str) -> Optional[str]:
        try:
            response = self.client.get(
                f"{self.API_URL}/in.php",
                params={
                    "key": self.api_key,
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": url,
                    "json": 1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    captcha_id = data.get("request")
                    return self._poll_result(captcha_id)
        except Exception as e:
            print(f"[2Captcha] Solve recaptcha error: {e}")
        return None
    
    def _poll_result(self, captcha_id: str, max_wait: int = 120) -> Optional[str]:
        for _ in range(max_wait // 10):
            try:
                response = self.client.get(
                    f"{self.API_URL}/res.php",
                    params={
                        "key": self.api_key,
                        "action": "get",
                        "id": captcha_id,
                        "json": 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == 1:
                        return data.get("request")
                    elif data.get("request") != "CAPCHA_NOT_READY":
                        break
            except Exception as e:
                print(f"[2Captcha] Poll result error: {e}")
            
            time.sleep(10)
        
        return None
    
    def get_balance(self) -> Optional[float]:
        try:
            response = self.client.get(
                f"{self.API_URL}/res.php",
                params={
                    "key": self.api_key,
                    "action": "getbalance",
                    "json": 1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    return float(data.get("request"))
        except Exception as e:
            print(f"[2Captcha] Get balance error: {e}")
        return None
    
    def close(self):
        self.client.close()


class TwoCaptchaTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_key = global_config.get("captcha_services", {}).get("2captcha", {}).get("api_key", "")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            if not self.api_key:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="2Captcha API key not configured"
                )
            
            self.provider = TwoCaptchaProvider(self.api_key)
            balance = self.provider.get_balance()
            
            if balance is not None:
                self.logger.info(f"2Captcha balance: ${balance}")
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"2Captcha connected, balance: ${balance}",
                    data={"balance": balance}
                )
            else:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to get 2Captcha balance"
                )
            
        except Exception as e:
            self.logger.error(f"2Captcha error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()


class AntiCaptchaProvider:
    API_URL = "https://api.anti-captcha.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(timeout=60.0)
    
    def solve_image(self, image_base64: str) -> Optional[str]:
        try:
            response = self.client.post(
                f"{self.API_URL}/createTask",
                json={
                    "clientKey": self.api_key,
                    "task": {
                        "type": "ImageToTextTask",
                        "body": image_base64
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("taskId")
                if task_id:
                    return self._poll_result(task_id)
        except Exception as e:
            print(f"[AntiCaptcha] Solve image error: {e}")
        return None
    
    def solve_recaptcha(self, site_key: str, url: str) -> Optional[str]:
        try:
            response = self.client.post(
                f"{self.API_URL}/createTask",
                json={
                    "clientKey": self.api_key,
                    "task": {
                        "type": "RecaptchaV2TaskProxyless",
                        "websiteKey": site_key,
                        "websiteURL": url
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("taskId")
                if task_id:
                    return self._poll_result(task_id)
        except Exception as e:
            print(f"[AntiCaptcha] Solve recaptcha error: {e}")
        return None
    
    def _poll_result(self, task_id: str, max_wait: int = 120) -> Optional[str]:
        for _ in range(max_wait // 5):
            try:
                response = self.client.post(
                    f"{self.API_URL}/getTaskResult",
                    json={"clientKey": self.api_key, "taskId": task_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ready":
                        return data.get("solution", {}).get("text")
            except Exception as e:
                print(f"[AntiCaptcha] Poll result error: {e}")
            
            time.sleep(5)
        
        return None
    
    def get_balance(self) -> Optional[float]:
        try:
            response = self.client.post(
                f"{self.API_URL}/getBalance",
                json={"clientKey": self.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("balance")
        except Exception as e:
            print(f"[AntiCaptcha] Get balance error: {e}")
        return None
    
    def close(self):
        self.client.close()


class AntiCaptchaTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_key = global_config.get("captcha_services", {}).get("anticaptcha", {}).get("api_key", "")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            if not self.api_key:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="AntiCaptcha API key not configured"
                )
            
            self.provider = AntiCaptchaProvider(self.api_key)
            balance = self.provider.get_balance()
            
            if balance is not None:
                self.logger.info(f"AntiCaptcha balance: ${balance}")
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"AntiCaptcha connected, balance: ${balance}",
                    data={"balance": balance}
                )
            else:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to get AntiCaptcha balance"
                )
            
        except Exception as e:
            self.logger.error(f"AntiCaptcha error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
