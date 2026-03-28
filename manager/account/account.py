"""
Account Management - 统一账号管理
"""

import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AccountType(Enum):
    PERSONAL = "personal"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class AccountStatus(Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"


@dataclass
class Account:
    id: str
    name: str
    account_type: AccountType
    owner_id: str
    status: AccountStatus = AccountStatus.ACTIVE
    
    members: List[str] = field(default_factory=list)
    quotas: Dict[str, int] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class AccountManager:
    """
    账号管理器
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.accounts: Dict[str, Account] = {}
        self._user_accounts: Dict[str, List[str]] = {}  # user_id -> [account_ids]
    
    def create_account(
        self,
        name: str,
        account_type: AccountType,
        owner_id: str,
        **kwargs
    ) -> Account:
        account = Account(
            id=str(uuid.uuid4())[:8],
            name=name,
            account_type=account_type,
            owner_id=owner_id,
            **kwargs
        )
        
        self.accounts[account.id] = account
        
        if owner_id not in self._user_accounts:
            self._user_accounts[owner_id] = []
        self._user_accounts[owner_id].append(account.id)
        
        return account
    
    def get_account(self, account_id: str) -> Optional[Account]:
        return self.accounts.get(account_id)
    
    def get_user_accounts(self, user_id: str) -> List[Account]:
        account_ids = self._user_accounts.get(user_id, [])
        return [self.accounts[aid] for aid in account_ids if aid in self.accounts]
    
    def add_member(self, account_id: str, user_id: str) -> bool:
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        if user_id not in account.members:
            account.members.append(user_id)
            
            if user_id not in self._user_accounts:
                self._user_accounts[user_id] = []
            if account_id not in self._user_accounts[user_id]:
                self._user_accounts[user_id].append(account_id)
        
        return True
    
    def remove_member(self, account_id: str, user_id: str) -> bool:
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        if user_id in account.members:
            account.members.remove(user_id)
        
        if user_id in self._user_accounts:
            if account_id in self._user_accounts[user_id]:
                self._user_accounts[user_id].remove(account_id)
        
        return True
    
    def list_accounts(self) -> List[Account]:
        return list(self.accounts.values())
    
    def update_account(self, account_id: str, **kwargs) -> Optional[Account]:
        account = self.accounts.get(account_id)
        if account:
            for key, value in kwargs.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            account.updated_at = datetime.now().isoformat()
        return account
    
    def delete_account(self, account_id: str) -> bool:
        if account_id in self.accounts:
            account = self.accounts[account_id]
            
            for user_id in account.members:
                if user_id in self._user_accounts:
                    if account_id in self._user_accounts[user_id]:
                        self._user_accounts[user_id].remove(account_id)
            
            del self.accounts[account_id]
            return True
        return False


def get_account_manager() -> AccountManager:
    return AccountManager()
