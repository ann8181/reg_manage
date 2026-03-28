"""
Auto Register Tasks API Server
FastAPI REST API for task management
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_manager import TaskManager
from core.async_executor import AsyncTaskExecutor
from core.providers.factory import ProviderFactory
from core.providers.chain import ProviderChain

app = FastAPI(title="Auto Register Tasks API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config/tasks.json")
GLOBAL_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    data: Dict[str, Any] = {}

class EmailRequest(BaseModel):
    provider: Optional[str] = "mailtm"

class EmailResponse(BaseModel):
    email: str
    password: str
    provider: str

class MessagesResponse(BaseModel):
    messages: List[Dict[str, Any]]

class TaskStatusResponse(BaseModel):
    total: int
    enabled: int
    categories: List[Dict[str, Any]]

@app.get("/")
async def root():
    return {"message": "Auto Register Tasks API v2.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/tasks", response_model=TaskStatusResponse)
async def list_tasks():
    manager = TaskManager(CONFIG_PATH, GLOBAL_CONFIG_PATH)
    enabled = len(manager.get_enabled_tasks())
    return TaskStatusResponse(
        total=len(manager.all_tasks),
        enabled=enabled,
        categories=[
            {"id": cat.id, "name": cat.name, "enabled": cat.enabled, "groups": [
                {"id": grp.id, "name": grp.name, "enabled": grp.enabled}
                for grp in cat.groups
            ]}
            for cat in manager.categories.values()
        ]
    )

@app.post("/tasks/{task_id}/enable")
async def enable_task(task_id: str):
    manager = TaskManager(CONFIG_PATH, GLOBAL_CONFIG_PATH)
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    manager.enable_task(task_id, True)
    manager.save_config()
    return {"message": f"Task {task_id} enabled", "task_id": task_id}

@app.post("/tasks/{task_id}/disable")
async def disable_task(task_id: str):
    manager = TaskManager(CONFIG_PATH, GLOBAL_CONFIG_PATH)
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    manager.enable_task(task_id, False)
    manager.save_config()
    return {"message": f"Task {task_id} disabled", "task_id": task_id}

@app.post("/run/{task_id}", response_model=TaskResponse)
async def run_task(task_id: str, background_tasks: BackgroundTasks):
    manager = TaskManager(CONFIG_PATH, GLOBAL_CONFIG_PATH)
    executor = AsyncTaskExecutor(manager, max_workers=1)
    
    task_config = manager.get_task(task_id)
    if not task_config:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    async def execute():
        results = await executor.execute_async()
        return results[0] if results else None
    
    result = await execute()
    
    if result:
        return TaskResponse(
            task_id=result.task_id,
            status=result.status.value,
            message=result.message or result.error or "",
            data=result.data
        )
    
    return TaskResponse(
        task_id=task_id,
        status="unknown",
        message="Task execution completed with no result"
    )

@app.post("/email/create", response_model=EmailResponse)
async def create_email(request: EmailRequest):
    try:
        provider = ProviderFactory.create(request.provider)
        email, password = provider.create_email()
        return EmailResponse(
            email=email,
            password=password,
            provider=request.provider
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/email/{email}/messages", response_model=MessagesResponse)
async def get_messages(email: str, provider: str = "mailtm"):
    try:
        provider_instance = ProviderFactory.create(provider)
        messages = provider_instance.get_messages(email)
        return MessagesResponse(
            messages=[
                {
                    "id": msg.id,
                    "from": msg.from_addr,
                    "to": msg.to_addr,
                    "subject": msg.subject,
                    "body": msg.body,
                    "timestamp": msg.timestamp
                }
                for msg in messages
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers")
async def list_providers():
    return {"providers": ProviderFactory.get_provider_names()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
