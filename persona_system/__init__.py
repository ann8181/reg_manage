import os
import json
from typing import Optional, Dict, List
from datetime import datetime

from .database import JSONDatabase, MultiDatabase
from .generator import IdentityGenerator
from .fingerprint import FingerprintGenerator
from .quality import IdentityQualityScorer, ProxyQualityChecker
from .manager import AccountManager, AccountPool
from .proxy_pool import ProxyPoolManager
from .selector import PersonaSelector, TaskContext, SelectionStrategy

class PersonaSystem:
    def __init__(self, data_dir: str = "data/persona"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.identities_path = os.path.join(data_dir, "identities.json")
        self.accounts_path = os.path.join(data_dir, "accounts.json")
        self.proxies_path = os.path.join(data_dir, "proxies.json")
        self.task_history_path = os.path.join(data_dir, "task_history.json")
        
        self.identities_db = JSONDatabase(self.identities_path)
        self.accounts_db = JSONDatabase(self.accounts_path)
        self.proxies_db = JSONDatabase(self.proxies_path)
        self.task_history_db = JSONDatabase(self.task_history_path)
        
        self.generator = IdentityGenerator()
        self.quality_scorer = IdentityQualityScorer()
        self.proxy_quality_checker = ProxyQualityChecker()
        
        self.account_manager = AccountManager(self.accounts_path)
        self.proxy_manager = ProxyPoolManager(self.proxies_path)
        self.selector = PersonaSelector(
            self.identities_path,
            self.accounts_path,
            self.proxies_path
        )
    
    def generate_identity(
        self,
        country: str = "US",
        gender: Optional[str] = None,
        age_range: tuple = (22, 45),
        save: bool = True
    ) -> Dict:
        identity = self.generator.generate(country, gender, age_range)
        if save:
            self.identities_db.add(identity)
        return identity
    
    def generate_batch_identities(
        self,
        count: int,
        country: str = "US",
        gender: Optional[str] = None,
        age_range: tuple = (22, 45),
        save: bool = True
    ) -> List[Dict]:
        identities = self.generator.generate_batch(
            count,
            country=country,
            gender=gender,
            age_range=age_range
        )
        if save:
            for identity in identities:
                self.identities_db.add(identity)
        return identities
    
    def get_identity(self, identity_id: str) -> Optional[Dict]:
        return self.identities_db.get_by_id(identity_id)
    
    def get_active_identities(self) -> List[Dict]:
        all_identities = self.identities_db.get_all()
        return [i for i in all_identities if i.get("status") == "active"]
    
    def get_identity_stats(self) -> Dict:
        all_identities = self.identities_db.get_all()
        by_status = {}
        quality_buckets = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        
        for identity in all_identities:
            status = identity.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
            
            score = identity.get("quality_score", 0)
            if score >= 90:
                quality_buckets["A+"] += 1
            elif score >= 80:
                quality_buckets["A"] += 1
            elif score >= 70:
                quality_buckets["B"] += 1
            elif score >= 60:
                quality_buckets["C"] += 1
            elif score >= 50:
                quality_buckets["D"] += 1
            else:
                quality_buckets["F"] += 1
        
        return {
            "total": len(all_identities),
            "by_status": by_status,
            "quality_distribution": quality_buckets
        }
    
    def create_account(
        self,
        identity_id: str,
        service: Dict,
        credentials: Dict,
        metadata: Optional[Dict] = None
    ) -> Dict:
        return self.account_manager.create_account(
            identity_id=identity_id,
            service=service,
            credentials=credentials,
            metadata=metadata
        )
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        return self.account_manager.get_account(account_id)
    
    def get_accounts_by_service(self, service_name: str) -> List[Dict]:
        return self.account_manager.get_accounts_by_service(service_name)
    
    def get_accounts_by_identity(self, identity_id: str) -> List[Dict]:
        return self.account_manager.get_accounts_by_identity(identity_id)
    
    def get_available_account(self, service_name: str) -> Optional[Dict]:
        return self.account_manager.get_available_account(service_name)
    
    def update_account_status(self, account_id: str, status: str) -> bool:
        result = self.account_manager.update_status(account_id, status)
        return result is not None
    
    def add_proxy(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: str = "US"
    ) -> Dict:
        return self.proxy_manager.add_proxy(
            host=host, port=port, protocol=protocol,
            username=username, password=password, country=country
        )
    
    def add_proxy_from_string(self, proxy_str: str, country: str = "US") -> Optional[Dict]:
        return self.proxy_manager.add_proxy_from_string(proxy_str, country)
    
    def get_available_proxy(self, country: Optional[str] = None) -> Optional[Dict]:
        return self.proxy_manager.get_best_proxy(country=country)
    
    def select_identity_for_service(
        self,
        service: str,
        strategy: SelectionStrategy = "isolation"
    ) -> Optional[Dict]:
        return self.selector.select_identity(service=service, strategy=strategy)
    
    def create_task_context(
        self,
        task_id: str,
        task_type: str,
        service: str
    ) -> TaskContext:
        return TaskContext(task_id, task_type, service)
    
    def save_task_record(self, context: TaskContext) -> Dict:
        record = context.to_dict()
        self.task_history_db.add(record)
        return record
    
    def get_system_stats(self) -> Dict:
        return {
            "identities": self.get_identity_stats(),
            "accounts": self.account_manager.get_stats(),
            "proxies": self.proxy_manager.get_stats(),
            "tasks": {
                "total": self.task_history_db.count()
            }
        }
    
    def export_all_data(self) -> Dict:
        return {
            "exported_at": datetime.now().isoformat(),
            "identities": self.identities_db.get_all(),
            "accounts": self.accounts_db.get_all(),
            "proxies": self.proxies_db.get_all(),
            "task_history": self.task_history_db.get_all()
        }
    
    def import_data(self, data: Dict):
        if "identities" in data:
            for identity in data["identities"]:
                existing = self.identities_db.get_by_id(identity.get("id"))
                if not existing:
                    self.identities_db.add(identity)
        
        if "accounts" in data:
            for account in data["accounts"]:
                existing = self.accounts_db.get_by_id(account.get("id"))
                if not existing:
                    self.accounts_db.add(account)
        
        if "proxies" in data:
            for proxy in data["proxies"]:
                existing = self.proxies_db.get_by_id(proxy.get("id"))
                if not existing:
                    self.proxies_db.add(proxy)
    
    def clear_all_data(self, confirm: bool = False):
        if not confirm:
            raise ValueError("Must confirm before clearing data")
        
        self.identities_db.clear()
        self.accounts_db.clear()
        self.proxies_db.clear()
        self.task_history_db.clear()


def create_persona_system(data_dir: str = "data/persona") -> PersonaSystem:
    return PersonaSystem(data_dir)


__all__ = [
    "PersonaSystem",
    "IdentityGenerator", 
    "FingerprintGenerator",
    "IdentityQualityScorer",
    "ProxyQualityChecker",
    "AccountManager",
    "AccountPool",
    "ProxyPoolManager",
    "PersonaSelector",
    "TaskContext",
    "SelectionStrategy",
    "JSONDatabase",
    "MultiDatabase",
    "create_persona_system"
]
