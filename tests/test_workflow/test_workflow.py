"""
Workflow 工作流 CRUD 测试
"""
import pytest
from modules.workflow import WorkflowStep, Workflow, WorkflowStatus


class TestWorkflowCreation:
    """测试工作流创建"""

    def test_create_workflow(self, workflow):
        """测试创建工作流"""
        wf = workflow.create_workflow("my_workflow", "description")
        
        assert wf.name == "my_workflow"
        assert wf.description == "description"
        assert wf.id in workflow.workflows
        assert wf.status == WorkflowStatus.IDLE

    def test_create_workflow_without_description(self, workflow):
        """测试创建工作流不带描述"""
        wf = workflow.create_workflow("simple_workflow")
        
        assert wf.name == "simple_workflow"
        assert wf.description == ""

    def test_workflow_has_uuid(self, workflow):
        """测试工作流有 UUID"""
        wf1 = workflow.create_workflow("wf1")
        wf2 = workflow.create_workflow("wf2")
        
        assert wf1.id != wf2.id


class TestWorkflowCRUD:
    """测试工作流增删改查"""

    def test_get_workflow(self, workflow):
        """测试获取工作流"""
        wf = workflow.create_workflow("get_test")
        
        retrieved = workflow.get_workflow(wf.id)
        
        assert retrieved is wf

    def test_get_workflow_not_found(self, workflow):
        """测试获取不存在的工作流"""
        result = workflow.get_workflow("nonexistent")
        
        assert result is None

    def test_delete_workflow(self, workflow):
        """测试删除工作流"""
        wf = workflow.create_workflow("delete_test")
        
        workflow.delete_workflow(wf.id)
        
        assert wf.id not in workflow.workflows

    def test_delete_workflow_not_found(self, workflow):
        """测试删除不存在的工作流"""
        workflow.delete_workflow("nonexistent")

    def test_list_workflows(self, workflow):
        """测试列出所有工作流"""
        workflow.create_workflow("list1")
        workflow.create_workflow("list2")
        
        workflows = workflow.list_workflows()
        
        assert len(workflows) >= 2


class TestWorkflowSteps:
    """测试工作流步骤"""

    def test_add_step(self, workflow):
        """测试添加步骤"""
        wf = workflow.create_workflow("step_test")
        step = WorkflowStep(name="Test Step", step_type="task", task_id="test")
        
        result = workflow.add_step(wf.id, step)
        
        assert result is not None
        assert step in wf.steps

    def test_add_step_to_nonexistent_workflow(self, workflow):
        """测试向不存在的工作流添加步骤"""
        step = WorkflowStep(name="Orphan Step", step_type="task", task_id="test")
        
        result = workflow.add_step("nonexistent", step)
        
        assert result is None

    def test_add_edge(self, workflow):
        """测试添加连接"""
        wf = workflow.create_workflow("edge_test")
        step1 = WorkflowStep(id="s1", name="Step1", step_type="task", task_id="t1")
        step2 = WorkflowStep(id="s2", name="Step2", step_type="task", task_id="t2")
        
        workflow.add_step(wf.id, step1)
        workflow.add_step(wf.id, step2)
        workflow.add_edge(wf.id, "s1", "s2")
        
        assert len(wf.edges) == 1
        assert wf.edges[0]["from"] == "s1"
        assert wf.edges[0]["to"] == "s2"

    def test_add_edge_with_condition(self, workflow):
        """测试添加带条件的连接"""
        wf = workflow.create_workflow("condition_edge_test")
        step1 = WorkflowStep(id="start", name="Start", step_type="task")
        step2 = WorkflowStep(id="end", name="End", step_type="task")
        
        workflow.add_step(wf.id, step1)
        workflow.add_step(wf.id, step2)
        workflow.add_edge(wf.id, "start", "end", "x > 5")
        
        assert wf.edges[0]["condition"] == "x > 5"


class TestWorkflowStatus:
    """测试工作流状态"""

    def test_pause_workflow(self, workflow):
        """测试暂停工作流"""
        wf = workflow.create_workflow("pause_test")
        
        workflow.pause_workflow(wf.id)
        
        assert wf.status == WorkflowStatus.PAUSED

    def test_cancel_workflow(self, workflow):
        """测试取消工作流"""
        wf = workflow.create_workflow("cancel_test")
        
        workflow.cancel_workflow(wf.id)
        
        assert wf.status == WorkflowStatus.CANCELLED

    def test_workflow_to_dict(self, workflow):
        """测试工作流转字典"""
        wf = workflow.create_workflow("dict_test", "description")
        step = WorkflowStep(id="s1", name="Step1", step_type="task", task_id="t1")
        workflow.add_step(wf.id, step)
        
        wf_dict = wf.to_dict()
        
        assert wf_dict["name"] == "dict_test"
        assert wf_dict["description"] == "description"
        assert len(wf_dict["steps"]) == 1
