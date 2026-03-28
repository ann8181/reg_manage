"""
Provider Factory - 提供商工厂
"""

from typing import Dict, Type, Optional
import httpx


class ProviderFactory:
    """服务提供商工厂"""
    
    _providers: Dict[str, Type] = {}
    _provider_configs: Dict[str, Dict] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: Type, config: Dict = None):
        """注册提供商"""
        cls._providers[name] = provider_class
        if config:
            cls._provider_configs[name] = config
    
    @classmethod
    def create(cls, name: str, **kwargs) -> Optional["BaseProvider"]:
        """创建提供商实例"""
        provider_class = cls._providers.get(name)
        if provider_class:
            return provider_class(**kwargs)
        return None
    
    @classmethod
    def get_provider_names(cls) -> list:
        """获取已注册提供商名称列表"""
        return list(cls._providers.keys())
    
    @classmethod
    def get_config(cls, name: str) -> Dict:
        """获取提供商配置"""
        return cls._provider_configs.get(name, {})


class BaseProvider:
    """提供商基类"""
    
    def __init__(self, name: str, api_url: str = ""):
        self.name = name
        self.api_url = api_url
        self._client = httpx.Client(timeout=30)
        self._token = None
    
    def create_email(self) -> tuple:
        """创建邮箱 (email, password)"""
        raise NotImplementedError
    
    def get_messages(self, email: str) -> list:
        """获取邮件列表"""
        raise NotImplementedError
    
    def get_verification_code(self, email: str, **kwargs) -> str:
        """获取验证码"""
        raise NotImplementedError
    
    def close(self):
        """关闭连接"""
        self._client.close()


ProviderFactory.register("mailtm", BaseProvider)
