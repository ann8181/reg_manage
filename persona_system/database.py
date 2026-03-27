import os
import json
import fcntl
from typing import List, Optional, TypeVar, Type, Dict, Any
from datetime import datetime
from pathlib import Path

T = TypeVar('T')

class JSONDatabase:
    def __init__(self, file_path: str, model_class: Optional[Type[T]] = None):
        self.file_path = file_path
        self.model_class = model_class
        self._lock_path = file_path + ".lock"
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        dir_path = os.path.dirname(self.file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(self.file_path):
            self._save({"items": [], "updated_at": datetime.now().isoformat()})
        if not os.path.exists(self._lock_path):
            with open(self._lock_path, 'w') as f:
                f.write("")
    
    def _acquire_lock(self):
        self._lock_file = open(self._lock_path, 'w')
        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX)
    
    def _release_lock(self):
        if hasattr(self, '_lock_file') and self._lock_file:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
    
    def _load(self) -> Dict:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"items": [], "updated_at": datetime.now().isoformat()}
    
    def _save(self, data: Dict):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def get_all(self) -> List[Any]:
        self._acquire_lock()
        try:
            data = self._load()
            if self.model_class and hasattr(self.model_class, 'model_validate'):
                return [self.model_class.model_validate(item) for item in data.get("items", [])]
            return data.get("items", [])
        finally:
            self._release_lock()
    
    def get_by_id(self, id: str) -> Optional[Any]:
        items = self.get_all()
        for item in items:
            item_id = getattr(item, 'id', None) if not isinstance(item, dict) else item.get('id')
            if item_id == id:
                return item
        return None
    
    def add(self, item: Any) -> Any:
        self._acquire_lock()
        try:
            data = self._load()
            items = data.get("items", [])
            
            if not isinstance(item, dict):
                item_dict = item.model_dump() if hasattr(item, 'model_dump') else vars(item)
            else:
                item_dict = item
            
            items.append(item_dict)
            data["items"] = items
            data["updated_at"] = datetime.now().isoformat()
            self._save(data)
            
            if self.model_class and hasattr(self.model_class, 'model_validate'):
                return self.model_class.model_validate(item_dict)
            return item
        finally:
            self._release_lock()
    
    def update(self, id: str, updates: Dict) -> Optional[Any]:
        self._acquire_lock()
        try:
            data = self._load()
            items = data.get("items", [])
            
            for i, item in enumerate(items):
                if item.get('id') == id:
                    item.update(updates)
                    items[i] = item
                    data["items"] = items
                    data["updated_at"] = datetime.now().isoformat()
                    self._save(data)
                    
                    if self.model_class and hasattr(self.model_class, 'model_validate'):
                        return self.model_class.model_validate(item)
                    return item
            return None
        finally:
            self._release_lock()
    
    def delete(self, id: str) -> bool:
        self._acquire_lock()
        try:
            data = self._load()
            items = data.get("items", [])
            original_len = len(items)
            items = [item for item in items if item.get('id') != id]
            
            if len(items) < original_len:
                data["items"] = items
                data["updated_at"] = datetime.now().isoformat()
                self._save(data)
                return True
            return False
        finally:
            self._release_lock()
    
    def query(self, **filters) -> List[Any]:
        items = self.get_all()
        for key, value in filters.items():
            if "__" in key:
                parts = key.split("__")
                items = [item for item in items if self._get_nested_field(item, parts) == value]
            else:
                items = [item for item in items if self._get_field(item, key) == value]
        return items
    
    def _get_nested_field(self, item: Any, parts: List[str]) -> Any:
        current = item
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        return current
    
    def _get_field(self, item: Any, field: str) -> Any:
        if isinstance(item, dict):
            return item.get(field)
        return getattr(item, field, None)
    
    def count(self) -> int:
        return len(self.get_all())
    
    def clear(self):
        self._acquire_lock()
        try:
            self._save({"items": [], "updated_at": datetime.now().isoformat()})
        finally:
            self._release_lock()
    
    def bulk_add(self, items: List[Any]) -> List[Any]:
        self._acquire_lock()
        try:
            data = self._load()
            existing_items = data.get("items", [])
            
            for item in items:
                if not isinstance(item, dict):
                    item = item.model_dump() if hasattr(item, 'model_dump') else vars(item)
                existing_items.append(item)
            
            data["items"] = existing_items
            data["updated_at"] = datetime.now().isoformat()
            self._save(data)
            return items
        finally:
            self._release_lock()


class MultiDatabase:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self.identities = JSONDatabase(os.path.join(base_dir, "identities.json"))
        self.accounts = JSONDatabase(os.path.join(base_dir, "accounts.json"))
        self.proxies = JSONDatabase(os.path.join(base_dir, "proxies.json"))
        self.task_history = JSONDatabase(os.path.join(base_dir, "task_history.json"))
    
    def get_stats(self) -> Dict[str, int]:
        return {
            "identities_count": self.identities.count(),
            "accounts_count": self.accounts.count(),
            "proxies_count": self.proxies.count(),
            "tasks_count": self.task_history.count()
        }
    
    def backup(self, backup_dir: str):
        import shutil
        os.makedirs(backup_dir, exist_ok=True)
        for db_name in ["identities", "accounts", "proxies", "task_history"]:
            db = getattr(self, db_name)
            if os.path.exists(db.file_path):
                shutil.copy2(
                    db.file_path,
                    os.path.join(backup_dir, f"{db_name}_backup.json")
                )
    
    def restore(self, backup_dir: str):
        import shutil
        for db_name in ["identities", "accounts", "proxies", "task_history"]:
            backup_file = os.path.join(backup_dir, f"{db_name}_backup.json")
            if os.path.exists(backup_file):
                db = getattr(self, db_name)
                shutil.copy2(backup_file, db.file_path)


class Credential加密:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            from cryptography.fernet import Fernet
            key_file = os.path.expanduser("~/.persona_key")
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(key)
            cls._instance = super().__new__(cls)
            cls._instance._fernet = Fernet(key)
        return cls._instance
    
    def encrypt(self, data: str) -> str:
        if not data:
            return ""
        return self._fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, data: str) -> str:
        if not data:
            return ""
        try:
            return self._fernet.decrypt(data.encode()).decode()
        except Exception:
            return data
