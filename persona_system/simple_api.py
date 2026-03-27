"""
Persona System SimpleAPI - 傻瓜化接口层
提供最简单易用的API，让用户无需关心内部实现
"""
import os
from typing import Optional, Dict, List, Callable
from datetime import datetime
import uuid

from .generator import IdentityGenerator
from .fingerprint import FingerprintGenerator
from .quality import IdentityQualityScorer
from .database import JSONDatabase, CredentialVault
from .selector import TaskContext


class PersonaLite:
    """
    傻瓜化Persona系统 - 一句话完成所有操作
    """
    
    def __init__(self, data_dir: str = "data/persona"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.identities_db = JSONDatabase(os.path.join(data_dir, "identities.json"))
        self.accounts_db = JSONDatabase(os.path.join(data_dir, "accounts.json"))
        self.proxies_db = JSONDatabase(os.path.join(data_dir, "proxies.json"))
        
        self.generator = IdentityGenerator()
        self.fingerprint_gen = FingerprintGenerator()
        self.quality_scorer = IdentityQualityScorer()
        self._crypto = CredentialVault()
        
        self._init_default_proxies()
    
    def _init_default_proxies(self):
        """初始化默认代理池"""
        if self.proxies_db.count() == 0:
            default_proxies = [
                {"host": "127.0.0.1", "port": 8080, "protocol": "http", "country": "US"},
            ]
            for p in default_proxies:
                self.add_proxy(**p)
    
    def create_identity(
        self,
        country: str = "US",
        gender: Optional[str] = None,
        age_range: tuple = (22, 45)
    ) -> Dict:
        """一句话创建身份"""
        identity = self.generator.generate(country, gender, age_range)
        self.identities_db.add(identity)
        return identity
    
    def get_identity(
        self,
        service: Optional[str] = None,
        strategy: str = "isolation"
    ) -> Optional[Dict]:
        """
        获取一个身份用于服务注册
        自动跳过已用于该服务的身份
        """
        used_ids = set()
        if service:
            accounts = self.accounts_db.query(service__name=service)
            for acc in accounts:
                identity_id = acc.get("identity_id")
                if identity_id:
                    used_ids.add(identity_id)
        
        all_identities = self.identities_db.get_all()
        available = [i for i in all_identities if i.get("id") not in used_ids and i.get("status") == "active"]
        
        if not available:
            return self.create_identity()
        
        if strategy == "random":
            import random
            identity = random.choice(available)
        elif strategy == "priority":
            available.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            identity = available[0]
        else:
            identity = available[0]
        
        self._record_usage(identity.get("id"))
        return identity
    
    def _record_usage(self, identity_id: str):
        if identity_id:
            identity = self.identities_db.get_by_id(identity_id)
            if identity:
                metadata = identity.get("metadata", {})
                metadata["used_count"] = metadata.get("used_count", 0) + 1
                metadata["last_used_at"] = datetime.now().isoformat()
                self.identities_db.update(identity_id, {"metadata": metadata})
    
    def register_account(
        self,
        service: str,
        email: str,
        password: str,
        username: Optional[str] = None,
        identity_id: Optional[str] = None,
        extra_data: Optional[Dict] = None,
        encrypt_password: bool = True
    ) -> Dict:
        """
        一句话注册账号并保存
        自动加密密码
        """
        if identity_id is None:
            identity = self.get_identity(service)
            identity_id = identity.get("id") if identity else None
        
        encrypted_password = self._crypto.encrypt(password) if encrypt_password else password
        
        account = {
            "id": str(uuid.uuid4()),
            "identity_id": identity_id,
            "service": {
                "name": service,
                "display_name": service.upper(),
                "category": self._get_service_category(service)
            },
            "credentials": {
                "email": email,
                "password": encrypted_password,
                "username": username or "",
                "phone": ""
            },
            "status": "active",
            "registered_at": datetime.now().isoformat(),
            "last_used_at": None,
            "metadata": extra_data or {}
        }
        
        self.accounts_db.add(account)
        return account
    
    def _get_service_category(self, service: str) -> str:
        categories = {
            "github": "ai", "claude": "ai", "gpt": "ai", "gemini": "ai",
            "cursor": "ai", "copilot": "ai", "deepseek": "ai",
            "twitter": "social", "facebook": "social", "instagram": "social",
            "gmail": "email", "outlook": "email", "proton": "email"
        }
        return categories.get(service.lower(), "other")
    
    def get_account(
        self,
        service: str,
        status: str = "active"
    ) -> Optional[Dict]:
        """
        获取某服务的可用账号
        """
        accounts = self.accounts_db.query(service__name=service)
        filtered = [a for a in accounts if a.get("status") == status]
        
        if not filtered:
            return None
        
        account = filtered[0]
        self._update_last_used(account.get("id"))
        return account
    
    def get_account_decrypted(self, service: str) -> Optional[Dict]:
        """获取账号并解密密码"""
        account = self.get_account(service)
        if account:
            encrypted_pw = account.get("credentials", {}).get("password", "")
            if encrypted_pw and encrypted_pw.startswith("gA"):
                try:
                    decrypted = self._crypto.decrypt(encrypted_pw)
                    account["credentials"]["password"] = decrypted
                except Exception:
                    pass
        return account
    
    def _update_last_used(self, account_id: str):
        if account_id:
            self.accounts_db.update(account_id, {
                "last_used_at": datetime.now().isoformat()
            })
    
    def add_proxy(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: str = "US"
    ) -> Dict:
        """添加代理"""
        proxy = {
            "id": str(uuid.uuid4()),
            "proxy": {
                "host": host,
                "port": port,
                "protocol": protocol,
                "auth": {"username": username, "password": password} if username else None
            },
            "location": {"country": country, "city": "", "isp": ""},
            "quality": {
                "anonymity": "elite",
                "speed_ms": 100,
                "uptime": 100,
                "last_checked": datetime.now().isoformat()
            },
            "status": "active",
            "assigned_identity_id": None,
            "added_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        self.proxies_db.add(proxy)
        return proxy
    
    def get_proxy(self, country: Optional[str] = None) -> Optional[Dict]:
        """获取可用代理"""
        all_proxies = self.proxies_db.get_all()
        available = [p for p in all_proxies if p.get("status") == "active" and not p.get("assigned_identity_id")]
        
        if country:
            available = [p for p in available if p.get("location", {}).get("country") == country]
        
        if not available:
            return None
        
        proxy = available[0]
        self.proxies_db.update(proxy.get("id"), {
            "usage_count": proxy.get("usage_count", 0) + 1,
            "last_used_at": datetime.now().isoformat()
        })
        return proxy
    
    def auto_setup(self, service: str) -> Dict:
        """
        自动化准备 - 一句话获取注册所需一切
        返回 identity, proxy, account_info
        """
        identity = self.get_identity(service)
        proxy = self.get_proxy(country=identity.get("profile", {}).get("location", {}).get("country"))
        
        return {
            "identity": identity,
            "proxy": proxy,
            "ready": True
        }
    
    def register_service(
        self,
        service: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        username: Optional[str] = None,
        encrypt: bool = True
    ) -> Dict:
        """
        一句话完成服务注册
        自动生成邮箱、密码、身份
        """
        identity = self.get_identity(service)
        identity_id = identity.get("id") if identity else None
        
        if email is None:
            name = identity.get("profile", {}).get("name", {})
            first = name.get("first", "").lower()
            last = name.get("last", "").lower()
            import random
            random_suffix = random.randint(100, 999)
            email = f"{first}.{last}{random_suffix}@mail.com"
        
        if password is None:
            import secrets
            import string
            password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(16))
        
        account = self.register_account(
            service=service,
            email=email,
            password=password,
            username=username,
            identity_id=identity_id,
            encrypt_password=encrypt
        )
        
        return {
            "identity": identity,
            "account": account,
            "email": email,
            "password": password,
            "success": True
        }
    
    def get_all_accounts(self, service: Optional[str] = None) -> List[Dict]:
        """获取所有账号"""
        if service:
            return self.accounts_db.query(service__name=service)
        return self.accounts_db.get_all()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        identities = self.identities_db.get_all()
        accounts = self.accounts_db.get_all()
        proxies = self.proxies_db.get_all()
        
        service_counts = {}
        for acc in accounts:
            svc = acc.get("service", {}).get("name", "unknown")
            service_counts[svc] = service_counts.get(svc, 0) + 1
        
        return {
            "total_identities": len(identities),
            "active_identities": len([i for i in identities if i.get("status") == "active"]),
            "total_accounts": len(accounts),
            "total_proxies": len(proxies),
            "accounts_by_service": service_counts
        }


def create_persona(data_dir: str = "data/persona") -> PersonaLite:
    """
    创建傻瓜化Persona系统实例
    使用示例:
    
    ps = create_persona()
    
    # 一句话注册GitHub账号
    result = ps.register_service("github")
    print(f"邮箱: {result['email']}")
    print(f"密码: {result['password']}")
    
    # 获取已注册的账号
    account = ps.get_account_decrypted("github")
    print(f"邮箱: {account['credentials']['email']}")
    print(f"密码: {account['credentials']['password']}")
    """
    return PersonaLite(data_dir)


__all__ = ["PersonaLite", "create_persona"]
