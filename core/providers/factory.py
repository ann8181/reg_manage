"""
Provider 工厂类
"""

from typing import Dict, Type, Optional, Any
from .base import EmailProvider
import logging


logger = logging.getLogger(__name__)


class ProviderFactory:
    _providers: Dict[str, Type[EmailProvider]] = {}
    _provider_configs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[EmailProvider], config: Optional[Dict] = None):
        cls._providers[name.lower()] = provider_class
        if config:
            cls._provider_configs[name.lower()] = config
        logger.info(f"Registered provider: {name}")

    @classmethod
    def create(cls, name: str, **kwargs) -> EmailProvider:
        name_lower = name.lower()

        if name_lower not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(
                f"Provider '{name}' not found. Available providers: {available}"
            )

        provider_class = cls._providers[name_lower]
        config = cls._provider_configs.get(name_lower, {})

        merged_config = {**config, **kwargs}
        return provider_class(**merged_config)

    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type[EmailProvider]]:
        return cls._providers.get(name.lower())

    @classmethod
    def list_providers(cls) -> Dict[str, Type[EmailProvider]]:
        return cls._providers.copy()

    @classmethod
    def get_provider_names(cls) -> list:
        return list(cls._providers.keys())


def register_default_providers():
    from .mailtm import MailTmProvider
    from .guerrillamail import GuerrillaMailProvider
    from .getnada import GetNadaProvider
    from .yopmail import YopMailProvider
    from .onemail import OneSecMailProvider
    from .tempmail_org import TempMailOrgProvider
    from .fakemail import FakeMailProvider
    from .gmailnator import GmailnatorProvider
    from .mailsac import MailsacProvider
    from .temp_mail_asia import TempMailAsiaProvider
    from .emailnator import EmailnatorProvider
    from .inboxkitten import InboxKittenProvider
    from .tempmail_plus import TempMailPlusProvider
    from .tempmail_lol import TempMailLolProvider

    ProviderFactory.register("mailtm", MailTmProvider, {"api_url": "https://api.mail.tm"})
    ProviderFactory.register("guerrillamail", GuerrillaMailProvider, {"api_url": "https://api.guerrillamail.com"})
    ProviderFactory.register("getnada", GetNadaProvider, {"api_url": "https://getnada.com/api"})
    ProviderFactory.register("yopmail", YopMailProvider, {"api_url": "https://api.yopmail.com"})
    ProviderFactory.register("1secmail", OneSecMailProvider, {"api_url": "https://www.1secmail.com"})
    ProviderFactory.register("tempmailorg", TempMailOrgProvider, {"api_url": "https://temp-mail.org/en/api/v2"})
    ProviderFactory.register("fakemail", FakeMailProvider, {"api_url": "https://fakemail.top"})
    ProviderFactory.register("gmailnator", GmailnatorProvider, {"api_url": "https://www.gmailnator.com/api/v1"})
    ProviderFactory.register("mailsac", MailsacProvider, {"api_url": "https://mailsac.com/api"})
    ProviderFactory.register("temp-mail-asia", TempMailAsiaProvider, {"api_url": "https://www.v3.temp-mail.asia"})
    ProviderFactory.register("emailnator", EmailnatorProvider, {"api_url": "https://emailnator.com"})
    ProviderFactory.register("inboxkitten", InboxKittenProvider, {"api_url": "https://inboxkitten.com"})
    ProviderFactory.register("tempmailplus", TempMailPlusProvider, {"api_url": "https://api.tempmailplus.com"})
    ProviderFactory.register("tempmaillol", TempMailLolProvider, {"api_url": "https://api.tempmaillol.com"})


register_default_providers()
