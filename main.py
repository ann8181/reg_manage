#!/usr/bin/env python3
import os
import sys
import json
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config/tasks.json")
GLOBAL_CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_global_config():
    with open(GLOBAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_global_config(config):
    with open(GLOBAL_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def enable_task_by_id(task_id: str):
    config = load_global_config()
    categories = config.get("categories", {})
    
    for cat_id, cat_data in categories.items():
        for grp_id, grp_data in cat_data.get("groups", {}).items():
            if task_id in grp_data.get("tasks", {}):
                grp_data["tasks"][task_id]["enabled"] = True
                save_global_config(config)
                print(f"已启用任务: {task_id}")
                return True
    
    print(f"未找到任务: {task_id}")
    return False


def disable_task_by_id(task_id: str):
    config = load_global_config()
    categories = config.get("categories", {})
    
    for cat_id, cat_data in categories.items():
        for grp_id, grp_data in cat_data.get("groups", {}).items():
            if task_id in grp_data.get("tasks", {}):
                grp_data["tasks"][task_id]["enabled"] = False
                save_global_config(config)
                print(f"已禁用任务: {task_id}")
                return True
    
    print(f"未找到任务: {task_id}")
    return False


def enable_tasks_by_pattern(pattern: str):
    config = load_global_config()
    categories = config.get("categories", {})
    count = 0
    
    for cat_id, cat_data in categories.items():
        for grp_id, grp_data in cat_data.get("groups", {}).items():
            for task_id, task_data in grp_data.get("tasks", {}).items():
                if pattern.lower() in task_id.lower():
                    task_data["enabled"] = True
                    count += 1
    
    save_global_config(config)
    print(f"已启用 {count} 个匹配 '{pattern}' 的任务")
    return count


def disable_all_tasks():
    config = load_global_config()
    categories = config.get("categories", {})
    
    for cat_id, cat_data in categories.items():
        for grp_id, grp_data in cat_data.get("groups", {}).items():
            for task_id, task_data in grp_data.get("tasks", {}).items():
                task_data["enabled"] = False
    
    save_global_config(config)
    print("已禁用所有任务")


def list_tasks():
    sys.path.insert(0, BASE_DIR)
    from core.task_manager import TaskManager
    
    manager = TaskManager(CONFIG_PATH, GLOBAL_CONFIG_PATH)
    manager.print_status()


def run_tasks(task_filter: str = None):
    sys.path.insert(0, BASE_DIR)
    from core.task_manager import TaskManager
    from core.executor import TaskExecutor
    
    manager = TaskManager(CONFIG_PATH, GLOBAL_CONFIG_PATH)
    executor = TaskExecutor(manager, max_workers=5)
    
    if task_filter:
        if "." in task_filter:
            task_config = manager.get_task(task_filter)
            if task_config:
                executor.execute_task_by_id(task_filter)
            else:
                print(f"未找到任务: {task_filter}")
        else:
            executor.execute_category(task_filter)
    else:
        executor.execute_enabled_tasks()
    
    executor.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="自动注册任务系统 - 分层勾选执行的模块化注册工具"
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    list_parser = subparsers.add_parser("list", help="列出所有任务及状态")
    
    enable_parser = subparsers.add_parser("enable", help="启用任务")
    enable_parser.add_argument("pattern", help="任务ID或模式 (如 email.mailtm 或 email)")
    
    disable_parser = subparsers.add_parser("disable", help="禁用任务")
    disable_parser.add_argument("pattern", help="任务ID或模式")
    
    disable_all_parser = subparsers.add_parser("disable-all", help="禁用所有任务")
    
    run_parser = subparsers.add_parser("run", help="运行任务")
    run_parser.add_argument("filter", nargs="?", help="任务过滤 (category.task_id)")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_tasks()
    elif args.command == "enable":
        if "." in args.pattern:
            enable_task_by_id(args.pattern)
        else:
            enable_tasks_by_pattern(args.pattern)
    elif args.command == "disable":
        if "." in args.pattern:
            disable_task_by_id(args.pattern)
        else:
            config = load_global_config()
            categories = config.get("categories", {})
            count = 0
            for cat_id, cat_data in categories.items():
                if args.pattern.lower() in cat_id.lower():
                    for grp_id, grp_data in cat_data.get("groups", {}).items():
                        for task_id in grp_data.get("tasks", {}).keys():
                            disable_task_by_id(task_id)
                            count += 1
            if count == 0:
                print(f"未找到匹配 '{args.pattern}' 的任务")
    elif args.command == "disable-all":
        disable_all_tasks()
    elif args.command == "run":
        run_tasks(args.filter)
    else:
        print("自动注册任务系统")
        print("\n用法:")
        print("  python main.py list              列出所有任务及状态")
        print("  python main.py enable <pattern>  启用任务 (如 email.mailtm 或 email)")
        print("  python main.py disable <pattern> 禁用任务")
        print("  python main.py disable-all       禁用所有任务")
        print("  python main.py run [filter]      运行任务 (可指定过滤条件)")
        print("\n任务分层:")
        print("  - email: 邮箱任务 (temp_email, real_email, temp_convert)")
        print("  - ai: AI服务任务 (free_ai, coding_ai, chinese_ai)")
        print("\n示例:")
        print("  python main.py enable email              启用所有邮箱任务")
        print("  python main.py enable email.outlook      启用 Outlook 注册任务")
        print("  python main.py enable ai                 启用所有AI服务任务")
        print("  python main.py run email.outlook         只运行 Outlook 注册任务")
        print("  python main.py run                       运行所有已启用的任务")


if __name__ == "__main__":
    main()
