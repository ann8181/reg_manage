import os
import json
from typing import List, Optional, TypeVar, Type, Dict, Any
from datetime import datetime

T = TypeVar('T')

class JSONDatabase:
    def __init__(self, file_path: str, model_class: Optional[Type[T]] = None):
        self.file_path = file_path
        self.model_class = model_class
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        dir_path = os.path.dirname(self.file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(self.file_path):
            self._save({"items": [], "updated_at": datetime.now().isoformat()})
    
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
        data = self._load()
        if self.model_class and hasattr(self.model_class, 'model_validate'):
            return [self.model_class.model_validate(item) for item in data.get("items", [])]
        return data.get("items", [])
    
    def get_by_id(self, id: str) -> Optional[Any]:
        items = self.get_all()
        for item in items:
            item_id = getattr(item, 'id', None) if not isinstance(item, dict) else item.get('id')
            if item_id == id:
                return item
        return None
    
    def add(self, item: Any) -> Any:
        items = self.get_all()
        if not isinstance(item, dict):
            item_dict = item.model_dump() if hasattr(item, 'model_dump') else vars(item)
        else:
            item_dict = item
        
        items.append(item_dict)
        self._save({"items": items, "updated_at": datetime.now().isoformat()})
        
        if self.model_class and hasattr(self.model_class, 'model_validate'):
            return self.model_class.model_validate(item_dict)
        return item
    
    def update(self, id: str, updates: Dict) -> Optional[Any]:
        data = self._load()
        items = data.get("items", [])
        
        for i, item in enumerate(items):
            if item.get('id') == id:
                item.update(updates)
                items[i] = item
                self._save({"items": items, "updated_at": datetime.now().isoformat()})
                
                if self.model_class and hasattr(self.model_class, 'model_validate'):
                    return self.model_class.model_validate(item)
                return item
        return None
    
    def delete(self, id: str) -> bool:
        data = self._load()
        items = data.get("items", [])
        original_len = len(items)
        items = [item for item in items if item.get('id') != id]
        
        if len(items) < original_len:
            self._save({"items": items, "updated_at": datetime.now().isoformat()})
            return True
        return False
    
    def query(self, **filters) -> List[Any]:
        items = self.get_all()
        for key, value in filters.items():
            items = [item for item in items if self._get_field(item, key) == value]
        return items
    
    def _get_field(self, item: Any, field: str) -> Any:
        if isinstance(item, dict):
            return item.get(field)
        return getattr(item, field, None)
    
    def count(self) -> int:
        return len(self.get_all())
    
    def clear(self):
        self._save({"items": [], "updated_at": datetime.now().isoformat()})
    
    def bulk_add(self, items: List[Any]) -> List[Any]:
        data = self._load()
        existing_items = data.get("items", [])
        
        for item in items:
            if not isinstance(item, dict):
                item = item.model_dump() if hasattr(item, 'model_dump') else vars(item)
            existing_items.append(item)
        
        self._save({"items": existing_items, "updated_at": datetime.now().isoformat()})
        return items


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
