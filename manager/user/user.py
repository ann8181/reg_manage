"""
User Management - 用户管理
"""

import uuid
import hashlib
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class UserRole(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"


class UserStatus(Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"


@dataclass
class User:
    id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    
    permissions: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    max_tasks: int = 100
    max_concurrent: int = 5
    
    created_at: str = ""
    updated_at: str = ""
    last_login: str = ""
    login_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class UserManager:
    """
    用户管理器
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.users: Dict[str, User] = {}
        self._tokens: Dict[str, str] = {}  # token -> user_id
        
        if not self.users:
            self.create_user(
                username="admin",
                email="admin@localhost",
                password="admin123",
                role=UserRole.ADMIN
            )
    
    def _hash_password(self, password: str, salt: str = "") -> str:
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.VIEWER,
        **kwargs
    ) -> Optional[User]:
        if any(u.username == username or u.email == email for u in self.users.values()):
            return None
        
        user = User(
            id=str(uuid.uuid4())[:8],
            username=username,
            email=email,
            password_hash=self._hash_password(password),
            role=role,
            **kwargs
        )
        
        self.users[user.id] = user
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        for user in self.users.values():
            if user.username == username and user.password_hash == self._hash_password(password):
                user.last_login = datetime.now().isoformat()
                user.login_count += 1
                
                token = secrets.token_urlsafe(32)
                self._tokens[token] = user.id
                return token
        return None
    
    def validate_token(self, token: str) -> Optional[User]:
        user_id = self._tokens.get(token)
        if user_id:
            return self.users.get(user_id)
        return None
    
    def revoke_token(self, token: str):
        if token in self._tokens:
            del self._tokens[token]
    
    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def list_users(self) -> List[User]:
        return list(self.users.values())
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        user = self.users.get(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.now().isoformat()
        return user
    
    def delete_user(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        user = self.users.get(user_id)
        if not user:
            return False
        
        if user.role == UserRole.ADMIN:
            return True
        
        return permission in user.permissions
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_users": len(self.users),
            "by_role": {
                role.value: sum(1 for u in self.users.values() if u.role == role)
                for role in UserRole
            }
        }


def get_user_manager() -> UserManager:
    return UserManager()
