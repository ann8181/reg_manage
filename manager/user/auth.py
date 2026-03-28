"""
Authentication - 认证管理
"""

import secrets
import hashlib
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Token:
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def is_expired(self) -> bool:
        created = datetime.fromisoformat(self.created_at)
        expires_at = created + timedelta(seconds=self.expires_in)
        return datetime.now() > expires_at


class AuthManager:
    """
    认证管理器
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}
        self._token_metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_token_pair(self, user_id: str) -> Token:
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        self._refresh_tokens[refresh_token] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
        
        self._token_metadata[access_token] = {
            "user_id": user_id,
            "refresh_token": refresh_token,
            "created_at": datetime.now().isoformat()
        }
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    def validate_access_token(self, token: str) -> Optional[str]:
        metadata = self._token_metadata.get(token)
        if not metadata:
            return None
        
        return metadata.get("user_id")
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Token]:
        token_data = self._refresh_tokens.get(refresh_token)
        if not token_data:
            return None
        
        user_id = token_data["user_id"]
        return self.create_token_pair(user_id)
    
    def revoke_token(self, token: str):
        if token in self._token_metadata:
            refresh_token = self._token_metadata[token].get("refresh_token")
            if refresh_token and refresh_token in self._refresh_tokens:
                del self._refresh_tokens[refresh_token]
            del self._token_metadata[token]
    
    def revoke_all_user_tokens(self, user_id: str):
        tokens_to_remove = [
            token for token, meta in self._token_metadata.items()
            if meta.get("user_id") == user_id
        ]
        for token in tokens_to_remove:
            self.revoke_token(token)


def get_auth_manager() -> AuthManager:
    return AuthManager()
