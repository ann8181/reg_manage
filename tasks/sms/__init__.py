import time
import httpx
from typing import List, Dict, Optional
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class FreeOtpApiProvider:
    API_URL = "https://free-otp-api-8e544c41220a.herokuapp.com"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self.phone = ""
        self.otp_id = ""
    
    def get_numbers(self) -> List[Dict]:
        try:
            response = self.client.get(f"{self.API_URL}/numbers")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[FreeOtpApi] Get numbers error: {e}")
        return []
    
    def request_otp(self, phone: str, service: str = "whatsapp") -> Optional[str]:
        try:
            response = self.client.post(
                f"{self.API_URL}/request",
                json={"phone": phone, "service": service}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("id")
        except Exception as e:
            print(f"[FreeOtpApi] Request OTP error: {e}")
        return None
    
    def get_otp(self, otp_id: str, max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = self.client.get(f"{self.API_URL}/otp/{otp_id}")
                if response.status_code == 200:
                    data = response.json()
                    otp = data.get("otp")
                    if otp:
                        return otp
            except Exception as e:
                print(f"[FreeOtpApi] Get OTP error: {e}")
            time.sleep(10)
        return None
    
    def close(self):
        self.client.close()


class FreeOtpApiTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = FreeOtpApiProvider()
            
            numbers = self.provider.get_numbers()
            if not numbers:
                self.logger.warning("No phone numbers available")
            
            self.logger.info(f"FreeOtpApi connected, {len(numbers)} numbers available")
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"FreeOtpApi connected, {len(numbers)} numbers available",
                data={"available_numbers": len(numbers)}
            )
            
        except Exception as e:
            self.logger.error(f"FreeOtpApi error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()


class OtpGatewayProvider:
    def __init__(self, api_url: str = "http://localhost:9000"):
        self.api_url = api_url
        self.client = httpx.Client(timeout=30.0)
    
    def get_services(self) -> List[Dict]:
        try:
            response = self.client.get(f"{self.api_url}/services")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[OtpGateway] Get services error: {e}")
        return []
    
    def get_number(self, service: str) -> Optional[Dict]:
        try:
            response = self.client.post(
                f"{self.api_url}/number",
                json={"service": service}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[OtpGateway] Get number error: {e}")
        return None
    
    def get_otp(self, number_id: str, max_wait: int = 120) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = self.client.get(f"{self.api_url}/otp/{number_id}")
                if response.status_code == 200:
                    data = response.json()
                    otp = data.get("otp")
                    if otp:
                        return otp
            except Exception as e:
                print(f"[OtpGateway] Get OTP error: {e}")
            time.sleep(10)
        return None
    
    def release_number(self, number_id: str):
        try:
            self.client.delete(f"{self.api_url}/number/{number_id}")
        except Exception as e:
            print(f"[OtpGateway] Release number error: {e}")
    
    def close(self):
        self.client.close()


class OtpGatewayTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("sms_services", {}).get("otpgateway", {}).get("api_url", "http://localhost:9000")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = OtpGatewayProvider(self.api_url)
            
            services = self.provider.get_services()
            self.logger.info(f"OtpGateway connected, services: {services}")
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"OtpGateway connected",
                data={"services": services}
            )
            
        except Exception as e:
            self.logger.error(f"OtpGateway error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
