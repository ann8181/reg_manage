from typing import Dict
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus
from core.providers.mailtm import MailTmProvider


class MailTmTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("email_providers", {}).get("mailtm", {}).get("api_url", "https://api.mail.tm")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = MailTmProvider(self.api_url)
            
            self.logger.log_action_start("create_email", "Creating temporary email")
            email, password = self.provider.create_email()
            
            if not email:
                self.logger.log_action_end("create_email", "Failed to create email", False)
                return TaskResult(
                    task_id=self.config.task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to create email"
                )
            
            self.logger.log_action_end("create_email", f"Email created: {email}", True)
            self.save_account(email, password)
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"Email created: {email}",
                data={"email": email, "password": password}
            )
            
        except Exception as e:
            self.logger.error(f"MailTm task failed: {str(e)}")
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
