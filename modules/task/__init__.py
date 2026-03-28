"""
Task Module - 任务模块
提供各种任务类型的实现
"""

from .email import CreateEmailTask, GetMessagesTask, GetVerificationCodeTask
from .ai import GenerateTextTask, AnalyzeImageTask

__all__ = [
    "CreateEmailTask",
    "GetMessagesTask",
    "GetVerificationCodeTask",
    "GenerateTextTask",
    "AnalyzeImageTask",
]
