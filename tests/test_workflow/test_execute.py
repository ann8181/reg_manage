"""
Workflow 工作流执行测试
"""
import pytest
from modules.workflow import WorkflowStep, WorkflowStatus, StepType


class TestWorkflowExecution:
    """测试工作流执行"""

    def test_execute_workflow_success(self, workflow, kernel, mocker):
        """测试工作流执行成功"""
        wf = workflow.create_workflow("exec_test")
        step = WorkflowStep(id="exec_step", name="Execute", step_type="task", task_id="test")
        workflow.add_step(wf.id, step)
        
        mocker.patch.object(kernel, 'run_task', return_value={"success": True})
        
        result = workflow.execute_workflow(wf.id)
        
        assert result["success"] is True
        assert wf.status == WorkflowStatus.COMPLETED

    def test_execute_workflow_not_found(self, workflow):
        """测试执行不存在的工作流"""
        result = workflow.execute_workflow("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_execute_workflow_with_wait(self, workflow, kernel, mocker):
        """测试带等待步骤的工作流"""
        wf = workflow.create_workflow("wait_test")
        step = WorkflowStep(id="wait_step", name="Wait", step_type="wait", params={"seconds": 0})
        workflow.add_step(wf.id, step)
        
        mocker.patch.object(kernel, 'run_task')
        
        result = workflow.execute_workflow(wf.id)
        
        assert result["success"] is True
        assert step.status == "completed"

    def test_execute_workflow_with_condition(self, workflow, kernel, mocker):
        """测试带条件步骤的工作流"""
        wf = workflow.create_workflow("condition_test")
        step = WorkflowStep(id="cond_step", name="Condition", step_type="condition", condition="x > 5")
        workflow.add_step(wf.id, step)
        
        mocker.patch.object(kernel, 'run_task')
        
        wf.context = {"x": 10}
        result = workflow.execute_workflow(wf.id)
        
        assert result["success"] is True

    def test_execute_workflow_failure(self, workflow, kernel, mocker):
        """测试工作流执行失败"""
        wf = workflow.create_workflow("fail_test")
        step = WorkflowStep(id="fail_step", name="Fail", step_type="task", task_id="failing_task")
        workflow.add_step(wf.id, step)
        
        mocker.patch.object(kernel, 'run_task', side_effect=ValueError("Task failed"))
        
        result = workflow.execute_workflow(wf.id)
        
        assert result["success"] is False
        assert wf.status == WorkflowStatus.FAILED


class TestWorkflowStepTypes:
    """测试不同步骤类型"""

    def test_step_type_task(self, workflow, kernel, mocker):
        """测试任务步骤"""
        wf = workflow.create_workflow("task_step_test")
        step = WorkflowStep(id="task", name="Task", step_type=StepType.TASK, task_id="test")
        workflow.add_step(wf.id, step)
        
        mock_run = mocker.patch.object(kernel, 'run_task', return_value={"success": True})
        workflow.execute_workflow(wf.id)
        
        mock_run.assert_called_once_with("test", {})

    def test_step_type_wait(self, workflow, kernel, mocker):
        """测试等待步骤"""
        wf = workflow.create_workflow("wait_step_test")
        step = WorkflowStep(id="wait", name="Wait", step_type=StepType.WAIT, params={"seconds": 0})
        workflow.add_step(wf.id, step)
        
        mocker.patch.object(kernel, 'run_task')
        
        workflow.execute_workflow(wf.id)
        
        assert step.status == "completed"

    def test_step_type_notify(self, running_kernel, mocker):
        """测试通知步骤"""
        workflow = running_kernel.workflow
        
        wf = workflow.create_workflow("notify_step_test")
        step = WorkflowStep(id="notify", name="Notify", step_type=StepType.NOTIFY, params={"message": "test"})
        workflow.add_step(wf.id, step)
        
        mock_send = mocker.patch.object(running_kernel.notification, 'send', return_value=mocker.Mock(success=True, to_dict=lambda: {"success": True}))
        workflow.execute_workflow(wf.id)
        
        mock_send.assert_called_once()


class TestWorkflowGraph:
    """测试工作流图算法"""

    def test_build_graph(self, workflow):
        """测试构建邻接表"""
        wf = workflow.create_workflow("graph_test")
        s1 = WorkflowStep(id="a", step_type="task")
        s2 = WorkflowStep(id="b", step_type="task")
        s3 = WorkflowStep(id="c", step_type="task")
        
        wf.steps = [s1, s2, s3]
        wf.edges = [{"from": "a", "to": "b"}, {"from": "b", "to": "c"}]
        
        adj = workflow._build_graph(wf)
        
        assert "a" in adj
        assert "b" in adj
        assert "c" in adj
        assert "b" in adj["a"]
        assert "c" in adj["b"]

    def test_get_start_steps(self, workflow):
        """测试获取起始步骤"""
        wf = workflow.create_workflow("start_test")
        s1 = WorkflowStep(id="start", step_type="task")
        s2 = WorkflowStep(id="end", step_type="task")
        
        wf.steps = [s1, s2]
        wf.edges = [{"from": "start", "to": "end"}]
        
        start_steps = workflow._get_start_steps(wf)
        
        assert "start" in start_steps
        assert "end" not in start_steps

    def test_get_start_steps_multiple(self, workflow):
        """测试多个起始步骤"""
        wf = workflow.create_workflow("multi_start_test")
        s1 = WorkflowStep(id="s1", step_type="task")
        s2 = WorkflowStep(id="s2", step_type="task")
        s3 = WorkflowStep(id="s3", step_type="task")
        
        wf.steps = [s1, s2, s3]
        wf.edges = [{"from": "s1", "to": "s3"}, {"from": "s2", "to": "s3"}]
        
        start_steps = workflow._get_start_steps(wf)
        
        assert len(start_steps) == 2
        assert "s1" in start_steps
        assert "s2" in start_steps
        assert "s3" not in start_steps
