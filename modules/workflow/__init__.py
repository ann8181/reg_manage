"""
Workflow Module - 工作流模块
任务编排和工作流执行
"""

import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime


class StepType:
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    WAIT = "wait"
    NOTIFY = "notify"
    BRANCH = "branch"


class WorkflowStatus:
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    def __init__(
        self,
        id: str = None,
        name: str = "",
        step_type: str = StepType.TASK,
        task_id: str = "",
        params: Dict = None,
        condition: str = "",
        **kwargs
    ):
        self.id = id or str(uuid.uuid4())[:8]
        self.name = name
        self.step_type = step_type
        self.task_id = task_id
        self.params = params or {}
        self.condition = condition
        self.status = "pending"
        self.error = None
        self.result = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "step_type": self.step_type,
            "task_id": self.task_id,
            "params": self.params,
            "condition": self.condition,
            "status": self.status,
            "error": self.error
        }


class Workflow:
    def __init__(
        self,
        id: str = None,
        name: str = "",
        description: str = "",
        steps: List[WorkflowStep] = None,
        edges: List[Dict] = None
    ):
        self.id = id or str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.steps = steps or []
        self.edges = edges or []
        self.status = WorkflowStatus.IDLE
        self.context: Dict = {}
        self.created_at = datetime.now().isoformat()
    
    def add_step(self, step: WorkflowStep):
        self.steps.append(step)
    
    def add_edge(self, from_step: str, to_step: str, condition: str = ""):
        self.edges.append({"from": from_step, "to": to_step, "condition": condition})
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "edges": self.edges,
            "status": self.status,
            "created_at": self.created_at
        }


class WorkflowModule:
    """
    工作流模块
    负责任务编排和执行
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.workflows: Dict[str, Workflow] = {}
        self.logger = kernel.get_logger("workflow")
        self.logger.info("WorkflowModule initialized")
    
    def create_workflow(
        self,
        name: str,
        description: str = ""
    ) -> Workflow:
        """创建工作流"""
        wf = Workflow(name=name, description=description)
        self.workflows[wf.id] = wf
        self.logger.info(f"Workflow created: {name} ({wf.id})")
        return wf
    
    def add_step(
        self,
        workflow_id: str,
        step: WorkflowStep
    ) -> WorkflowStep:
        """添加步骤"""
        wf = self.workflows.get(workflow_id)
        if wf:
            wf.add_step(step)
            return step
        return None
    
    def add_edge(
        self,
        workflow_id: str,
        from_step: str,
        to_step: str,
        condition: str = ""
    ):
        """添加连接"""
        wf = self.workflows.get(workflow_id)
        if wf:
            wf.add_edge(from_step, to_step, condition)
    
    def execute_workflow(self, workflow_id: str) -> Dict:
        """执行工作流"""
        wf = self.workflows.get(workflow_id)
        if not wf:
            return {"success": False, "error": "Workflow not found"}
        
        wf.status = WorkflowStatus.RUNNING
        
        try:
            result = self._execute_steps(wf)
            wf.status = WorkflowStatus.COMPLETED if result["success"] else WorkflowStatus.FAILED
            return result
        except Exception as e:
            wf.status = WorkflowStatus.FAILED
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_steps(self, workflow: Workflow) -> Dict:
        """执行步骤"""
        step_map = {s.id: s for s in workflow.steps}
        adjacency = self._build_graph(workflow)
        start_steps = self._get_start_steps(workflow)
        
        results = {}
        
        for start_id in start_steps:
            queue = [start_id]
            visited = set()
            
            while queue:
                step_id = queue.pop(0)
                if step_id in visited or step_id not in step_map:
                    continue
                visited.add(step_id)
                
                step = step_map[step_id]
                step.status = "running"
                
                try:
                    if step.step_type == StepType.TASK:
                        # 执行任务
                        result = self.kernel.run_task(step.task_id, step.params)
                        step.result = result
                        step.status = "completed"
                        results[step_id] = result
                    
                    elif step.step_type == StepType.WAIT:
                        # 等待
                        import time
                        wait_seconds = step.params.get("seconds", 5)
                        time.sleep(wait_seconds)
                        step.status = "completed"
                    
                    elif step.step_type == StepType.CONDITION:
                        # 条件判断
                        condition_result = self._evaluate_condition(step.condition, workflow.context)
                        step.result = condition_result
                        step.status = "completed"
                        results[step_id] = {"condition": condition_result}
                    
                    elif step.step_type == StepType.NOTIFY:
                        # 通知
                        self.kernel.emit("notify", step.params)
                        step.status = "completed"
                    
                    # 处理后续步骤
                    if step_id in adjacency:
                        for next_step_id in adjacency[step_id]:
                            queue.append(next_step_id)
                
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    results[step_id] = {"error": str(e)}
                    self.logger.error(f"Step {step_id} failed: {e}")
        
        return {
            "success": all(r.get("error") is None for r in results.values()),
            "results": results
        }
    
    def _build_graph(self, workflow: Workflow) -> Dict[str, List[str]]:
        """构建邻接表"""
        adjacency = {s.id: [] for s in workflow.steps}
        for edge in workflow.edges:
            if edge["from"] in adjacency:
                adjacency[edge["from"]].append(edge["to"])
        return adjacency
    
    def _get_start_steps(self, workflow: Workflow) -> List[str]:
        """获取起始步骤"""
        all_to = {e["to"] for e in workflow.edges}
        return [s.id for s in workflow.steps if s.id not in all_to]
    
    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """评估条件 (安全版本)"""
        if not condition:
            return True
        try:
            import re
            safe_pattern = re.compile(r'^[\w\s\+\-\*\/\(\)\.\<\>\=\!\&\|]+$')
            if not safe_pattern.match(condition.strip()):
                self.logger.warning(f"Condition contains unsafe characters: {condition}")
                return False
            allowed_names = {"context": context, "True": True, "False": False, "None": None}
            for key, value in context.items():
                if key.isidentifier():
                    allowed_names[key] = value
            return eval(condition, {"__builtins__": {}}, allowed_names)
        except Exception as e:
            self.logger.warning(f"Condition evaluation failed: {e}")
            return False
    
    def pause_workflow(self, workflow_id: str):
        wf = self.workflows.get(workflow_id)
        if wf:
            wf.status = WorkflowStatus.PAUSED
    
    def cancel_workflow(self, workflow_id: str):
        wf = self.workflows.get(workflow_id)
        if wf:
            wf.status = WorkflowStatus.CANCELLED
    
    def delete_workflow(self, workflow_id: str):
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Workflow]:
        return list(self.workflows.values())
    
    def stop(self):
        self.logger.info("WorkflowModule stopped")
