import time
import httpx
from typing import Dict, Optional
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class TempMailConverter(BaseTask):
    TEMP_MAIL_SERVICES = {
        "temp-mail-asia": {
            "name": "Temp Mail Asia",
            "api_url": "https://www.v3.temp-mail.asia"
        },
        "temp-mail-awsl": {
            "name": "Temp Mail Awsl",
            "api_url": "https://temp-mail.awsl.uk"
        },
        "guerrilla-mail": {
            "name": "Guerrilla Mail",
            "api_url": "https://api.guerrillamail.com"
        },
        "maildrop": {
            "name": "MailDrop",
            "api_url": "https://api.maildrop.cc"
        }
    }
    
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider_type = global_config.get("temp_email_provider", "temp-mail-asia")
        self.provider_url = self.TEMP_MAIL_SERVICES.get(self.provider_type, {}).get("api_url", "")
        self.jwt_password = global_config.get("temp_mail_awsl_jwt", "")
    
    def validate(self) -> bool:
        return True
    
    def convert_web_to_api(self) -> Dict:
        result = {
            "provider": self.provider_type,
            "api_url": self.provider_url,
            "converted": False,
            "email": "",
            "instructions": ""
        }
        
        if self.provider_type == "temp-mail-asia":
            result["converted"] = True
            result["instructions"] = "直接使用 POST /random-email 接口生成随机邮箱"
            result["example"] = "curl -X POST https://www.v3.temp-mail.asia/random-email"
        
        elif self.provider_type == "temp-mail-awsl":
            result["converted"] = True
            result["instructions"] = "使用自部署的 Cloudflare Workers API"
            result["example"] = f"GET {self.provider_url}/open_api/settings (需要 JWT)"
        
        elif self.provider_type == "guerrilla-mail":
            result["converted"] = True
            result["instructions"] = "GET /api/v2/get_email_address/ 获取邮箱地址"
            result["example"] = "curl https://api.guerrillamail.com/api/v2/get_email_address/"
        
        elif self.provider_type == "maildrop":
            result["converted"] = True
            result["instructions"] = "直接使用 address@maildrop.cc 格式，无需注册"
            result["example"] = "curl https://api.maildrop.cc/api/messages/{address}"
        
        return result
    
    def execute(self) -> TaskResult:
        try:
            conversion_result = self.convert_web_to_api()
            
            if conversion_result["converted"]:
                self.save_account(
                    conversion_result["provider"],
                    conversion_result["api_url"],
                    instructions=conversion_result["instructions"],
                    example=conversion_result["example"]
                )
                
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.SUCCESS,
                    message=f"Converted {conversion_result['provider']} to API format",
                    data=conversion_result
                )
            else:
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message=f"Failed to convert {self.provider_type}"
                )
                
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )


class TenMinuteMailTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = "https://10minutemail.com"
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            import httpx
            client = httpx.Client(timeout=30.0)
            
            session = client.get(f"{self.api_url}/address/create.json")
            if session.status_code == 200:
                data = session.json()
                email = data.get("email", {}).get("address", "")
                session_id = data.get("email", {}).get("session_id", "")
                
                if email:
                    self.save_account(email, "", session_id=session_id)
                    
                    return TaskResult(
                        task_id=self.config.task_id,
                        status=TaskStatus.SUCCESS,
                        message=f"10MinuteMail created: {email}",
                        data={"email": email, "session_id": session_id}
                    )
            
            client.close()
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                message="Failed to create 10MinuteMail"
            )
            
        except Exception as e:
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
