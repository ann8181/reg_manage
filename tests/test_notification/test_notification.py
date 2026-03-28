"""
Notification 模块测试
"""
import pytest
from modules.notification import (
    NotificationModule,
    NotificationChannel,
    NotificationResult,
    EmailChannel,
    DingTalkChannel,
    FeishuChannel,
    SlackChannel,
    WebhookChannel,
    ChannelType
)


class TestNotificationResult:
    """测试通知结果"""

    def test_result_success(self):
        """测试成功结果"""
        result = NotificationResult(True, "email", "Sent successfully")
        
        assert result.success is True
        assert result.channel == "email"
        assert result.message == "Sent successfully"
        assert result.error == ""

    def test_result_failure(self):
        """测试失败结果"""
        result = NotificationResult(False, "email", error="SMTP connection failed")
        
        assert result.success is False
        assert result.error == "SMTP connection failed"

    def test_result_to_dict(self):
        """测试转字典"""
        result = NotificationResult(True, "slack", "OK")
        
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["channel"] == "slack"


class TestEmailChannel:
    """测试邮件渠道"""

    def test_create_email_channel(self):
        """测试创建邮件渠道"""
        config = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test@gmail.com",
            "smtp_password": "password",
            "to_addrs": ["recipient@example.com"]
        }
        channel = EmailChannel("test_email", config)
        
        assert channel.name == "test_email"
        assert channel.smtp_host == "smtp.gmail.com"

    def test_validate_config_complete(self):
        """测试配置完整验证"""
        config = {
            "smtp_host": "smtp.gmail.com",
            "smtp_user": "test@gmail.com",
            "smtp_password": "password"
        }
        channel = EmailChannel(config=config)
        
        assert channel.validate_config() is True

    def test_validate_config_incomplete(self):
        """测试配置不完整验证"""
        config = {
            "smtp_host": "smtp.gmail.com"
        }
        channel = EmailChannel(config=config)
        
        assert channel.validate_config() is False


class TestDingTalkChannel:
    """测试钉钉渠道"""

    def test_create_dingtalk_channel(self):
        """测试创建钉钉渠道"""
        config = {
            "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx"
        }
        channel = DingTalkChannel(config=config)
        
        assert channel.webhook_url == "https://oapi.dingtalk.com/robot/send?access_token=xxx"

    def test_validate_config(self):
        """测试配置验证"""
        config = {"webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx"}
        channel = DingTalkChannel(config=config)
        
        assert channel.validate_config() is True


class TestFeishuChannel:
    """测试飞书渠道"""

    def test_create_feishu_channel(self):
        """测试创建飞书渠道"""
        config = {"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"}
        channel = FeishuChannel(config=config)
        
        assert channel.webhook_url == "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"


class TestSlackChannel:
    """测试 Slack 渠道"""

    def test_create_slack_channel(self):
        """测试创建 Slack 渠道"""
        config = {
            "webhook_url": "https://hooks.slack.com/services/xxx",
            "channel": "#alerts"
        }
        channel = SlackChannel(config=config)
        
        assert channel.channel == "#alerts"


class TestNotificationModule:
    """测试通知模块"""

    def test_create_module(self, notification):
        """测试创建通知模块"""
        assert notification is not None
        assert notification.default_channel is None

    def test_register_email_channel(self, notification):
        """测试注册邮件渠道"""
        result = notification.register_email(
            name="my_email",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            to_addrs=["test@example.com"],
            set_default=True
        )
        
        assert result is True
        assert "my_email" in notification.list_channels()
        assert notification.default_channel == "my_email"

    def test_register_dingtalk_channel(self, notification):
        """测试注册钉钉渠道"""
        result = notification.register_dingtalk(
            name="dingtalk",
            webhook_url="https://oapi.dingtalk.com/robot/send?access_token=xxx",
            set_default=True
        )
        
        assert result is True
        assert "dingtalk" in notification.list_channels()

    def test_register_feishu_channel(self, notification):
        """测试注册飞书渠道"""
        result = notification.register_feishu(
            name="feishu",
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
        )
        
        assert result is True

    def test_register_slack_channel(self, notification):
        """测试注册 Slack 渠道"""
        result = notification.register_slack(
            name="slack",
            webhook_url="https://hooks.slack.com/services/xxx",
            channel="#notifications"
        )
        
        assert result is True

    def test_get_channel(self, notification):
        """测试获取渠道"""
        notification.register_email(
            name="get_test",
            smtp_host="smtp.gmail.com",
            smtp_user="test@gmail.com",
            smtp_password="password"
        )
        
        channel = notification.get_channel("get_test")
        
        assert channel is not None
        assert channel.name == "get_test"

    def test_get_nonexistent_channel(self, notification):
        """测试获取不存在的渠道"""
        channel = notification.get_channel("nonexistent")
        
        assert channel is None

    def test_remove_channel(self, notification):
        """测试移除渠道"""
        notification.register_email(
            name="remove_test",
            smtp_host="smtp.gmail.com",
            smtp_user="test@gmail.com",
            smtp_password="password"
        )
        
        result = notification.remove_channel("remove_test")
        
        assert result is True
        assert notification.get_channel("remove_test") is None

    def test_list_channels(self, notification):
        """测试列出渠道"""
        notification.register_email(name="ch1", smtp_host="smtp1.com", smtp_user="u1", smtp_password="p")
        notification.register_dingtalk(name="ch2", webhook_url="http://test.com")
        
        channels = notification.list_channels()
        
        assert len(channels) >= 2

    def test_send_without_channel(self, notification):
        """测试未配置渠道时发送"""
        result = notification.send("test message")
        
        assert result.success is False
        assert "No channel" in result.error


class TestNotificationModuleKernelIntegration:
    """测试 NotificationModule 与 Kernel 集成"""

    def test_kernel_notification_property(self, running_kernel):
        """测试 kernel.notification 属性"""
        assert running_kernel.notification is not None
        assert running_kernel.notification.__class__.__name__ == "NotificationModule"

    def test_workflow_notify_step(self, running_kernel, mocker):
        """测试工作流 NOTIFY 步骤"""
        from modules.workflow import WorkflowStep
        
        notification = running_kernel.notification
        notification.register_dingtalk(
            name="test_notify",
            webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test"
        )
        
        mocker.patch("requests.post", return_value=mocker.Mock(status_code=200, json=lambda: {"errcode": 0}))
        
        wf = running_kernel.workflow.create_workflow("notify_test")
        step = WorkflowStep(
            id="notify_step",
            name="Notify",
            step_type="notify",
            params={"message": "Test notification", "channel": "test_notify"}
        )
        running_kernel.workflow.add_step(wf.id, step)
        
        result = running_kernel.workflow.execute_workflow(wf.id)
        
        assert result is not None
