"""
Workflow Engine - 工作流执行引擎
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


logger = logging.getLogger(__name__)


class StepType(Enum):
    TASK = "task"               # 执行任务
    CONDITION = "condition"      # 条件判断
    PARALLEL = "parallel"       # 并行执行
    LOOP = "loop"              # 循环执行
    WAIT = "wait"              # 等待
    NOTIFY = "notify"           # 通知
    APPROVAL = "approval"       # 人工审批
    BRANCH = "branch"          # 分支


class WorkflowStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    id: str
    name: str
    step_type: StepType
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 执行配置
    task_id: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    
    # 条件配置
    condition: str = ""           # 条件表达式
    true_steps: List[str] = field(default_factory=list)   # 条件为真时执行
    false_steps: List[str] = field(default_factory=list)  # 条件为假时执行
    
    # 循环配置
    loop_count: int = 0          # 循环次数，0为无限
    loop_until: str = ""         # 循环条件
    loop_steps: List[str] = field(default_factory=list)
    
    # 并行配置
    parallel_steps: List[str] = field(default_factory=list)
    
    # 等待配置
    wait_seconds: int = 0
    
    # 通知配置
    notify_type: str = ""        # email, webhook, telegram
    notify_config: Dict = field(default_factory=dict)
    
    # 状态
    status: str = "pending"
    error: str = ""
    retries: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class Workflow:
    id: str
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    edges: List[Dict] = field(default_factory=list)  # 连接关系
    
    status: WorkflowStatus = WorkflowStatus.IDLE
    created_at: str = ""
    updated_at: str = ""
    
    # 执行上下文
    context: Dict[str, Any] = field(default_factory=dict)
    current_step: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class WorkflowEngine:
    """
    工作流执行引擎
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.workflows: Dict[str, Workflow] = {}
        self._step_handlers: Dict[StepType, Callable] = {}
        self._task_executor: Optional[Callable] = None
        
        self._register_default_handlers()
        logger.info("WorkflowEngine initialized")
    
    def _register_default_handlers(self):
        """注册默认步骤处理器"""
        from .nodes import (
            TaskNode, ConditionNode, ParallelNode, LoopNode,
            WaitNode, NotifyNode, BranchNode
        )
        
        self._step_handlers[StepType.TASK] = TaskNode().execute
        self._step_handlers[StepType.CONDITION] = ConditionNode().execute
        self._step_handlers[StepType.PARALLEL] = ParallelNode().execute
        self._step_handlers[StepType.LOOP] = LoopNode().execute
        self._step_handlers[StepType.WAIT] = WaitNode().execute
        self._step_handlers[StepType.NOTIFY] = NotifyNode().execute
        self._step_handlers[StepType.BRANCH] = BranchNode().execute
    
    def set_task_executor(self, executor: Callable):
        """设置任务执行器"""
        self._task_executor = executor
    
    def create_workflow(
        self,
        name: str,
        description: str = ""
    ) -> Workflow:
        """创建工作流"""
        wf = Workflow(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description
        )
        self.workflows[wf.id] = wf
        return wf
    
    def add_step(
        self,
        workflow_id: str,
        step: WorkflowStep
    ) -> WorkflowStep:
        """添加步骤"""
        wf = self.workflows.get(workflow_id)
        if wf:
            wf.steps.append(step)
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
            wf.edges.append({
                "from": from_step,
                "to": to_step,
                "condition": condition
            })
    
    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """执行工作流"""
        wf = self.workflows.get(workflow_id)
        if not wf:
            return {"success": False, "error": "Workflow not found"}
        
        wf.status = WorkflowStatus.RUNNING
        
        try:
            result = self._execute_steps(wf)
            
            if result["success"]:
                wf.status = WorkflowStatus.COMPLETED
            else:
                wf.status = WorkflowStatus.FAILED
            
            return result
            
        except Exception as e:
            wf.status = WorkflowStatus.FAILED
            logger.error(f"Workflow {workflow_id} failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_steps(self, workflow: Workflow) -> Dict[str, Any]:
        """执行步骤"""
        results = {}
        step_map = {s.id: s for s in workflow.steps}
        
        # 构建邻接表
        adjacency = self._build_graph(workflow)
        
        # 从第一个步骤开始执行
        start_steps = self._get_start_steps(workflow)
        
        for start_id in start_steps:
            queue = [start_id]
            visited = set()
            
            while queue:
                step_id = queue.pop(0)
                if step_id in visited:
                    continue
                visited.add(step_id)
                
                step = step_map.get(step_id)
                if not step:
                    continue
                
                workflow.current_step = step_id
                step.status = "running"
                
                try:
                    handler = self._step_handlers.get(step.step_type)
                    if handler:
                        result = handler(step, workflow.context, self._task_executor)
                        results[step_id] = result
                        step.status = "completed" if result.get("success") else "failed"
                        
                        # 处理后续步骤
                        if result.get("success") and step_id in adjacency:
                            for next_step in adjacency[step_id]:
                                queue.append(next_step)
                    else:
                        step.status = "skipped"
                        
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    results[step_id] = {"success": False, "error": str(e)}
        
        return {
            "success": all(r.get("success") for r in results.values()),
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
        all_to = set()
        for edge in workflow.edges:
            all_to.add(edge["to"])
        
        return [s.id for s in workflow.steps if s.id not in all_to]
    
    def pause_workflow(self, workflow_id: str):
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = WorkflowStatus.PAUSED
    
    def cancel_workflow(self, workflow_id: str):
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = WorkflowStatus.CANCELLED
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Workflow]:
        return list(self.workflows.values())
    
    def delete_workflow(self, workflow_id: str):
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]


def get_workflow_engine() -> WorkflowEngine:
    return WorkflowEngine()
