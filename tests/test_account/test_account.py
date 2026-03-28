"""
Account 模块测试
"""
import pytest
from modules.account import (
    Account, AccountModule, AccountType, AccountStatus
)


class TestAccountCreation:
    """测试账号创建"""

    def test_create_account(self, account):
        """测试创建账号"""
        acc = account.create_account(
            name="test_ai",
            account_type=AccountType.AI_SERVICE,
            provider="openai",
            credentials={"api_key": "sk-test"}
        )
        
        assert acc is not None
        assert acc.name == "test_ai"
        assert acc.account_type == AccountType.AI_SERVICE
        assert acc.provider == "openai"
        assert acc.enabled is True
        assert acc.status == AccountStatus.ACTIVE

    def test_create_account_with_quota(self, account):
        """测试创建带配额的账号"""
        acc = account.create_account(
            name="limited",
            account_type=AccountType.AI_SERVICE,
            quota={"requests": 100, "default": -1}
        )
        
        assert acc.quota["requests"] == 100
        assert acc.check_quota("requests") is True


class TestAccountOperations:
    """测试账号操作"""

    def test_get_account(self, account):
        """测试获取账号"""
        created = account.create_account(name="get_test", account_type=AccountType.EMAIL)
        retrieved = account.get_account(created.id)
        
        assert retrieved is created

    def test_get_account_not_found(self, account):
        """测试获取不存在的账号"""
        result = account.get_account("nonexistent")
        
        assert result is None

    def test_list_accounts(self, account):
        """测试列出账号"""
        account.create_account(name="acc1", account_type=AccountType.AI_SERVICE)
        account.create_account(name="acc2", account_type=AccountType.EMAIL)
        
        accounts = account.list_accounts()
        
        assert len(accounts) >= 2

    def test_list_accounts_by_type(self, account):
        """测试按类型列出账号"""
        account.create_account(name="ai1", account_type=AccountType.AI_SERVICE)
        account.create_account(name="ai2", account_type=AccountType.AI_SERVICE)
        account.create_account(name="email1", account_type=AccountType.EMAIL)
        
        ai_accounts = account.get_accounts_by_type(AccountType.AI_SERVICE)
        
        assert len(ai_accounts) >= 2

    def test_list_accounts_by_provider(self, account):
        """测试按提供商列出账号"""
        account.create_account(name="openai1", account_type=AccountType.AI_SERVICE, provider="openai")
        account.create_account(name="openai2", account_type=AccountType.AI_SERVICE, provider="openai")
        account.create_account(name="anthropic", account_type=AccountType.AI_SERVICE, provider="anthropic")
        
        openai_accounts = account.get_accounts_by_provider("openai")
        
        assert len(openai_accounts) >= 2


class TestAccountUpdate:
    """测试账号更新"""

    def test_update_account(self, account):
        """测试更新账号"""
        acc = account.create_account(name="update_test", account_type=AccountType.AI_SERVICE)
        
        account.update_account(acc.id, name="updated_name")
        
        assert acc.name == "updated_name"

    def test_update_credentials(self, account):
        """测试更新凭证"""
        acc = account.create_account(
            name="cred_test",
            account_type=AccountType.AI_SERVICE,
            credentials={"api_key": "old_key"}
        )
        
        account.update_account(acc.id, credentials={"api_key": "new_key"})
        
        assert acc.credentials["api_key"] == "new_key"

    def test_delete_account(self, account):
        """测试删除账号"""
        acc = account.create_account(name="delete_test", account_type=AccountType.AI_SERVICE)
        
        result = account.delete_account(acc.id)
        
        assert result is True
        assert account.get_account(acc.id) is None


class TestAccountEnableDisable:
    """测试账号启用禁用"""

    def test_enable_account(self, account):
        """测试启用账号"""
        acc = account.create_account(name="enable_test", account_type=AccountType.AI_SERVICE)
        acc.enabled = False
        
        result = account.enable_account(acc.id)
        
        assert result is True
        assert acc.enabled is True

    def test_disable_account(self, account):
        """测试禁用账号"""
        acc = account.create_account(name="disable_test", account_type=AccountType.AI_SERVICE)
        
        result = account.disable_account(acc.id)
        
        assert result is True
        assert acc.enabled is False


class TestAccountValidation:
    """测试账号验证"""

    def test_validate_valid_account(self, account):
        """测试验证有效账号"""
        acc = account.create_account(name="valid_test", account_type=AccountType.AI_SERVICE)
        
        result = account.validate_account(acc.id)
        
        assert result["valid"] is True
        assert result["account"] is acc

    def test_validate_disabled_account(self, account):
        """测试验证禁用的账号"""
        acc = account.create_account(name="disabled_test", account_type=AccountType.AI_SERVICE)
        account.disable_account(acc.id)
        
        result = account.validate_account(acc.id)
        
        assert result["valid"] is False
        assert "disabled" in result["reason"].lower()

    def test_validate_nonexistent_account(self, account):
        """测试验证不存在的账号"""
        result = account.validate_account("nonexistent")
        
        assert result["valid"] is False
        assert "not found" in result["reason"].lower()


class TestAccountQuota:
    """测试配额管理"""

    def test_check_quota_unlimited(self, account):
        """测试无限制配额"""
        acc = account.create_account(
            name="unlimited",
            account_type=AccountType.AI_SERVICE,
            quota={"default": -1}
        )
        
        assert acc.check_quota("any_action") is True

    def test_check_quota_within_limit(self, account):
        """测试在配额内"""
        acc = account.create_account(
            name="within_limit",
            account_type=AccountType.AI_SERVICE,
            quota={"requests": 10},
            usage={"requests": 5}
        )
        
        assert acc.check_quota("requests") is True

    def test_check_quota_exceeded(self, account):
        """测试超出配额"""
        acc = account.create_account(
            name="exceeded",
            account_type=AccountType.AI_SERVICE,
            quota={"requests": 10},
            usage={"requests": 10}
        )
        
        assert acc.check_quota("requests") is False

    def test_increment_usage(self, account):
        """测试增加使用量"""
        acc = account.create_account(
            name="increment",
            account_type=AccountType.AI_SERVICE,
            quota={"requests": 10},
            usage={"requests": 5}
        )
        
        acc.increment_usage("requests", 3)
        
        assert acc.usage["requests"] == 8


class TestAccountToDict:
    """测试账号转字典"""

    def test_to_dict_safe(self, account):
        """测试安全转字典（不暴露凭证）"""
        acc = account.create_account(
            name="safe_dict",
            account_type=AccountType.AI_SERVICE,
            credentials={"api_key": "secret"}
        )
        
        data = acc.to_dict(safe=True)
        
        assert "credentials" not in data
        assert data["name"] == "safe_dict"

    def test_to_dict_unsafe(self, account):
        """测试非安全转字典（暴露凭证）"""
        acc = account.create_account(
            name="unsafe_dict",
            account_type=AccountType.AI_SERVICE,
            credentials={"api_key": "secret"}
        )
        
        data = acc.to_dict(safe=False)
        
        assert data["credentials"]["api_key"] == "secret"


class TestAccountModuleKernel:
    """测试 AccountModule 与 Kernel 集成"""

    def test_kernel_account_property(self, running_kernel):
        """测试 kernel.account 属性"""
        assert running_kernel.account is not None
        assert running_kernel.account.__class__.__name__ == "AccountModule"

    def test_kernel_account_through_module(self, running_kernel):
        """测试通过 kernel 创建账号"""
        acc = running_kernel.account.create_account(
            name="via_kernel",
            account_type=AccountType.EMAIL,
            provider="mailtm"
        )
        
        assert acc is not None
        assert running_kernel.account.get_account(acc.id) is acc
