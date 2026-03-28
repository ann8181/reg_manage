"""
Workflow Nodes - 工作流步骤节点实现
"""

import logging
import time
import re
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class BaseNode:
    """节点基类"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        raise NotImplementedError
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        if not condition:
            return True
        
        try:
            local_vars = dict(context)
            result = eval(condition, {"__builtins__": {}}, local_vars)
            return bool(result)
        except Exception as e:
            logger.error(f"Condition evaluation failed: {condition}, error: {e}")
            return False


class TaskNode(BaseNode):
    """任务节点"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        try:
            if task_executor and step.task_id:
                result = task_executor(step.task_id, step.params, context)
                context[f"step_{step.id}_result"] = result
                return {"success": True, "result": result}
            else:
                context[f"step_{step.id}_result"] = step.params
                return {"success": True, "result": step.params}
        except Exception as e:
            logger.error(f"TaskNode execution failed: {e}")
            if step.retries < step.max_retries:
                step.retries += 1
                return {"success": False, "error": str(e), "retry": True}
            return {"success": False, "error": str(e)}


class ConditionNode(BaseNode):
    """条件节点"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        try:
            condition_result = self._evaluate_condition(step.condition, context)
            context[f"step_{step.id}_condition"] = condition_result
            
            next_steps = step.true_steps if condition_result else step.false_steps
            
            return {
                "success": True,
                "condition_result": condition_result,
                "next_steps": next_steps
            }
        except Exception as e:
            logger.error(f"ConditionNode execution failed: {e}")
            return {"success": False, "error": str(e)}


class ParallelNode(BaseNode):
    """并行执行节点"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        try:
            parallel_steps = step.parallel_steps
            if not parallel_steps:
                return {"success": True, "results": []}
            
            results = []
            with ThreadPoolExecutor(max_workers=len(parallel_steps)) as executor:
                futures = {}
                for sub_step_id in parallel_steps:
                    future = executor.submit(self._execute_sub_task, sub_step_id, context, task_executor)
                    futures[future] = sub_step_id
                
                for future in as_completed(futures):
                    sub_step_id = futures[future]
                    try:
                        result = future.result()
                        results.append({"step_id": sub_step_id, "result": result})
                    except Exception as e:
                        results.append({"step_id": sub_step_id, "error": str(e)})
            
            all_success = all(r.get("result", {}).get("success") for r in results)
            return {"success": all_success, "results": results}
        except Exception as e:
            logger.error(f"ParallelNode execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_sub_task(self, step_id: str, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        if task_executor:
            return task_executor(step_id, {}, context)
        return {"success": True}


class LoopNode(BaseNode):
    """循环执行节点"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        try:
            loop_count = step.loop_count
            loop_until = step.loop_until
            loop_steps = step.loop_steps
            
            if not loop_steps:
                return {"success": True, "iterations": 0}
            
            iterations = 0
            results = []
            max_iterations = loop_count if loop_count > 0 else 1000
            
            for i in range(max_iterations):
                if loop_until and self._evaluate_condition(loop_until, context):
                    break
                
                iteration_result = []
                for sub_step_id in loop_steps:
                    if task_executor:
                        result = task_executor(sub_step_id, {}, context)
                        iteration_result.append({"step_id": sub_step_id, "result": result})
                    
                results.append({"iteration": i, "steps": iteration_result})
                iterations += 1
            
            context[f"step_{step.id}_iterations"] = iterations
            return {"success": True, "iterations": iterations, "results": results}
        except Exception as e:
            logger.error(f"LoopNode execution failed: {e}")
            return {"success": False, "error": str(e)}


class WaitNode(BaseNode):
    """等待节点"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        try:
            wait_seconds = step.wait_seconds
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            
            context[f"step_{step.id}_waited"] = wait_seconds
            return {"success": True, "waited": wait_seconds}
        except Exception as e:
            logger.error(f"WaitNode execution failed: {e}")
            return {"success": False, "error": str(e)}


class NotifyNode(BaseNode):
    """通知节点"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        try:
            notify_type = step.notify_type
            notify_config = step.notify_config
            
            if notify_type == "webhook":
                result = self._send_webhook(notify_config, context)
            elif notify_type == "email":
                result = self._send_email(notify_config, context)
            elif notify_type == "telegram":
                result = self._send_telegram(notify_config, context)
            else:
                result = {"success": True, "message": "Notification skipped"}
            
            context[f"step_{step.id}_notification"] = result
            return result
        except Exception as e:
            logger.error(f"NotifyNode execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_webhook(self, config: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        url = config.get("url", "")
        method = config.get("method", "POST")
        payload = config.get("payload", {})
        
        logger.info(f"Webhook notification: {method} {url}")
        return {"success": True, "type": "webhook", "url": url}
    
    def _send_email(self, config: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        to = config.get("to", "")
        subject = config.get("subject", "")
        body = config.get("body", "")
        
        logger.info(f"Email notification to: {to}, subject: {subject}")
        return {"success": True, "type": "email", "to": to}
    
    def _send_telegram(self, config: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        chat_id = config.get("chat_id", "")
        message = config.get("message", "")
        
        logger.info(f"Telegram notification to chat: {chat_id}")
        return {"success": True, "type": "telegram", "chat_id": chat_id}


class BranchNode(BaseNode):
    """分支节点"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        try:
            branches = step.config.get("branches", [])
            default_branch = step.config.get("default", "")
            
            selected_branch = None
            for branch in branches:
                branch_condition = branch.get("condition", "")
                if self._evaluate_condition(branch_condition, context):
                    selected_branch = branch.get("id", "")
                    break
            
            if not selected_branch and default_branch:
                selected_branch = default_branch
            
            context[f"step_{step.id}_branch"] = selected_branch
            return {
                "success": True,
                "selected_branch": selected_branch,
                "next_steps": [selected_branch] if selected_branch else []
            }
        except Exception as e:
            logger.error(f"BranchNode execution failed: {e}")
            return {"success": False, "error": str(e)}


class ApprovalNode(BaseNode):
    """人工审批节点"""
    
    def execute(self, step, context: Dict[str, Any], task_executor: Optional[Callable]) -> Dict[str, Any]:
        try:
            approval_config = step.config.get("approval", {})
            approvers = approval_config.get("approvers", [])
            timeout = approval_config.get("timeout", 3600)
            
            context[f"step_{step.id}_pending_approval"] = {
                "approvers": approvers,
                "timeout": timeout,
                "status": "pending"
            }
            
            return {
                "success": True,
                "status": "pending",
                "approvers": approvers
            }
        except Exception as e:
            logger.error(f"ApprovalNode execution failed: {e}")
            return {"success": False, "error": str(e)}
