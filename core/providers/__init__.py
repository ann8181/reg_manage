"""
Email Provider 抽象层
提供统一的邮箱服务接口，支持多提供商故障转移
"""

from .base import (
    EmailProvider,
    TempMailProvider,
    EmailProviderError,
    APIError,
    WebParseError,
    RateLimitError,
    EmailNotFoundError,
)
from .factory import ProviderFactory
from .chain import ProviderChain

__all__ = [
    "EmailProvider",
    "TempMailProvider",
    "EmailProviderError",
    "APIError",
    "WebParseError",
    "RateLimitError",
    "EmailNotFoundError",
    "ProviderFactory",
    "ProviderChain",
]
