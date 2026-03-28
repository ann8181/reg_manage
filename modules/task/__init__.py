"""
Task Module - 任务模块
提供各种任务类型的实现
"""

from .email import (
    CreateEmailTask,
    GetMessagesTask,
    GetVerificationCodeTask,
    OutlookRegisterTask,
    GmailReceiveTask,
    TempMailConvertTask,
    MailTmReceiveTask,
)
from .ai import GenerateTextTask, AnalyzeImageTask
from .ai_services import (
    GitHubRegisterTask,
    ClaudeRegisterTask,
    CopilotRegisterTask,
    CursorRegisterTask,
    AugmentRegisterTask,
    WindsurfRegisterTask,
    KiroRegisterTask,
    OpenCodeRegisterTask,
    TraeRegisterTask,
    GPTRegisterTask,
    CodexRegisterTask,
    NvidiaRegisterTask,
    ZenAIRegisterTask,
    GeminiRegisterTask,
    AIStudioRegisterTask,
    GeminiBusinessRegisterTask,
    GrokRegisterTask,
)

__all__ = [
    "CreateEmailTask",
    "GetMessagesTask",
    "GetVerificationCodeTask",
    "OutlookRegisterTask",
    "GmailReceiveTask",
    "TempMailConvertTask",
    "MailTmReceiveTask",
    "GenerateTextTask",
    "AnalyzeImageTask",
    "GitHubRegisterTask",
    "ClaudeRegisterTask",
    "CopilotRegisterTask",
    "CursorRegisterTask",
    "AugmentRegisterTask",
    "WindsurfRegisterTask",
    "KiroRegisterTask",
    "OpenCodeRegisterTask",
    "TraeRegisterTask",
    "GPTRegisterTask",
    "CodexRegisterTask",
    "NvidiaRegisterTask",
    "ZenAIRegisterTask",
    "GeminiRegisterTask",
    "AIStudioRegisterTask",
    "GeminiBusinessRegisterTask",
    "GrokRegisterTask",
]
