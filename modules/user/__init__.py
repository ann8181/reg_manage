"""
User Module - 用户权限模块
用户管理和认证
"""

import uuid
import secrets
from typing import Dict, List, Optional

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


class UserRole:
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"


class UserStatus:
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"


class User:
    def __init__(
        self,
        id: str = None,
        username: str = "",
        email: str = "",
        password: str = "",
        role: str = UserRole.VIEWER,
        **kwargs
    ):
        self.id = id or str(uuid.uuid4())[:8]
        self.username = username
        self.email = email
        self.password_hash = self._hash_password(password)
        self.role = role
        self.status = UserStatus.ACTIVE
        self.permissions = kwargs.get("permissions", [])
        self.max_tasks = kwargs.get("max_tasks", 100)
        self.max_concurrent = kwargs.get("max_concurrent", 5)
        self.created_at = kwargs.get("created_at", "")
        self.last_login = None
        self.login_count = 0
    
    def _hash_password(self, password: str) -> str:
        if not password:
            return ""
        if HAS_BCRYPT:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        import hashlib
        import base64
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update(f"{password}{salt}".encode('utf-8'))
        return f"{base64.b64encode(salt.encode()).decode()}:{hash_obj.hexdigest()}"
    
    def check_password(self, password: str) -> bool:
        if not password or not self.password_hash:
            return False
        if HAS_BCRYPT and self.password_hash.startswith('$2'):
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        if ':' in self.password_hash:
            try:
                salt_b64, stored_hash = self.password_hash.split(':')
                import hashlib
                import base64
                salt = base64.b64decode(salt_b64.encode()).decode()
                hash_obj = hashlib.sha256()
                hash_obj.update(f"{password}{salt}".encode('utf-8'))
                return hash_obj.hexdigest() == stored_hash
            except Exception:
                return False
        return False
    
    def to_dict(self, safe: bool = True) -> Dict:
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "status": self.status
        }
        if not safe:
            data["password_hash"] = self.password_hash
        return data


class UserModule:
    """
    用户权限模块
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.users: Dict[str, User] = {}
        self.tokens: Dict[str, str] = {}  # token -> user_id
        self.logger = kernel.get_logger("user")
        
        # 创建默认管理员
        if not self.users:
            self.create_user("admin", "admin@localhost", "admin123", UserRole.ADMIN)
        
        self.logger.info("UserModule initialized")
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = UserRole.VIEWER,
        **kwargs
    ) -> Optional[User]:
        """创建用户"""
        if any(u.username == username or u.email == email for u in self.users.values()):
            return None
        
        user = User(
            username=username,
            email=email,
            password=password,
            role=role,
            **kwargs
        )
        self.users[user.id] = user
        self.logger.info(f"User created: {username}")
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """认证用户，返回token"""
        for user in self.users.values():
            if user.username == username and user.check_password(password):
                user.last_login = ""
                user.login_count += 1
                
                token = secrets.token_urlsafe(32)
                self.tokens[token] = user.id
                self.logger.info(f"User logged in: {username}")
                return token
        return None
    
    def validate_token(self, token: str) -> Optional[User]:
        """验证token"""
        user_id = self.tokens.get(token)
        if user_id:
            return self.users.get(user_id)
        return None
    
    def revoke_token(self, token: str):
        """撤销token"""
        if token in self.tokens:
            del self.tokens[token]
    
    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    def list_users(self) -> List[User]:
        return list(self.users.values())
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        user = self.users.get(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
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
    
    def stop(self):
        self.logger.info("UserModule stopped")
