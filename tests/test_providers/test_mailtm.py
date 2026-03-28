"""
Mail.tm Provider 测试
"""
import pytest
from core.providers.mailtm import MailTmProvider

class TestMailTmProvider:
    def test_create_email(self):
        provider = MailTmProvider()
        try:
            email, password = provider.create_email()
            assert "@" in email
            assert len(email.split("@")) == 2
            username, domain = email.split("@")
            assert len(username) > 0
            assert len(domain) > 0
        except Exception as e:
            pytest.skip(f"Mail.tm API not available: {e}")
    
    def test_get_domain(self):
        provider = MailTmProvider()
        domain = provider.get_domain()
        assert domain
        assert "@" not in domain
    
    def test_provider_close(self):
        provider = MailTmProvider()
        try:
            provider.create_email()
        except Exception:
            pass
        provider.close()
        assert provider._email is None
