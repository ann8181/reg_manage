import httpx
from typing import Optional
from dataclasses import dataclass


@dataclass
class CaptchaResult:
    text: str
    confidence: float = 1.0


class CaptchaSolver:
    def __init__(self, api_key: str):
        self.base_url = "https://optiic.dev/api"
        self.api_key = api_key
        self.client = httpx.Client(timeout=60.0)
    
    def solve(self, image_path: str) -> Optional[str]:
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {'api_key': self.api_key}
                response = self.client.post(
                    f"{self.base_url}/solve",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "").strip()
        except Exception as e:
            print(f"[CaptchaSolver] Solve error: {e}")
        return None
    
    def solve_url(self, image_url: str) -> Optional[str]:
        try:
            response = self.client.get(
                f"{self.base_url}/solve",
                params={
                    "url": image_url,
                    "api_key": self.api_key
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "").strip()
        except Exception as e:
            print(f"[CaptchaSolver] Solve URL error: {e}")
        return None
    
    def close(self):
        self.client.close()


class OptiicCaptchaTask:
    def __init__(self, config: dict, global_config: dict):
        self.config = config
        self.global_config = global_config
        self.api_key = global_config.get("captcha", {}).get("optiic_api_key", "")
    
    def execute(self, image_path: str) -> dict:
        if not self.api_key:
            return {"status": "failed", "message": "Optiic API key not configured"}
        
        try:
            solver = CaptchaSolver(self.api_key)
            result = solver.solve(image_path)
            solver.close()
            
            if result:
                return {
                    "status": "success",
                    "message": f"Captcha solved: {result}",
                    "data": {"captcha_text": result}
                }
            return {"status": "failed", "message": "Failed to solve captcha"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


def OptiicTask(config: dict, global_config: dict):
    return OptiicCaptchaTask(config, global_config)
