"""
Auto Register Tasks - Unified Management API
完整的任务、调度、工作流、浏览器管理API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manager.scheduler import Scheduler, TaskSchedule, ScheduleType
from manager.browser import BrowserManager, BrowserConfig, BrowserType
from manager.workflow import WorkflowEngine, Workflow, WorkflowStep, StepType
from manager.user import UserManager, UserRole
from manager.account import AccountManager, Account
from manager.module import ModuleManager, Module, ModuleStatus

from core.providers.factory import ProviderFactory
from core.task_manager import TaskManager
from core.executor import TaskExecutor

app = FastAPI(title="Auto Register Tasks Management API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config/tasks.json")
GLOBAL_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

scheduler = Scheduler()
browser_manager = BrowserManager()
workflow_engine = WorkflowEngine()
user_manager = UserManager()
account_manager = AccountManager()
module_manager = ModuleManager()
task_manager = TaskManager(CONFIG_PATH, GLOBAL_CONFIG_PATH)


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    return user_manager.validate_token(token)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    }


@app.get("/tasks")
async def list_tasks():
    return {
        "total": len(task_manager.all_tasks),
        "enabled": len(task_manager.get_enabled_tasks()),
        "tasks": [
            {"id": t.task_id, "name": t.name, "enabled": t.enabled}
            for t in task_manager.all_tasks.values()
        ]
    }


@app.post("/tasks/{task_id}/enable")
async def enable_task(task_id: str):
    task_manager.enable_task(task_id, True)
    task_manager.save_config()
    return {"success": True}


@app.post("/tasks/{task_id}/disable")
async def disable_task(task_id: str):
    task_manager.enable_task(task_id, False)
    task_manager.save_config()
    return {"success": True}


@app.post("/tasks/{task_id}/run")
async def run_task(task_id: str, background_tasks: BackgroundTasks):
    executor = TaskExecutor(task_manager, max_workers=1)
    result = executor.execute_task_by_id(task_id)
    return {
        "task_id": task_id,
        "status": result.status.value if result else "unknown",
        "message": result.message if result else ""
    }


@app.get("/schedules")
async def list_schedules():
    schedules = scheduler.list_schedules()
    return {
        "total": len(schedules),
        "schedules": [
            {
                "id": s.id,
                "name": s.name,
                "task_id": s.task_id,
                "type": s.schedule_type.value,
                "enabled": s.enabled,
                "cron": s.cron_expr,
                "interval": s.interval_seconds,
                "next_run": s.next_run,
                "last_run": s.last_run,
                "run_count": s.run_count
            }
            for s in schedules
        ]
    }


@app.post("/schedules")
async def create_schedule(
    name: str,
    task_id: str,
    schedule_type: str,
    cron_expr: str = "",
    interval_seconds: int = 0
):
    schedule = scheduler.create_schedule(
        name=name,
        task_id=task_id,
        schedule_type=ScheduleType(schedule_type),
        cron_expr=cron_expr,
        interval_seconds=interval_seconds
    )
    return {"id": schedule.id, "success": True}


@app.post("/schedules/{schedule_id}/run")
async def run_schedule_now(schedule_id: str):
    scheduler.run_now(schedule_id)
    return {"success": True}


@app.post("/schedules/{schedule_id}/pause")
async def pause_schedule(schedule_id: str):
    scheduler.pause_schedule(schedule_id)
    return {"success": True}


@app.post("/schedules/{schedule_id}/resume")
async def resume_schedule(schedule_id: str):
    scheduler.resume_schedule(schedule_id)
    return {"success": True}


@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    scheduler.remove_schedule(schedule_id)
    return {"success": True}


@app.get("/browsers")
async def list_browsers():
    configs = browser_manager.list_configs()
    return {
        "total": len(configs),
        "browsers": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.browser_type.value,
                "enabled": c.enabled,
                "priority": c.priority,
                "headless": c.headless
            }
            for c in configs
        ]
    }


@app.get("/browsers/stats")
async def browser_stats():
    return browser_manager.get_stats()


@app.post("/browsers")
async def create_browser_config(config: BrowserConfig):
    browser_manager.add_config(config)
    return {"id": config.id, "success": True}


@app.get("/browsers/{browser_id}")
async def get_browser(browser_id: str):
    config = browser_manager.get_config(browser_id)
    if not config:
        raise HTTPException(status_code=404, detail="Browser not found")
    return config


@app.delete("/browsers/{browser_id}")
async def delete_browser(browser_id: str):
    browser_manager.close_browser(browser_id)
    return {"success": True}


@app.get("/workflows")
async def list_workflows():
    workflows = workflow_engine.list_workflows()
    return {
        "total": len(workflows),
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "status": w.status.value if hasattr(w.status, 'value') else str(w.status),
                "steps": len(w.steps)
            }
            for w in workflows
        ]
    }


@app.post("/workflows")
async def create_workflow(name: str, description: str = ""):
    wf = workflow_engine.create_workflow(name, description)
    return {"id": wf.id, "success": True}


@app.post("/workflows/{workflow_id}/steps")
async def add_workflow_step(
    workflow_id: str,
    step: WorkflowStep
):
    step = workflow_engine.add_step(workflow_id, step)
    return {"id": step.id, "success": True} if step else {"success": False}


@app.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    result = workflow_engine.execute_workflow(workflow_id)
    return result


@app.get("/users")
async def list_users():
    users = user_manager.list_users()
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role.value,
                "status": u.status.value if hasattr(u.status, 'value') else str(u.status)
            }
            for u in users
        ]
    }


@app.post("/auth/login")
async def login(username: str, password: str):
    token = user_manager.authenticate(username, password)
    if token:
        return {"token": token, "success": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/auth/logout")
async def logout(token: str = Depends(get_current_user)):
    if token:
        user_manager.revoke_token(token)
    return {"success": True}


@app.get("/modules")
async def list_modules():
    modules = module_manager.list_modules()
    return {
        "total": len(modules),
        "modules": [
            {
                "id": m.id,
                "name": m.name,
                "version": m.get_latest_version().version if m.get_latest_version() else "",
                "status": m.status.value if hasattr(m.status, 'value') else str(m.status)
            }
            for m in modules
        ]
    }


@app.get("/modules/{module_id}/info")
async def get_module_info(module_id: str):
    module = module_manager.get_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    latest_version = module.get_latest_version()
    return {
        "id": module.id,
        "name": module.name,
        "description": module.description,
        "status": module.status.value,
        "version": latest_version.version if latest_version else "",
        "versions": [
            {"version": v.version, "changelog": v.changelog, "created_at": v.created_at}
            for v in module.versions
        ]
    }


@app.get("/accounts")
async def list_accounts(service: str = None):
    accounts = account_manager.list_accounts()
    return {"total": len(accounts), "accounts": accounts}


@app.get("/providers")
async def list_providers():
    return {"providers": ProviderFactory.get_provider_names()}


@app.post("/email/create")
async def create_email(provider: str = "mailtm"):
    try:
        p = ProviderFactory.create(provider)
        email, password = p.create_email()
        return {"email": email, "password": password, "provider": provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/email/{email}/messages")
async def get_messages(email: str, provider: str = "mailtm"):
    try:
        p = ProviderFactory.create(provider)
        messages = p.get_messages(email)
        return {
            "messages": [
                {"id": m.id, "from": m.from_addr, "subject": m.subject}
                for m in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/stats")
async def dashboard_stats():
    return {
        "tasks": {
            "total": len(task_manager.all_tasks),
            "enabled": len(task_manager.get_enabled_tasks())
        },
        "schedules": scheduler.get_stats(),
        "browsers": browser_manager.get_stats(),
        "workflows": {"total": len(workflow_engine.list_workflows())},
        "users": user_manager.get_stats(),
        "accounts": {"total": len(account_manager.list_accounts())},
        "modules": {"total": len(module_manager.list_modules())}
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
