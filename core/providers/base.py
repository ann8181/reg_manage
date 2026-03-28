"""
Email Provider 基类和异常定义
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time
import logging


logger = logging.getLogger(__name__)


class EmailProviderError(Exception):
    pass


class APIError(EmailProviderError):
    def __init__(self, provider: str, status_code: int, message: str):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] API Error {status_code}: {message}")


class WebParseError(EmailProviderError):
    pass


class RateLimitError(EmailProviderError):
    def __init__(self, provider: str, wait_time: int = 60):
        self.provider = provider
        self.wait_time = wait_time
        super().__init__(f"[{provider}] Rate limited. Wait {wait_time}s")


class EmailNotFoundError(EmailProviderError):
    pass


class SessionExpiredError(EmailProviderError):
    pass


@dataclass
class EmailMessage:
    id: str
    from_addr: str
    to_addr: str
    subject: str
    body: str
    html: Optional[str] = None
    timestamp: Optional[str] = None
    read: bool = False


class EmailProvider(ABC):
    def __init__(self, api_url: str = "", timeout: int = 30):
        self.api_url = api_url
        self.timeout = timeout
        self._session = None
        self._domain = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def create_email(self) -> Tuple[str, str]:
        pass

    @abstractmethod
    def get_messages(self, email: str) -> List[EmailMessage]:
        pass

    @abstractmethod
    def get_message(self, email: str, message_id: str) -> Optional[EmailMessage]:
        pass

    @abstractmethod
    def get_verification_code(
        self,
        email: str,
        subject_contains: str = "",
        max_wait: int = 120,
        poll_interval: int = 3
    ) -> Optional[str]:
        pass

    @abstractmethod
    def get_domain(self) -> str:
        pass

    def close(self):
        self._session = None

    def _retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: tuple = (Exception,)
    ):
        delay = base_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e}, "
                        f"retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
                else:
                    self.logger.error(f"All {max_retries} attempts failed")

        raise last_exception


class TempMailProvider(EmailProvider):
    def __init__(self, api_url: str = "", timeout: int = 30):
        super().__init__(api_url, timeout)
        self._email = None
        self._password = None

    def create_email(self) -> Tuple[str, str]:
        raise NotImplementedError

    def get_messages(self, email: str) -> List[EmailMessage]:
        raise NotImplementedError

    def get_message(self, email: str, message_id: str) -> Optional[EmailMessage]:
        raise NotImplementedError

    def get_verification_code(
        self,
        email: str,
        subject_contains: str = "",
        max_wait: int = 120,
        poll_interval: int = 3
    ) -> Optional[str]:
        import re
        start_time = time.time()

        while time.time() - start_time < max_wait:
            messages = self.get_messages(email)

            for msg in messages:
                if subject_contains and subject_contains.lower() not in msg.subject.lower():
                    continue

                code = self._extract_code_from_message(msg)
                if code:
                    self.logger.info(f"Found verification code: {code}")
                    return code

            time.sleep(poll_interval)

        self.logger.warning(f"Timeout waiting for verification code")
        return None

    def _extract_code_from_message(self, message: EmailMessage, length: int = 6) -> Optional[str]:
        text = message.body or ""
        if message.html:
            import re
            text += re.sub('<[^>]+>', '', message.html)

        if length == 6:
            codes = re.findall(r'\b\d{6}\b', text)
        else:
            codes = re.findall(r'\b\d{4}\b', text)

        return codes[0] if codes else None

    def get_domain(self) -> str:
        raise NotImplementedError
