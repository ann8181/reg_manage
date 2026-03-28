"""
Webhook 模块测试
"""
import pytest
import hmac
import hashlib
from modules.webhook import (
    WebhookModule,
    Webhook,
    Delivery,
    EventType,
    DeliveryStatus
)


class TestWebhookModule:
    """测试 Webhook 模块"""

    def test_create_module(self, webhook):
        """测试创建模块"""
        assert webhook is not None
        assert len(webhook._webhooks) == 0

    def test_register_webhook(self, webhook):
        """测试注册 Webhook"""
        webhook_id = webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"]
        )
        
        assert webhook_id is not None
        assert webhook_id in webhook._webhooks

    def test_unregister_webhook(self, webhook):
        """测试注销 Webhook"""
        webhook_id = webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"]
        )
        
        result = webhook.unregister(webhook_id)
        
        assert result is True
        assert webhook_id not in webhook._webhooks

    def test_get_webhook(self, webhook):
        """测试获取 Webhook"""
        webhook_id = webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"]
        )
        
        webhook_obj = webhook.get(webhook_id)
        
        assert webhook_obj is not None
        assert webhook_obj.name == "test_webhook"

    def test_get_nonexistent_webhook(self, webhook):
        """测试获取不存在的 Webhook"""
        result = webhook.get("nonexistent")
        
        assert result is None

    def test_list_webhooks(self, webhook):
        """测试列出 Webhooks"""
        webhook.register(name="wh1", url="https://example.com/1", events=["task.completed"])
        webhook.register(name="wh2", url="https://example.com/2", events=["task.failed"])
        
        webhooks = webhook.list_webhooks()
        
        assert len(webhooks) == 2

    def test_list_webhooks_by_event(self, webhook):
        """测试按事件列出 Webhooks"""
        webhook.register(name="wh1", url="https://example.com/1", events=["task.completed"])
        webhook.register(name="wh2", url="https://example.com/2", events=["task.failed"])
        
        webhooks = webhook.list_webhooks(event="task.completed")
        
        assert len(webhooks) == 1
        assert webhooks[0].name == "wh1"

    def test_enable_webhook(self, webhook):
        """测试启用 Webhook"""
        webhook_id = webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"],
            enabled=False
        )
        
        result = webhook.enable(webhook_id)
        
        assert result is True
        assert webhook.get(webhook_id).enabled is True

    def test_disable_webhook(self, webhook):
        """测试禁用 Webhook"""
        webhook_id = webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"]
        )
        
        result = webhook.disable(webhook_id)
        
        assert result is True
        assert webhook.get(webhook_id).enabled is False


class TestWebhookTrigger:
    """测试 Webhook 触发"""

    def test_trigger_event(self, webhook, mocker):
        """测试触发事件"""
        webhook_id = webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"],
            retry_count=0
        )
        
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post = mocker.patch("requests.post", return_value=mock_response)
        
        deliveries = webhook.trigger("task.completed", {"task_id": "123"})
        
        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.SUCCESS.value
        mock_post.assert_called_once()

    def test_trigger_with_signature(self, webhook, mocker):
        """测试带签名的触发"""
        webhook_id = webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"],
            secret="my_secret",
            retry_count=0
        )
        
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post = mocker.patch("requests.post", return_value=mock_response)
        
        webhook.trigger("task.completed", {"task_id": "123"})
        
        call_kwargs = mock_post.call_args[1]
        assert "X-Webhook-Signature" in call_kwargs["headers"]

    def test_trigger_no_matching_webhooks(self, webhook, mocker):
        """测试无匹配的 Webhook 时触发"""
        webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"]
        )
        
        deliveries = webhook.trigger("nonexistent.event", {})
        
        assert len(deliveries) == 0

    def test_local_handler(self, webhook):
        """测试本地处理器"""
        received = []
        
        def handler(event, payload):
            received.append((event, payload))
        
        webhook.subscribe("task.completed", handler)
        webhook.trigger("task.completed", {"task_id": "123"})
        
        assert len(received) == 1
        assert received[0][0] == "task.completed"


class TestWebhookSignature:
    """测试签名验证"""

    def test_generate_signature(self, webhook):
        """测试生成签名"""
        payload = '{"test": true}'
        secret = "my_secret"
        
        signature = webhook._generate_signature(payload, secret)
        
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        assert signature == expected

    def test_verify_signature(self, webhook):
        """测试验证签名"""
        payload = '{"test": true}'
        secret = "my_secret"
        signature = webhook._generate_signature(payload, secret)
        
        result = webhook._verify_signature(payload, signature, secret)
        
        assert result is True

    def test_verify_invalid_signature(self, webhook):
        """测试验证无效签名"""
        payload = '{"test": true}'
        secret = "my_secret"
        
        result = webhook._verify_signature(payload, "invalid_signature", secret)
        
        assert result is False


class TestWebhookModuleKernelIntegration:
    """测试 WebhookModule 与 Kernel 集成"""

    def test_kernel_webhook_property(self, running_kernel):
        """测试 kernel.webhook 属性"""
        assert running_kernel.webhook is not None
        assert running_kernel.webhook.__class__.__name__ == "WebhookModule"

    def test_webhook_stats(self, webhook):
        """测试 Webhook 统计"""
        webhook.register(
            name="test_webhook",
            url="https://example.com/webhook",
            events=["task.completed"]
        )
        
        stats = webhook.get_stats()
        
        assert stats["webhooks"] == 1
        assert "total_deliveries" in stats
