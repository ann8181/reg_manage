"""
Auto Register Tasks Web Management Interface
基于 Gradio 的可视化 Web 管理界面
"""
import gradio as gr
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_manager import TaskManager
from core.async_executor import AsyncTaskExecutor
from core.providers.factory import ProviderFactory
from core.providers.chain import ProviderChain

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config/tasks.json")
GLOBAL_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

def get_task_manager():
    return TaskManager(CONFIG_PATH, GLOBAL_CONFIG_PATH)

def refresh_task_list():
    manager = get_task_manager()
    tasks = []
    for cat_id, cat in manager.categories.items():
        for grp in cat.groups:
            for task in grp.tasks:
                status = "Enabled" if task.enabled else "Disabled"
                tasks.append([cat.name, grp.name, task.name, task.task_id, status])
    return tasks

def toggle_task(task_id: str, enable: bool):
    manager = get_task_manager()
    manager.enable_task(task_id, enable)
    manager.save_config()
    return refresh_task_list()

def create_email(provider: str = "mailtm"):
    try:
        p = ProviderFactory.create(provider)
        email, password = p.create_email()
        return email, password, provider, ""
    except Exception as e:
        return "", "", provider, f"Error: {str(e)}"

def get_messages(email: str, provider: str = "mailtm"):
    if not email:
        return [], "Please enter an email first"
    try:
        p = ProviderFactory.create(provider)
        messages = p.get_messages(email)
        msg_list = []
        for msg in messages:
            msg_list.append([msg.id, msg.from_addr, msg.subject, msg.timestamp or ""])
        return msg_list, f"Found {len(messages)} messages"
    except Exception as e:
        return [], f"Error: {str(e)}"

def run_selected_task(task_id: str):
    if not task_id:
        return "Please select a task first"
    
    manager = get_task_manager()
    executor = AsyncTaskExecutor(manager, max_workers=1)
    
    async def execute():
        return await executor.execute_async()
    
    import asyncio
    results = asyncio.run(execute())
    
    for r in results:
        if r.task_id == task_id:
            return f"Task: {r.task_id}\nStatus: {r.status.value}\nMessage: {r.message or r.error}"
    
    return "Task completed"

def get_stats():
    manager = get_task_manager()
    enabled = len(manager.get_enabled_tasks())
    total = len(manager.all_tasks)
    categories = len(manager.categories)
    
    return f"""统计信息:
- 总任务数: {total}
- 已启用: {enabled}
- 已禁用: {total - enabled}
- 分类数: {categories}"""

with gr.Blocks(title="Auto Register Tasks", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Auto Register Tasks Management")
    gr.Markdown("任务管理、邮箱服务和执行监控的可视化界面")
    
    with gr.Tabs():
        with gr.TabItem("任务管理"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 任务列表")
                    task_table = gr.DataTable(
                        headers=["Category", "Group", "Name", "Task ID", "Status"],
                        label="All Tasks"
                    )
                    task_table.value = refresh_task_list()
                    
                    with gr.Row():
                        refresh_btn = gr.Button("Refresh", variant="secondary")
                        refresh_btn.click(fn=refresh_task_list, outputs=task_table)
                
                with gr.Column():
                    gr.Markdown("### 操作")
                    task_id_input = gr.Textbox(label="Task ID", placeholder="e.g., email.outlook")
                    
                    with gr.Row():
                        enable_btn = gr.Button("Enable", variant="primary")
                        disable_btn = gr.Button("Disable", variant="secondary")
                    
                    status_output = gr.Textbox(label="Status")
                    
                    enable_btn.click(
                        fn=lambda tid: toggle_task(tid, True),
                        inputs=task_id_input,
                        outputs=[task_table, status_output]
                    )
                    disable_btn.click(
                        fn=lambda tid: toggle_task(tid, False),
                        inputs=task_id_input,
                        outputs=[task_table, status_output]
                    )
        
        with gr.TabItem("临时邮箱"):
            gr.Markdown("### 创建临时邮箱")
            
            with gr.Row():
                provider_dropdown = gr.Dropdown(
                    choices=ProviderFactory.get_provider_names(),
                    value="mailtm",
                    label="Provider"
                )
                create_btn = gr.Button("Create Email", variant="primary")
            
            with gr.Row():
                email_output = gr.Textbox(label="Email")
                password_output = gr.Textbox(label="Password")
                provider_output = gr.Textbox(label="Provider")
            
            create_btn.click(
                fn=create_email,
                inputs=provider_dropdown,
                outputs=[email_output, password_output, provider_output]
            )
            
            gr.Markdown("### 获取邮件")
            
            with gr.Row():
                email_input = gr.Textbox(label="Email Address")
                get_btn = gr.Button("Get Messages", variant="primary")
            
            messages_table = gr.DataTable(
                headers=["ID", "From", "Subject", "Timestamp"],
                label="Messages"
            )
            status_msg = gr.Textbox(label="Status")
            
            get_btn.click(
                fn=get_messages,
                inputs=[email_input, provider_dropdown],
                outputs=[messages_table, status_msg]
            )
        
        with gr.TabItem("执行任务"):
            gr.Markdown("### 执行选定的任务")
            
            with gr.Row():
                run_task_id = gr.Textbox(label="Task ID", placeholder="e.g., email.outlook")
                run_btn = gr.Button("Run Task", variant="primary")
            
            run_output = gr.Textbox(label="Result", lines=10)
            
            run_btn.click(
                fn=run_selected_task,
                inputs=run_task_id,
                outputs=run_output
            )
        
        with gr.TabItem("统计信息"):
            gr.Markdown("### 系统统计")
            stats_output = gr.Textbox(label="Statistics", lines=10)
            stats_output.value = get_stats()
            
            refresh_stats = gr.Button("Refresh Stats", variant="secondary")
            refresh_stats.click(fn=get_stats, outputs=stats_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
