"""
Account Module - 外部服务账号模块
管理 AI 服务、邮箱、代理等外部账号配置
"""

import uuid
import secrets
from typing import Dict, List, Optional, Any


class AccountType:
    AI_SERVICE = "ai_service"
    EMAIL = "email"
    PROXY = "proxy"
    CAPTCHA = "captcha"
    CUSTOM = "custom"


class AccountStatus:
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"
    QUOTA_EXCEEDED = "quota_exceeded"


class Account:
    """外部服务账号"""
    
    def __init__(
        self,
        id: str = None,
        name: str = "",
        account_type: str = AccountType.AI_SERVICE,
        provider: str = "",
        credentials: Dict[str, str] = None,
        config: Dict[str, Any] = None,
        enabled: bool = True,
        **kwargs
    ):
        self.id = id or str(uuid.uuid4())[:8]
        self.name = name
        self.account_type = account_type
        self.provider = provider
        self.credentials = credentials or {}
        self.config = config or {}
        self.status = AccountStatus.ACTIVE
        self.enabled = enabled
        self.quota = kwargs.get("quota", {})
        self.usage = kwargs.get("usage", {})
        self.created_at = kwargs.get("created_at", "")
        self.updated_at = kwargs.get("updated_at", "")
        self.expires_at = kwargs.get("expires_at", None)
        self.metadata = kwargs.get("metadata", {})
    
    def to_dict(self, safe: bool = True) -> Dict:
        """转字典，credentials 默认不暴露"""
        data = {
            "id": self.id,
            "name": self.name,
            "account_type": self.account_type,
            "provider": self.provider,
            "config": self.config,
            "status": self.status,
            "enabled": self.enabled,
            "quota": self.quota,
            "usage": self.usage,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }
        if not safe:
            data["credentials"] = self.credentials
        return data
    
    def check_quota(self, action: str = "default") -> bool:
        """检查配额"""
        if self.quota.get(action, -1) == -1:
            return True
        current = self.usage.get(action, 0)
        return current < self.quota[action]
    
    def increment_usage(self, action: str = "default", amount: int = 1):
        """增加使用量"""
        self.usage[action] = self.usage.get(action, 0) + amount


class AccountModule:
    """
    外部服务账号模块
    统一管理 AI 服务、邮箱、代理等外部账号配置
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.accounts: Dict[str, Account] = {}
        self.logger = kernel.get_logger("account")
        self.logger.info("AccountModule initialized")
    
    def create_account(
        self,
        name: str,
        account_type: str = AccountType.AI_SERVICE,
        provider: str = "",
        credentials: Dict[str, str] = None,
        config: Dict[str, Any] = None,
        **kwargs
    ) -> Account:
        """创建账号"""
        account = Account(
            name=name,
            account_type=account_type,
            provider=provider,
            credentials=credentials,
            config=config,
            **kwargs
        )
        self.accounts[account.id] = account
        self.logger.info(f"Account created: {name} ({account_type})")
        return account
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """获取账号"""
        return self.accounts.get(account_id)
    
    def get_accounts_by_type(self, account_type: str) -> List[Account]:
        """按类型获取账号"""
        return [a for a in self.accounts.values() if a.account_type == account_type]
    
    def get_accounts_by_provider(self, provider: str) -> List[Account]:
        """按提供商获取账号"""
        return [a for a in self.accounts.values() if a.provider == provider]
    
    def get_enabled_account(self, account_type: str = None, provider: str = None) -> Optional[Account]:
        """获取第一个可用的账号"""
        for account in self.accounts.values():
            if not account.enabled:
                continue
            if account.status != AccountStatus.ACTIVE:
                continue
            if account_type and account.account_type != account_type:
                continue
            if provider and account.provider != provider:
                continue
            return account
        return None
    
    def list_accounts(self, account_type: str = None, enabled_only: bool = False) -> List[Account]:
        """列出账号"""
        accounts = list(self.accounts.values())
        if account_type:
            accounts = [a for a in accounts if a.account_type == account_type]
        if enabled_only:
            accounts = [a for a in accounts if a.enabled]
        return accounts
    
    def update_account(self, account_id: str, **kwargs) -> Optional[Account]:
        """更新账号"""
        account = self.accounts.get(account_id)
        if not account:
            return None
        
        for key, value in kwargs.items():
            if key == "credentials":
                account.credentials.update(value)
            elif key == "config":
                account.config.update(value)
            elif hasattr(account, key):
                setattr(account, key, value)
        
        account.updated_at = ""
        self.logger.info(f"Account updated: {account.name}")
        return account
    
    def delete_account(self, account_id: str) -> bool:
        """删除账号"""
        if account_id in self.accounts:
            account = self.accounts[account_id]
            del self.accounts[account_id]
            self.logger.info(f"Account deleted: {account.name}")
            return True
        return False
    
    def enable_account(self, account_id: str) -> bool:
        """启用账号"""
        account = self.accounts.get(account_id)
        if account:
            account.enabled = True
            return True
        return False
    
    def disable_account(self, account_id: str) -> bool:
        """禁用账号"""
        account = self.accounts.get(account_id)
        if account:
            account.enabled = False
            return True
        return False
    
    def validate_account(self, account_id: str) -> Dict[str, Any]:
        """验证账号是否有效"""
        account = self.accounts.get(account_id)
        if not account:
            return {"valid": False, "reason": "Account not found"}
        if not account.enabled:
            return {"valid": False, "reason": "Account is disabled"}
        if account.status == AccountStatus.EXPIRED:
            return {"valid": False, "reason": "Account is expired"}
        if account.status == AccountStatus.QUOTA_EXCEEDED:
            return {"valid": False, "reason": "Account quota exceeded"}
        return {"valid": True, "account": account}
    
    def stop(self):
        """停止模块"""
        self.logger.info("AccountModule stopped")
