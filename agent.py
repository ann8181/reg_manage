"""
Agent - Unified API for Auto Register Tasks

统一的Agent接口，整合：
- Persona System (身份、代理、账号管理)
- Provider System (临时邮箱服务)
- Task System (任务执行)
- Logger System (日志和监控)
"""

import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from core.persona import PersonaSystem, create_persona_system
from core.providers.factory import ProviderFactory
from core.providers.chain import ProviderChain
from core.task_manager import TaskManager
from core.logger import get_task_logger, TaskLogger


class Agent:
    """
    统一Agent接口
    """
    
    _instance = None
    
    def __new__(cls, data_dir: str = "data"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init(data_dir)
        return cls._instance
    
    def _init(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.persona_dir = self.data_dir / "persona"
        self.results_dir = self.data_dir / "results"
        self.logs_dir = self.data_dir / "logs"
        
        self.persona_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.persona = create_persona_system(str(self.persona_dir))
        
        config_path = BASE_DIR / "config" / "tasks.json"
        global_config_path = BASE_DIR / "config.json"
        self.task_manager = TaskManager(str(config_path), str(global_config_path))
    
    def create_email(self, provider: str = "mailtm") -> Dict[str, Any]:
        """创建临时邮箱"""
        try:
            p = ProviderFactory.create(provider)
            email, password = p.create_email()
            return {
                "success": True,
                "email": email,
                "password": password,
                "provider": provider
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }
    
    def get_messages(self, email: str, provider: str = "mailtm") -> List[Dict]:
        """获取邮件列表"""
        try:
            p = ProviderFactory.create(provider)
            messages = p.get_messages(email)
            return [
                {
                    "id": msg.id,
                    "from": msg.from_addr,
                    "subject": msg.subject,
                    "body": msg.body,
                    "timestamp": msg.timestamp
                }
                for msg in messages
            ]
        except Exception as e:
            return []
    
    def get_verification_code(
        self,
        email: str,
        provider: str = "mailtm",
        subject_contains: str = "",
        max_wait: int = 120
    ) -> Optional[str]:
        """等待验证码"""
        try:
            p = ProviderFactory.create(provider)
            return p.get_verification_code(email, subject_contains, max_wait)
        except Exception:
            return None
    
    def generate_identity(
        self,
        country: str = "US",
        gender: Optional[str] = None
    ) -> Dict:
        """生成身份"""
        return self.persona.generate_identity(country=country, gender=gender)
    
    def get_proxy(self, country: Optional[str] = None) -> Optional[Dict]:
        """获取代理"""
        return self.persona.get_proxy(country=country)
    
    def register_account(
        self,
        service: str,
        email: str,
        password: str,
        username: Optional[str] = None,
        identity_id: Optional[str] = None
    ) -> Dict:
        """注册账号"""
        return self.persona.register_account(
            service=service,
            email=email,
            password=password,
            username=username,
            identity_id=identity_id
        )
    
    def get_account(self, service: str) -> Optional[Dict]:
        """获取可用账号"""
        return self.persona.get_available_account(service)
    
    def get_account_decrypted(self, service: str) -> Optional[Dict]:
        """获取账号并解密"""
        return self.persona.get_account_decrypted(service)
    
    def list_tasks(self) -> Dict[str, Any]:
        """列出所有任务"""
        enabled = len(self.task_manager.get_enabled_tasks())
        return {
            "total": len(self.task_manager.all_tasks),
            "enabled": enabled,
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "groups": [
                        {
                            "id": grp.id,
                            "name": grp.name,
                            "tasks": [
                                {"id": t.task_id, "name": t.name, "enabled": t.enabled}
                                for t in grp.tasks
                            ]
                        }
                        for grp in cat.groups
                    ]
                }
                for cat in self.task_manager.categories.values()
            ]
        }
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        task = self.task_manager.get_task(task_id)
        if task:
            self.task_manager.enable_task(task_id, True)
            self.task_manager.save_config()
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        task = self.task_manager.get_task(task_id)
        if task:
            self.task_manager.enable_task(task_id, False)
            self.task_manager.save_config()
            return True
        return False
    
    def run_task(self, task_id: str) -> Dict[str, Any]:
        """运行任务"""
        from core.executor import TaskExecutor
        
        task_config = self.task_manager.get_task(task_id)
        if not task_config:
            return {"success": False, "error": f"Task {task_id} not found"}
        
        executor = TaskExecutor(self.task_manager, max_workers=1)
        result = executor.execute_task_by_id(task_id)
        
        if result:
            return {
                "success": result.status.value == "success",
                "task_id": result.task_id,
                "status": result.status.value,
                "message": result.message,
                "error": result.error
            }
        return {"success": False, "error": "Execution failed"}
    
    def get_stats(self) -> Dict:
        """获取系统统计"""
        return self.persona.get_system_stats()
    
    def get_providers(self) -> List[str]:
        """获取可用Provider列表"""
        return ProviderFactory.get_provider_names()


def create_agent(data_dir: str = "data") -> Agent:
    """创建Agent实例"""
    return Agent(data_dir)


agent = create_agent()
