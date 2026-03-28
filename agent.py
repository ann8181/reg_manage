"""
Agent - 统一入口
通过kernel驱动的命令行和编程接口
"""

import sys
import os
from kernel import Kernel, get_kernel


class Agent:
    """Agent - 用户级接口"""
    
    def __init__(self):
        self.kernel = get_kernel()
    
    # ========== 任务 ==========
    
    def run_task(self, task_id: str, **params):
        """运行单个任务"""
        return self.kernel.run_task(task_id, params)
    
    def run_tasks(self, task_ids: list, **params):
        """批量运行任务"""
        return self.kernel.run_tasks(task_ids, params)
    
    # ========== 调度 ==========
    
    def schedule(
        self,
        name: str,
        task_id: str,
        schedule_type: str = "cron",
        cron_expr: str = "",
        interval_seconds: int = 0,
        batch_size: int = 1
    ) -> str:
        """创建调度"""
        return self.kernel.scheduler.add_schedule(
            name=name,
            task_id=task_id,
            schedule_type=schedule_type,
            cron_expr=cron_expr,
            interval_seconds=interval_seconds,
            batch_size=batch_size
        )
    
    def list_schedules(self):
        """列出所有调度"""
        return self.kernel.scheduler.list_schedules()
    
    def run_schedule(self, schedule_id: str):
        """立即执行调度"""
        self.kernel.scheduler.run_now(schedule_id)
    
    def pause_schedule(self, schedule_id: str):
        """暂停调度"""
        self.kernel.scheduler.pause(schedule_id)
    
    def resume_schedule(self, schedule_id: str):
        """恢复调度"""
        self.kernel.scheduler.resume(schedule_id)
    
    def remove_schedule(self, schedule_id: str):
        """删除调度"""
        self.kernel.scheduler.remove(schedule_id)
    
    # ========== 工作流 ==========
    
    def create_workflow(self, name: str, description: str = ""):
        """创建工作流"""
        return self.kernel.workflow.create_workflow(name, description)
    
    def run_workflow(self, workflow_id: str):
        """执行工作流"""
        return self.kernel.workflow.execute_workflow(workflow_id)
    
    # ========== 邮箱 ==========
    
    def create_email(self, provider: str = "mailtm"):
        """创建临时邮箱"""
        return self.kernel.provider.create_email(provider)
    
    def get_messages(self, email: str, provider: str = "mailtm"):
        """获取邮件"""
        return self.kernel.provider.get_messages(email, provider)
    
    def get_code(self, email: str, provider: str = "mailtm", **kwargs):
        """等待验证码"""
        return self.kernel.provider.get_verification_code(email, provider, **kwargs)
    
    # ========== 浏览器 ==========
    
    def create_browser(self, config_id: str = None, service: str = None):
        """创建浏览器"""
        return self.kernel.browser.create_browser(config_id, service)
    
    def close_browser(self, config_id: str = None):
        """关闭浏览器"""
        self.kernel.browser.close_browser(config_id or "default")
    
    # ========== 用户 ==========
    
    def login(self, username: str, password: str):
        """用户登录"""
        return self.kernel.user.authenticate(username, password)
    
    def whoami(self, token: str):
        """验证token"""
        user = self.kernel.user.validate_token(token)
        if user:
            return {"username": user.username, "role": user.role}
        return None
    
    # ========== 系统 ==========
    
    def stats(self):
        """系统统计"""
        return {
            "schedules": len(self.kernel.scheduler.list_schedules()),
            "workflows": len(self.kernel.workflow.list_workflows()),
            "browsers": self.kernel.browser.get_stats(),
            "providers": self.kernel.provider.list_providers()
        }


# 全局agent实例
_agent = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


if __name__ == "__main__":
    import argparse
    
    agent = get_agent()
    
    parser = argparse.ArgumentParser(description="Auto Register Agent")
    subparsers = parser.add_subparsers(dest="command")
    
    # 任务命令
    run_parser = subparsers.add_parser("run", help="运行任务")
    run_parser.add_argument("task_id", help="任务ID")
    
    schedule_parser = subparsers.add_parser("schedule", help="创建调度")
    schedule_parser.add_argument("name", help="调度名称")
    schedule_parser.add_argument("task_id", help="任务ID")
    schedule_parser.add_argument("--cron", default="", help="Cron表达式")
    schedule_parser.add_argument("--interval", type=int, default=0, help="间隔秒数")
    
    # 邮箱命令
    email_parser = subparsers.add_parser("email", help="邮箱操作")
    email_parser.add_argument("--provider", default="mailtm", help="Provider")
    
    args = parser.parse_args()
    
    if args.command == "run":
        result = agent.run_task(args.task_id)
        print(result)
    
    elif args.command == "schedule":
        schedule_id = agent.schedule(
            args.name,
            args.task_id,
            cron_expr=args.cron,
            interval_seconds=args.interval
        )
        print(f"Schedule created: {schedule_id}")
    
    elif args.command == "email":
        email, password = agent.create_email(args.provider)
        print(f"Email: {email}")
        print(f"Password: {password}")
    
    else:
        parser.print_help()
