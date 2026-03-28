"""
Provider 故障转移链
"""

from typing import List, Tuple, Optional, Any
from .base import EmailProvider
import logging
import random


logger = logging.getLogger(__name__)


class ProviderChain:
    def __init__(self, providers: List[EmailProvider] = None):
        self.providers: List[EmailProvider] = providers or []
        self.current_index = 0

    def add_provider(self, provider: EmailProvider):
        self.providers.append(provider)

    def set_providers(self, providers: List[EmailProvider]):
        self.providers = providers
        self.current_index = 0

    def _get_next_provider(self) -> Optional[EmailProvider]:
        if not self.providers:
            return None
        provider = self.providers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.providers)
        return provider

    def create_email(self) -> Tuple[str, str, str]:
        tried = set()

        while len(tried) < len(self.providers):
            provider = self._get_next_provider()
            if not provider:
                break

            provider_name = provider.__class__.__name__
            if provider_name in tried:
                continue

            tried.add(provider_name)

            try:
                email, password = provider.create_email()
                if email:
                    logger.info(f"Email created with {provider_name}: {email}")
                    return email, password, provider_name
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                continue

        logger.error("All providers failed to create email")
        return "", "", ""

    def get_messages(self, email: str, provider_name: str = None) -> List[Any]:
        if provider_name:
            for provider in self.providers:
                if provider.__class__.__name__ == provider_name:
                    try:
                        return provider.get_messages(email)
                    except Exception as e:
                        logger.error(f"{provider_name} get_messages failed: {e}")
                        return []

        for provider in self.providers:
            try:
                messages = provider.get_messages(email)
                if messages is not None:
                    return messages
            except Exception as e:
                logger.warning(f"{provider.__class__.__name__} get_messages failed: {e}")
                continue

        return []

    def get_verification_code(
        self,
        email: str,
        subject_contains: str = "",
        max_wait: int = 120,
        provider_name: str = None
    ) -> Optional[str]:
        if provider_name:
            for provider in self.providers:
                if provider.__class__.__name__ == provider_name:
                    try:
                        return provider.get_verification_code(email, subject_contains, max_wait)
                    except Exception as e:
                        logger.error(f"{provider_name} get_verification_code failed: {e}")
                        return None

        for provider in self.providers:
            try:
                code = provider.get_verification_code(email, subject_contains, max_wait)
                if code:
                    return code
            except Exception as e:
                logger.warning(f"{provider.__class__.__name__} get_verification_code failed: {e}")
                continue

        return None

    def close_all(self):
        for provider in self.providers:
            try:
                provider.close()
            except Exception as e:
                logger.error(f"Error closing {provider.__class__.__name__}: {e}")

    def get_provider(self, name: str) -> Optional[EmailProvider]:
        for provider in self.providers:
            if provider.__class__.__name__ == name:
                return provider
        return None

    def get_provider_names(self) -> List[str]:
        return [p.__class__.__name__ for p in self.providers]


class RandomChoiceChain(ProviderChain):
    def _get_next_provider(self) -> Optional[EmailProvider]:
        if not self.providers:
            return None
        return random.choice(self.providers)
