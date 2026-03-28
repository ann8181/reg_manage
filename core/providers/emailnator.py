"""
Emailnator Provider 实现
"""

import httpx
from typing import List, Tuple, Optional
from .base import (
    EmailProvider,
    EmailMessage,
    APIError,
    RateLimitError,
    EmailNotFoundError
)


class EmailnatorProvider(EmailProvider):
    
    def __init__(self, api_url: str = "https://api.emailnator.com", timeout: int = 30):
        super().__init__(api_url, timeout)
        self._email = None
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.api_url, timeout=self.timeout)
    
    def create_email(self) -> Tuple[str, str]:
        raise NotImplementedError("Emailnator create_email not implemented")
    
    def get_messages(self, email: str) -> List[EmailMessage]:
        raise NotImplementedError("Emailnator get_messages not implemented")
    
    def get_message(self, email: str, message_id: str) -> Optional[EmailMessage]:
        raise NotImplementedError("Emailnator get_message not implemented")
    
    def get_verification_code(
        self,
        email: str,
        subject_contains: str = "",
        max_wait: int = 120,
        poll_interval: int = 3
    ) -> Optional[str]:
        raise NotImplementedError("Emailnator get_verification_code not implemented")
    
    def get_domain(self) -> str:
        raise NotImplementedError("Emailnator get_domain not implemented")
    
    def close(self):
        self._email = None
