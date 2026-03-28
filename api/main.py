"""
Auto Register Tasks - Unified Management API
基于Kernel的统一API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel import get_kernel

app = FastAPI(title="Auto Register Tasks API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kernel = get_kernel()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    }


@app.get("/stats")
async def stats():
    """系统统计"""
    return {
        "schedules": len(kernel.scheduler.list_schedules()),
        "workflows": len(kernel.workflow.list_workflows()),
        "browsers": kernel.browser.get_stats(),
        "providers": kernel.provider.list_providers(),
        "users": len(kernel.user.list_users())
    }


# ========== 调度管理 ==========

@app.get("/schedules")
async def list_schedules():
    schedules = kernel.scheduler.list_schedules()
    return {"total": len(schedules), "schedules": schedules}


@app.post("/schedules")
async def create_schedule(
    name: str,
    task_id: str,
    schedule_type: str = "cron",
    cron_expr: str = "",
    interval_seconds: int = 0,
    batch_size: int = 1
):
    schedule_id = kernel.scheduler.add_schedule(
        name=name,
        task_id=task_id,
        schedule_type=schedule_type,
        cron_expr=cron_expr,
        interval_seconds=interval_seconds,
        batch_size=batch_size
    )
    return {"id": schedule_id, "success": True}


@app.post("/schedules/{schedule_id}/run")
async def run_schedule(schedule_id: str):
    kernel.scheduler.run_now(schedule_id)
    return {"success": True}


@app.post("/schedules/{schedule_id}/pause")
async def pause_schedule(schedule_id: str):
    kernel.scheduler.pause(schedule_id)
    return {"success": True}


@app.post("/schedules/{schedule_id}/resume")
async def resume_schedule(schedule_id: str):
    kernel.scheduler.resume(schedule_id)
    return {"success": True}


@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    kernel.scheduler.remove(schedule_id)
    return {"success": True}


# ========== 工作流管理 ==========

@app.get("/workflows")
async def list_workflows():
    workflows = kernel.workflow.list_workflows()
    return {
        "total": len(workflows),
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "status": w.status,
                "steps": len(w.steps)
            }
            for w in workflows
        ]
    }


@app.post("/workflows")
async def create_workflow(name: str, description: str = ""):
    wf = kernel.workflow.create_workflow(name, description)
    return {"id": wf.id, "success": True}


@app.post("/workflows/{workflow_id}/steps")
async def add_step(
    workflow_id: str,
    step_id: str,
    step_name: str,
    step_type: str = "task",
    task_id: str = ""
):
    from modules.workflow import WorkflowStep, StepType
    step = WorkflowStep(
        id=step_id,
        name=step_name,
        step_type=step_type,
        task_id=task_id
    )
    step = kernel.workflow.add_step(workflow_id, step)
    return {"id": step.id if step else None, "success": step is not None}


@app.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    result = kernel.workflow.execute_workflow(workflow_id)
    return result


# ========== 浏览器管理 ==========

@app.get("/browsers")
async def list_browsers():
    configs = kernel.browser.list_configs()
    return {
        "total": len(configs),
        "browsers": [c.to_dict() for c in configs]
    }


@app.get("/browsers/stats")
async def browser_stats():
    return kernel.browser.get_stats()


# ========== 用户管理 ==========

@app.post("/auth/login")
async def login(username: str, password: str):
    token = kernel.user.authenticate(username, password)
    if token:
        return {"token": token, "success": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/users")
async def list_users():
    users = kernel.user.list_users()
    return {"total": len(users), "users": [u.to_dict() for u in users]}


# ========== Provider管理 ==========

@app.get("/providers")
async def list_providers():
    return {"providers": kernel.provider.list_providers()}


@app.post("/email/create")
async def create_email(provider: str = "mailtm"):
    try:
        email, password = kernel.provider.create_email(provider)
        return {"email": email, "password": password, "provider": provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/email/{email}/messages")
async def get_messages(email: str, provider: str = "mailtm"):
    try:
        messages = kernel.provider.get_messages(email, provider)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/email/{email}/code")
async def get_code(email: str, provider: str = "mailtm", subject: str = "", max_wait: int = 120):
    try:
        code = kernel.provider.get_verification_code(email, provider, subject_contains=subject, max_wait=max_wait)
        return {"code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
