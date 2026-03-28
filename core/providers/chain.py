"""
Provider Chain - 提供商链式调用
"""

from typing import List, Optional, Callable
from .factory import BaseProvider


class ProviderChain:
    """提供商链 - 按顺序尝试多个提供商"""
    
    def __init__(self, providers: List[BaseProvider] = None):
        self.providers: List[BaseProvider] = providers or []
        self.current_index = 0
    
    def add_provider(self, provider: BaseProvider):
        """添加提供商到链"""
        self.providers.append(provider)
    
    def next_provider(self) -> Optional[BaseProvider]:
        """获取下一个提供商"""
        if self.current_index < len(self.providers):
            provider = self.providers[self.current_index]
            self.current_index += 1
            return provider
        return None
    
    def reset(self):
        """重置链"""
        self.current_index = 0
    
    def execute_with_fallback(self, func: Callable, *args, **kwargs):
        """使用回退机制执行函数"""
        self.reset()
        last_error = None
        
        while True:
            provider = self.next_provider()
            if provider is None:
                break
            
            try:
                result = func(provider, *args, **kwargs)
                if result:
                    return result
            except Exception as e:
                last_error = e
                continue
        
        if last_error:
            raise last_error
        return None
