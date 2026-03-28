"""
Module Management - 模块版本管理
"""

import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ModuleStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class ModuleVersion:
    version: str
    changelog: str = ""
    created_at: str = ""
    created_by: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Module:
    id: str
    name: str
    description: str
    owner_id: str
    status: ModuleStatus = ModuleStatus.DRAFT
    
    versions: List[ModuleVersion] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    created_at: str = ""
    updated_at: str = ""
    published_at: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def get_latest_version(self) -> Optional[ModuleVersion]:
        if self.versions:
            return self.versions[-1]
        return None
    
    def add_version(self, version: str, changelog: str = "", created_by: str = "") -> ModuleVersion:
        module_version = ModuleVersion(
            version=version,
            changelog=changelog,
            created_by=created_by
        )
        self.versions.append(module_version)
        return module_version


class ModuleManager:
    """
    模块管理器
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.modules: Dict[str, Module] = {}
    
    def create_module(
        self,
        name: str,
        description: str,
        owner_id: str,
        **kwargs
    ) -> Module:
        module = Module(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            owner_id=owner_id,
            **kwargs
        )
        
        self.modules[module.id] = module
        return module
    
    def get_module(self, module_id: str) -> Optional[Module]:
        return self.modules.get(module_id)
    
    def get_module_by_name(self, name: str) -> Optional[Module]:
        for module in self.modules.values():
            if module.name == name:
                return module
        return None
    
    def list_modules(self) -> List[Module]:
        return list(self.modules.values())
    
    def list_published_modules(self) -> List[Module]:
        return [m for m in self.modules.values() if m.status == ModuleStatus.PUBLISHED]
    
    def publish_module(self, module_id: str) -> Optional[Module]:
        module = self.modules.get(module_id)
        if module:
            module.status = ModuleStatus.PUBLISHED
            module.published_at = datetime.now().isoformat()
            module.updated_at = datetime.now().isoformat()
        return module
    
    def deprecate_module(self, module_id: str) -> Optional[Module]:
        module = self.modules.get(module_id)
        if module:
            module.status = ModuleStatus.DEPRECATED
            module.updated_at = datetime.now().isoformat()
        return module
    
    def archive_module(self, module_id: str) -> Optional[Module]:
        module = self.modules.get(module_id)
        if module:
            module.status = ModuleStatus.ARCHIVED
            module.updated_at = datetime.now().isoformat()
        return module
    
    def add_version(
        self,
        module_id: str,
        version: str,
        changelog: str = "",
        created_by: str = ""
    ) -> Optional[ModuleVersion]:
        module = self.modules.get(module_id)
        if module:
            return module.add_version(version, changelog, created_by)
        return None
    
    def update_module(self, module_id: str, **kwargs) -> Optional[Module]:
        module = self.modules.get(module_id)
        if module:
            for key, value in kwargs.items():
                if hasattr(module, key):
                    setattr(module, key, value)
            module.updated_at = datetime.now().isoformat()
        return module
    
    def delete_module(self, module_id: str) -> bool:
        if module_id in self.modules:
            del self.modules[module_id]
            return True
        return False


def get_module_manager() -> ModuleManager:
    return ModuleManager()
