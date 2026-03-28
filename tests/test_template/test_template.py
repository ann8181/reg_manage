"""
Template 模块测试
"""
import pytest
from modules.template import (
    TemplateModule,
    WorkflowTemplate,
    TemplateParameter,
    TemplateStatus
)


class TestTemplateParameter:
    """测试模板参数"""

    def test_create_parameter(self):
        """测试创建参数"""
        param = TemplateParameter(
            name="email",
            description="User email",
            type="string",
            required=True,
            default=""
        )
        
        assert param.name == "email"
        assert param.required is True


class TestWorkflowTemplate:
    """测试工作流模板"""

    def test_create_template(self, template):
        """测试创建模板"""
        tmpl = template.create_template(
            name="test_template",
            description="A test template",
            category="testing",
            parameters=[
                {"name": "param1", "description": "Test param", "type": "string"}
            ],
            steps=[
                {"id": "step1", "name": "Step 1", "step_type": "task", "task_id": "task1"}
            ],
            edges=[
                {"from": "step1", "to": "step2"}
            ]
        )
        
        assert tmpl is not None
        assert tmpl.name == "test_template"
        assert len(tmpl.parameters) == 1
        assert len(tmpl.steps) == 1

    def test_validate_params_success(self, template):
        """测试参数验证成功"""
        tmpl = template.create_template(
            name="test",
            parameters=[
                {"name": "email", "required": True},
                {"name": "count", "required": False, "default": 10}
            ]
        )
        
        valid, errors = tmpl.validate_params({"email": "test@example.com"})
        
        assert valid is True
        assert len(errors) == 0

    def test_validate_params_missing_required(self, template):
        """测试缺少必需参数"""
        tmpl = template.create_template(
            name="test",
            parameters=[
                {"name": "email", "required": True}
            ]
        )
        
        valid, errors = tmpl.validate_params({})
        
        assert valid is False
        assert len(errors) == 1


class TestTemplateModule:
    """测试模板模块"""

    def test_create_template(self, template):
        """测试创建模板"""
        tmpl = template.create_template(name="my_template")
        
        assert tmpl is not None
        assert tmpl.name == "my_template"
        assert tmpl.status == TemplateStatus.DRAFT.value

    def test_get_template(self, template):
        """测试获取模板"""
        created = template.create_template(name="get_test")
        
        result = template.get_template(created.id)
        
        assert result is created

    def test_get_nonexistent_template(self, template):
        """测试获取不存在的模板"""
        result = template.get_template("nonexistent")
        
        assert result is None

    def test_update_template(self, template):
        """测试更新模板"""
        tmpl = template.create_template(name="update_test")
        
        result = template.update_template(tmpl.id, name="updated_name")
        
        assert result.name == "updated_name"

    def test_delete_template(self, template):
        """测试删除模板"""
        tmpl = template.create_template(name="delete_test")
        
        result = template.delete_template(tmpl.id)
        
        assert result is True
        assert template.get_template(tmpl.id) is None

    def test_publish_template(self, template):
        """测试发布模板"""
        tmpl = template.create_template(name="publish_test")
        
        result = template.publish_template(tmpl.id)
        
        assert result is True
        assert tmpl.status == TemplateStatus.PUBLISHED.value

    def test_deprecate_template(self, template):
        """测试弃用模板"""
        tmpl = template.create_template(name="deprecate_test")
        
        result = template.deprecate_template(tmpl.id)
        
        assert result is True
        assert tmpl.status == TemplateStatus.DEPRECATED.value

    def test_list_templates(self, template):
        """测试列出模板"""
        template.create_template(name="list1", category="test")
        template.create_template(name="list2", category="test")
        template.create_template(name="list3", category="other")
        
        all_templates = template.list_templates()
        
        assert len(all_templates) >= 3

    def test_list_by_category(self, template):
        """测试按分类列出"""
        template.create_template(name="cat1", category="ai")
        template.create_template(name="cat2", category="ai")
        template.create_template(name="cat3", category="other")
        
        ai_templates = template.list_templates(category="ai")
        
        assert len(ai_templates) == 2

    def test_list_by_status(self, template):
        """测试按状态列出"""
        tmpl = template.create_template(name="status_test")
        template.publish_template(tmpl.id)
        
        published = template.list_templates(status=TemplateStatus.PUBLISHED.value)
        
        assert any(t.id == tmpl.id for t in published)

    def test_duplicate_template(self, template):
        """测试复制模板"""
        original = template.create_template(
            name="original",
            description="Original description",
            steps=[{"id": "s1", "name": "Step"}]
        )
        
        duplicate = template.duplicate_template(original.id)
        
        assert duplicate is not None
        assert duplicate.name == "original (copy)"
        assert duplicate.description == "Original description"

    def test_get_categories(self, template):
        """测试获取分类"""
        template.create_template(name="t1", category="ai")
        template.create_template(name="t2", category="social")
        
        categories = template.get_categories()
        
        assert "ai" in categories
        assert "social" in categories

    def test_get_stats(self, template):
        """测试获取统计"""
        template.create_template(name="s1")
        template.create_template(name="s2")
        
        stats = template.get_stats()
        
        assert stats["total"] >= 2
        assert "by_status" in stats


class TestTemplateModuleKernelIntegration:
    """测试 TemplateModule 与 Kernel 集成"""

    def test_kernel_template_property(self, running_kernel):
        """测试 kernel.template 属性"""
        assert running_kernel.template is not None
        assert running_kernel.template.__class__.__name__ == "TemplateModule"
