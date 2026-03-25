#!/usr/bin/env python3
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import TaskLogger, GlobalLogger, get_task_logger, get_global_logger


def test_global_logger():
    print("=" * 60)
    print("Testing GlobalLogger...")
    print("=" * 60)
    
    global_logger = get_global_logger()
    global_logger.info("TestSource", "This is an info message")
    global_logger.debug("TestSource", "This is a debug message")
    global_logger.warning("TestSource", "This is a warning message")
    global_logger.error("TestSource", "This is an error message")
    
    print(f"Global log file: {global_logger.global_log_file}")
    print()


def test_task_logger():
    print("=" * 60)
    print("Testing TaskLogger...")
    print("=" * 60)
    
    task_logger = get_task_logger("email.outlook")
    task_logger.info("Task started")
    task_logger.debug("Debug info")
    task_logger.warning("Warning: something might be wrong")
    task_logger.error("Error: test error", Exception("Test exception"))
    
    print(f"Task log file: {task_logger.log_file}")
    print(f"Screenshot dir: {task_logger.screenshot_dir}")
    print()
    
    task_logger.log_result("success", "Email created successfully", {"email": "test@example.com"})
    task_logger.log_result("failed", "Registration failed", {"error": "timeout"})
    
    print()


def test_multiple_loggers():
    print("=" * 60)
    print("Testing Multiple Loggers...")
    print("=" * 60)
    
    logger1 = get_task_logger("email.mailtm")
    logger2 = get_task_logger("email.outlook")
    logger3 = get_task_logger("ai.github")
    
    logger1.info("MailTM task log")
    logger2.info("Outlook task log")
    logger3.info("GitHub task log")
    
    print(f"Logger1: {logger1.log_file}")
    print(f"Logger2: {logger2.log_file}")
    print(f"Logger3: {logger3.log_file}")
    print()
    
    TaskLogger.close_all()
    print("All loggers closed")


def show_log_contents():
    print("=" * 60)
    print("Log File Contents:")
    print("=" * 60)
    
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    print(f"Logs directory: {logs_dir}\n")
    
    for root, dirs, files in os.walk(logs_dir):
        for file in files:
            if file.endswith(".log"):
                filepath = os.path.join(root, file)
                print(f"\n--- {filepath} ---")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(content[:1000] if len(content) > 1000 else content)
                except Exception as e:
                    print(f"Error reading file: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AUTO REGISTER TASKS - LOGGING SYSTEM TEST")
    print("=" * 60 + "\n")
    
    test_global_logger()
    test_task_logger()
    test_multiple_loggers()
    show_log_contents()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
