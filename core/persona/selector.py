import random
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Literal
from .database import JSONDatabase
from .generator import IdentityGenerator
from .quality import IdentityQualityScorer

SelectionStrategy = Literal["round_robin", "priority", "isolation", "freshness", "random"]

class PersonaSelector:
    def __init__(self, identities_db_path: str, accounts_db_path: str, proxy_db_path: str):
        self.identities_db = JSONDatabase(identities_db_path)
        self.accounts_db = JSONDatabase(accounts_db_path)
        self.proxy_db = JSONDatabase(proxy_db_path)
        self.generator = IdentityGenerator()
        self.quality_scorer = IdentityQualityScorer()
        self._usage_counts: Dict[str, int] = {}
        self._round_robin_index: Dict[str, int] = {}
    
    def select_identity(
        self,
        service: Optional[str] = None,
        strategy: SelectionStrategy = "round_robin",
        identity_id: Optional[str] = None,
        regenerate: bool = False
    ) -> Optional[Dict]:
        if identity_id:
            identity = self.identities_db.get_by_id(identity_id)
            if identity and identity.get("status") == "active":
                return identity
            return None
        
        if regenerate:
            return self._generate_new_identity()
        
        if strategy == "round_robin":
            return self._select_round_robin(service)
        elif strategy == "priority":
            return self._select_by_priority()
        elif strategy == "isolation":
            return self._select_with_isolation(service)
        elif strategy == "freshness":
            return self._select_by_freshness()
        elif strategy == "random":
            return self._select_random()
        
        return self._select_round_robin(service)
    
    def _select_round_robin(self, service: Optional[str]) -> Optional[Dict]:
        used_identity_ids = self._get_used_identity_ids(service)
        all_identities = self.identities_db.get_all()
        available = [
            i for i in all_identities 
            if i.get("id") not in used_identity_ids and i.get("status") == "active"
        ]
        
        if not available:
            return self._generate_new_identity()
        
        key = service or "default"
        index = self._round_robin_index.get(key, 0) % len(available)
        identity = available[index]
        self._round_robin_index[key] = index + 1
        
        self._record_usage(identity.get("id"))
        return identity
    
    def _select_by_priority(self) -> Optional[Dict]:
        all_identities = self.identities_db.get_all()
        active = [i for i in all_identities if i.get("status") == "active"]
        
        if not active:
            return self._generate_new_identity()
        
        sorted_identities = sorted(
            active,
            key=lambda x: (
                x.get("quality_score", 0),
                -(self._usage_counts.get(x.get("id") or "", 0))
            ),
            reverse=True
        )
        
        identity = sorted_identities[0]
        self._record_usage(identity.get("id"))
        return identity
    
    def _select_with_isolation(self, service: Optional[str]) -> Optional[Dict]:
        return self._select_round_robin(service)
    
    def _select_by_freshness(self) -> Optional[Dict]:
        all_identities = self.identities_db.get_all()
        active = [i for i in all_identities if i.get("status") == "active"]
        
        if not active:
            return self._generate_new_identity()
        
        sorted_identities = sorted(
            active,
            key=lambda x: x.get("metadata", {}).get("last_used_at") or "",
            reverse=True
        )
        
        if sorted_identities and sorted_identities[0].get("metadata", {}).get("last_used_at"):
            identity = sorted_identities[-1]
        else:
            identity = sorted_identities[0]
        
        self._record_usage(identity.get("id"))
        return identity
    
    def _select_random(self) -> Optional[Dict]:
        all_identities = self.identities_db.get_all()
        active = [i for i in all_identities if i.get("status") == "active"]
        
        if not active:
            return self._generate_new_identity()
        
        identity = random.choice(active)
        self._record_usage(identity.get("id"))
        return identity
    
    def _generate_new_identity(self) -> Dict:
        identity = self.generator.generate()
        self.identities_db.add(identity)
        return identity
    
    def _get_used_identity_ids(self, service: Optional[str]) -> set:
        used_ids: set = set()
        
        if service:
            accounts = self.accounts_db.get_all()
            for acc in accounts:
                if acc.get("service", {}).get("name") == service:
                    identity_id = acc.get("identity_id")
                    if identity_id:
                        used_ids.add(identity_id)
        else:
            accounts = self.accounts_db.get_all()
            for acc in accounts:
                identity_id = acc.get("identity_id")
                if identity_id:
                    used_ids.add(identity_id)
        
        return used_ids
    
    def _record_usage(self, identity_id: Optional[str]):
        if not identity_id:
            return
        self._usage_counts[identity_id] = self._usage_counts.get(identity_id, 0) + 1
        identity = self.identities_db.get_by_id(identity_id)
        if identity:
            metadata = identity.get("metadata", {})
            metadata["used_count"] = self._usage_counts[identity_id]
            metadata["last_used_at"] = datetime.now().isoformat()
            self.identities_db.update(identity_id, {"metadata": metadata})
    
    def select_for_task(
        self,
        task_type: str,
        service: Optional[str] = None,
        strategy: SelectionStrategy = "round_robin"
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        identity = self.select_identity(service=service, strategy=strategy)
        proxy = self._select_proxy_for_identity(identity)
        
        return identity, proxy
    
    def _select_proxy_for_identity(self, identity: Optional[Dict]) -> Optional[Dict]:
        if not identity:
            return None
        
        from .proxy_pool import ProxyPoolManager
        
        location = identity.get("profile", {}).get("location", {})
        country = location.get("country", "US")
        
        proxy_manager = ProxyPoolManager.__new__(ProxyPoolManager)
        proxy_manager.db = self.proxy_db
        
        proxy = proxy_manager.get_best_proxy(country=country)
        if proxy:
            proxy_id = proxy.get("id")
            identity_id = identity.get("id")
            if proxy_id and identity_id:
                proxy_manager.assign_proxy_to_identity(proxy_id, identity_id)
        
        return proxy
    
    def get_identity_for_registration(
        self,
        service: str,
        strategy: SelectionStrategy = "isolation"
    ) -> Tuple[Dict, Dict]:
        identity = self.select_identity(service=service, strategy=strategy)
        
        if not identity:
            identity = self._generate_new_identity()
        
        return identity, {}
    
    def validate_identity_for_service(self, identity: Dict, service: str) -> Dict[str, bool]:
        return self.quality_scorer.validate_for_service(identity, service)
    
    def get_pool_status(self) -> Dict:
        all_identities = self.identities_db.get_all()
        
        by_status: Dict[str, int] = {}
        quality_distribution: Dict[str, int] = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        
        for identity in all_identities:
            status = identity.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
            
            score = identity.get("quality_score", 0)
            if score >= 90:
                quality_distribution["A+"] += 1
            elif score >= 80:
                quality_distribution["A"] += 1
            elif score >= 70:
                quality_distribution["B"] += 1
            elif score >= 60:
                quality_distribution["C"] += 1
            elif score >= 50:
                quality_distribution["D"] += 1
            else:
                quality_distribution["F"] += 1
        
        return {
            "total": len(all_identities),
            "by_status": by_status,
            "quality_distribution": quality_distribution,
            "usage_records": len(self._usage_counts)
        }


class TaskContext:
    def __init__(self, task_id: str, task_type: str, service: str):
        self.task_id = task_id
        self.task_type = task_type
        self.service = service
        self.identity: Optional[Dict] = None
        self.proxy: Optional[Dict] = None
        self.account: Optional[Dict] = None
        self.started_at = datetime.now()
        self.steps: List[Dict] = []
        self.status = "pending"
        self.error: Optional[str] = None
        self.completed_at: Optional[str] = None
    
    def assign_identity(self, identity: Dict):
        self.identity = identity
        self.add_step("identity_assigned", "success", {"identity_id": identity.get("id")})
    
    def assign_proxy(self, proxy: Dict):
        self.proxy = proxy
        self.add_step("proxy_assigned", "success", {"proxy_id": proxy.get("id")})
    
    def assign_account(self, account: Dict):
        self.account = account
        self.add_step("account_created", "success", {"account_id": account.get("id")})
    
    def add_step(self, name: str, status: str, details: Optional[Dict] = None):
        self.steps.append({
            "name": name,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def mark_running(self):
        self.status = "running"
    
    def mark_success(self):
        self.status = "success"
        self.completed_at = datetime.now().isoformat()
    
    def mark_failed(self, error: str):
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "service": self.service,
            "identity_id": self.identity.get("id") if self.identity else None,
            "proxy_id": self.proxy.get("id") if self.proxy else None,
            "account_id": self.account.get("id") if self.account else None,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at,
            "steps": self.steps,
            "error": self.error
        }
