"""
Mail.tm Provider 测试
"""
import pytest
from core.providers.mailtm import MailTmProvider

class TestMailTmProvider:
    def test_create_email(self):
        provider = MailTmProvider()
        email, password = provider.create_email()
        assert "@" in email
        assert "mail.tm" in email.lower() or "coolmail.tm" in email.lower()
    
    def test_get_domain(self):
        provider = MailTmProvider()
        domain = provider.get_domain()
        assert domain
    
    def test_provider_close(self):
        provider = MailTmProvider()
        provider.create_email()
        provider.close()
        assert provider._email is None
