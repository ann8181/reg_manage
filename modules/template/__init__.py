"""
Template Module - 工作流模板模块
支持工作流模板定义、参数化和模板市场
"""

import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class TemplateStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass
class TemplateParameter:
    """模板参数定义"""
    name: str
    description: str = ""
    type: str = "string"
    required: bool = True
    default: Any = None
    options: List[Any] = None
    validation: str = ""


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    id: str
    name: str
    description: str = ""
    category: str = "general"
    version: str = "1.0.0"
    status: str = TemplateStatus.DRAFT.value
    parameters: List[TemplateParameter] = field(default_factory=list)
    steps: List[Dict] = field(default_factory=list)
    edges: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "status": self.status,
            "parameters": [
                {"name": p.name, "description": p.description, "type": p.type,
                 "required": p.required, "default": p.default, "options": p.options}
                for p in self.parameters
            ],
            "steps": self.steps,
            "edges": self.edges,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "tags": self.tags
        }
    
    def validate_params(self, params: Dict[str, Any]) -> tuple:
        """验证参数，返回 (success, errors)"""
        errors = []
        for param in self.parameters:
            if param.required and param.name not in params and param.default is None:
                errors.append(f"Missing required parameter: {param.name}")
            if param.name in params:
                value = params[param.name]
                if param.options and value not in param.options:
                    errors.append(f"Invalid value for {param.name}: {value} not in options")
        return len(errors) == 0, errors


class TemplateModule:
    """
    工作流模板模块
    提供工作流模板的创建、管理和实例化
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._categories: Dict[str, List[str]] = {}
        self._logger = kernel.get_logger("template")
        self._logger.info("TemplateModule initialized")
    
    def create_template(
        self,
        name: str,
        description: str = "",
        category: str = "general",
        parameters: List[Dict] = None,
        steps: List[Dict] = None,
        edges: List[Dict] = None,
        author: str = "",
        tags: List[str] = None,
        **kwargs
    ) -> WorkflowTemplate:
        """创建模板"""
        template_id = str(uuid.uuid4())[:8]
        
        params = [
            TemplateParameter(**p) if isinstance(p, dict) else p
            for p in (parameters or [])
        ]
        
        template = WorkflowTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            parameters=params,
            steps=steps or [],
            edges=edges or [],
            author=author,
            tags=tags or [],
            **kwargs
        )
        
        self._templates[template_id] = template
        
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(template_id)
        
        self._logger.info(f"Template created: {name} ({template_id})")
        return template
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """获取模板"""
        return self._templates.get(template_id)
    
    def update_template(
        self,
        template_id: str,
        **kwargs
    ) -> Optional[WorkflowTemplate]:
        """更新模板"""
        template = self._templates.get(template_id)
        if not template:
            return None
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        self._logger.info(f"Template updated: {template.name}")
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        template = self._templates.get(template_id)
        if not template:
            return False
        
        del self._templates[template_id]
        
        if template.category in self._categories:
            if template_id in self._categories[template.category]:
                self._categories[template.category].remove(template_id)
        
        self._logger.info(f"Template deleted: {template.name}")
        return True
    
    def publish_template(self, template_id: str) -> bool:
        """发布模板"""
        template = self._templates.get(template_id)
        if not template:
            return False
        
        template.status = TemplateStatus.PUBLISHED.value
        self._logger.info(f"Template published: {template.name}")
        return True
    
    def deprecate_template(self, template_id: str) -> bool:
        """弃用模板"""
        template = self._templates.get(template_id)
        if not template:
            return False
        
        template.status = TemplateStatus.DEPRECATED.value
        self._logger.info(f"Template deprecated: {template.name}")
        return True
    
    def list_templates(
        self,
        category: str = None,
        status: str = None,
        tags: List[str] = None
    ) -> List[WorkflowTemplate]:
        """列出模板"""
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if status:
            templates = [t for t in templates if t.status == status]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        return templates
    
    def get_by_category(self, category: str) -> List[WorkflowTemplate]:
        """按分类获取模板"""
        template_ids = self._categories.get(category, [])
        return [self._templates[tid] for tid in template_ids if tid in self._templates]
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._categories.keys())
    
    def instantiate(
        self,
        template_id: str,
        params: Dict[str, Any],
        workflow_name: str = None,
        **kwargs
    ) -> Optional[Dict]:
        """从模板实例化工作流"""
        template = self._templates.get(template_id)
        if not template:
            self._logger.error(f"Template not found: {template_id}")
            return None
        
        valid, errors = template.validate_params(params)
        if not valid:
            self._logger.error(f"Invalid params: {errors}")
            return None
        
        workflow = self.kernel.workflow.create_workflow(
            name=workflow_name or f"{template.name}-instance",
            description=template.description
        )
        
        id_mapping = {}
        for step_def in template.steps:
            step_id = str(uuid.uuid4())[:8]
            id_mapping[step_def.get("id", "")] = step_id
            
            from modules.workflow import WorkflowStep
            step = WorkflowStep(
                id=step_id,
                name=step_def.get("name", ""),
                step_type=step_def.get("step_type", "task"),
                task_id=step_def.get("task_id", ""),
                params=step_def.get("params", {}),
                condition=step_def.get("condition", "")
            )
            self.kernel.workflow.add_step(workflow.id, step)
        
        for edge_def in template.edges:
            from_id = id_mapping.get(edge_def.get("from", ""), edge_def.get("from", ""))
            to_id = id_mapping.get(edge_def.get("to", ""), edge_def.get("to", ""))
            self.kernel.workflow.add_edge(
                workflow.id,
                from_id,
                to_id,
                edge_def.get("condition", "")
            )
        
        self._logger.info(f"Workflow instantiated from template: {template.name}")
        
        return {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "template_id": template_id,
            "template_name": template.name
        }
    
    def duplicate_template(self, template_id: str, new_name: str = None) -> Optional[WorkflowTemplate]:
        """复制模板"""
        template = self._templates.get(template_id)
        if not template:
            return None
        
        return self.create_template(
            name=new_name or f"{template.name} (copy)",
            description=template.description,
            category=template.category,
            parameters=[
                {"name": p.name, "description": p.description, "type": p.type,
                 "required": p.required, "default": p.default, "options": p.options}
                for p in template.parameters
            ],
            steps=template.steps.copy(),
            edges=template.edges.copy(),
            author=template.author,
            tags=template.tags.copy()
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        by_status = {}
        for template in self._templates.values():
            by_status[template.status] = by_status.get(template.status, 0) + 1
        
        return {
            "total": len(self._templates),
            "by_status": by_status,
            "categories": len(self._categories)
        }
    
    def stop(self):
        """停止模块"""
        self._logger.info("TemplateModule stopped")
