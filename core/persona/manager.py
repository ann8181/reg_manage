import uuid
from datetime import datetime
from typing import List, Optional, Dict
from .database import JSONDatabase

class AccountManager:
    def __init__(self, db_path: str):
        self.db = JSONDatabase(db_path)
    
    def create_account(
        self,
        identity_id: str,
        service: Dict,
        credentials: Dict,
        metadata: Optional[Dict] = None,
        status: str = "active"
    ) -> Dict:
        account = {
            "id": str(uuid.uuid4()),
            "identity_id": identity_id,
            "service": {
                "name": service.get("name", "unknown"),
                "display_name": service.get("display_name", service.get("name", "Unknown")),
                "signup_url": service.get("signup_url", ""),
                "category": service.get("category", "other")
            },
            "credentials": {
                "email": credentials.get("email", ""),
                "password": credentials.get("password", ""),
                "username": credentials.get("username", ""),
                "phone": credentials.get("phone", "")
            },
            "status": status,
            "registered_at": datetime.now().isoformat(),
            "last_used_at": None,
            "access_token": credentials.get("access_token", ""),
            "recovery_info": credentials.get("recovery_info", {}),
            "metadata": metadata or {},
            "notes": credentials.get("notes", "")
        }
        return self.db.add(account)
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        return self.db.get_by_id(account_id)
    
    def get_accounts_by_service(self, service_name: str) -> List[Dict]:
        return self.db.query(service__name=service_name)
    
    def get_accounts_by_identity(self, identity_id: str) -> List[Dict]:
        return self.db.query(identity_id=identity_id)
    
    def get_accounts_by_category(self, category: str) -> List[Dict]:
        all_accounts = self.db.get_all()
        return [acc for acc in all_accounts if acc.get("service", {}).get("category") == category]
    
    def update_status(self, account_id: str, status: str) -> Optional[Dict]:
        valid_statuses = ["active", "locked", "disabled", "suspended", "deleted"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of {valid_statuses}")
        return self.db.update(account_id, {"status": status})
    
    def update_credentials(self, account_id: str, credentials: Dict) -> Optional[Dict]:
        account = self.db.get_by_id(account_id)
        if account:
            current_creds = account.get("credentials", {})
            current_creds.update(credentials)
            return self.db.update(account_id, {"credentials": current_creds})
        return None
    
    def record_usage(self, account_id: str) -> Optional[Dict]:
        return self.db.update(
            account_id, 
            {"last_used_at": datetime.now().isoformat()}
        )
    
    def get_active_accounts(self, service_name: str) -> List[Dict]:
        accounts = self.get_accounts_by_service(service_name)
        return [acc for acc in accounts if acc.get("status") == "active"]
    
    def get_available_account(self, service_name: str) -> Optional[Dict]:
        active = self.get_active_accounts(service_name)
        if active:
            account = active[0]
            self.record_usage(account["id"])
            return account
        return None
    
    def get_stats(self) -> Dict:
        all_accounts = self.db.get_all()
        by_status = {}
        by_category = {}
        by_service = {}
        
        for acc in all_accounts:
            status = acc.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
            
            category = acc.get("service", {}).get("category", "unknown")
            by_category[category] = by_category.get(category, 0) + 1
            
            service = acc.get("service", {}).get("name", "unknown")
            by_service[service] = by_service.get(service, 0) + 1
        
        return {
            "total": len(all_accounts),
            "by_status": by_status,
            "by_category": by_category,
            "by_service": by_service
        }
    
    def delete_account(self, account_id: str) -> bool:
        return self.db.delete(account_id)
    
    def search_accounts(self, query: str) -> List[Dict]:
        all_accounts = self.db.get_all()
        query_lower = query.lower()
        results = []
        
        for acc in all_accounts:
            email = acc.get("credentials", {}).get("email", "").lower()
            username = acc.get("credentials", {}).get("username", "").lower()
            service_name = acc.get("service", {}).get("name", "").lower()
            
            if (query_lower in email or 
                query_lower in username or 
                query_lower in service_name):
                results.append(acc)
        
        return results


class AccountPool:
    def __init__(self, account_manager: AccountManager):
        self.manager = account_manager
        self._cache = {}
    
    def get_for_service(self, service: str, create_if_empty: bool = False) -> Optional[Dict]:
        account = self.manager.get_available_account(service)
        if account:
            return account
        
        if create_if_empty:
            return self._create_fallback_account(service)
        
        return None
    
    def _create_fallback_account(self, service: str) -> Dict:
        return {
            "id": "fallback",
            "credentials": {
                "email": "",
                "password": ""
            },
            "status": "fallback"
        }
    
    def rotate_account(self, service: str) -> Optional[Dict]:
        return self.manager.get_available_account(service)
