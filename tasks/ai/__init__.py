from .github import GitHubRegister
from .claude import ClaudeRegister
from .copilot import CopilotRegister
from .cursor import CursorRegister
from .augment import AugmentRegister
from .windsurf import WindsurfRegister
from .kiro import KiroRegister
from .opencode import OpenCodeRegister
from .trae import TraeRegister
from .gpt import GPTRegister, GPTWebRegister
from .codex import CodexAuth, CodexRegister
from .nvidia import NvidiaRegister
from .zen import ZenRegister
from .gemini import GeminiRegister, GeminiWebRegister
from .aistudio import AIStudioRegister
from .business_gemini import BusinessGeminiRegister
from .grok import GrokRegister
from .perplexity import PerplexityRegister
from .deepseek import DeepSeekRegister
from .mistral import MistralRegister
from .groq import GroqRegister
from .cohere import CohereRegister
from .replicate import ReplicateRegister
from .kimi import KimiRegister
from .step import StepRegister
from .zhipuai import ZhipuaiRegister
from .minimax import MinimaxRegister
from .yuanbao import YuanbaoRegister
from .openrelay import OpenRelayTask
from .freeapihub import FreeApiHubTask
from .chat2api import Chat2ApiTask

__all__ = [
    'GitHubRegister',
    'ClaudeRegister',
    'CopilotRegister',
    'CursorRegister',
    'AugmentRegister',
    'WindsurfRegister',
    'KiroRegister',
    'OpenCodeRegister',
    'TraeRegister',
    'GPTRegister',
    'GPTWebRegister',
    'CodexAuth',
    'CodexRegister',
    'NvidiaRegister',
    'ZenRegister',
    'GeminiRegister',
    'GeminiWebRegister',
    'AIStudioRegister',
    'BusinessGeminiRegister',
    'GrokRegister',
    'PerplexityRegister',
    'DeepSeekRegister',
    'MistralRegister',
    'GroqRegister',
    'CohereRegister',
    'ReplicateRegister',
    'KimiRegister',
    'StepRegister',
    'ZhipuaiRegister',
    'MinimaxRegister',
    'YuanbaoRegister',
    'OpenRelayTask',
    'FreeApiHubTask',
    'Chat2ApiTask'
]
