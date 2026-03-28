"""
Webhook Module - Webhook 事件驱动模块
支持 Webhook 注册、事件订阅、签名验证和重试机制
"""

import json
import hmac
import hashlib
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class EventType(Enum):
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    SCHEDULE_TRIGGERED = "schedule.triggered"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_UPDATED = "account.updated"
    NOTIFICATION_SENT = "notification.sent"
    CUSTOM = "custom"


class DeliveryStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Webhook:
    """Webhook 定义"""
    id: str
    name: str
    url: str
    events: List[str]
    secret: str = ""
    headers: Dict[str, str] = None
    enabled: bool = True
    retry_count: int = 3
    retry_delay: float = 1.0
    timeout: float = 10.0
    content_type: str = "application/json"


@dataclass
class Delivery:
    """Webhook 投递记录"""
    id: str
    webhook_id: str
    event: str
    payload: Dict[str, Any]
    status: str = DeliveryStatus.PENDING.value
    attempts: int = 0
    last_attempt: float = 0
    response_code: int = 0
    response_body: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)


class WebhookModule:
    """
    Webhook 模块
    提供事件驱动的 Webhook 订阅和投递
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self._webhooks: Dict[str, Webhook] = {}
        self._handlers: Dict[str, List[Callable]] = {}
        self._deliveries: List[Delivery] = []
        self._deliveries_lock = threading.Lock()
        self._logger = kernel.get_logger("webhook")
        self._logger.info("WebhookModule initialized")
    
    def register(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: str = "",
        headers: Dict[str, str] = None,
        enabled: bool = True,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 10.0
    ) -> str:
        """注册 Webhook"""
        import uuid
        webhook_id = str(uuid.uuid4())[:8]
        
        webhook = Webhook(
            id=webhook_id,
            name=name,
            url=url,
            events=events,
            secret=secret,
            headers=headers or {},
            enabled=enabled,
            retry_count=retry_count,
            retry_delay=retry_delay,
            timeout=timeout
        )
        
        self._webhooks[webhook_id] = webhook
        self._logger.info(f"Webhook registered: {name} ({webhook_id}) for events: {events}")
        return webhook_id
    
    def unregister(self, webhook_id: str) -> bool:
        """注销 Webhook"""
        if webhook_id in self._webhooks:
            webhook = self._webhooks[webhook_id]
            del self._webhooks[webhook_id]
            self._logger.info(f"Webhook unregistered: {webhook.name}")
            return True
        return False
    
    def get(self, webhook_id: str) -> Optional[Webhook]:
        """获取 Webhook"""
        return self._webhooks.get(webhook_id)
    
    def list_webhooks(self, event: str = None, enabled_only: bool = False) -> List[Webhook]:
        """列出 Webhooks"""
        webhooks = list(self._webhooks.values())
        
        if event:
            webhooks = [w for w in webhooks if event in w.events]
        
        if enabled_only:
            webhooks = [w for w in webhooks if w.enabled]
        
        return webhooks
    
    def enable(self, webhook_id: str) -> bool:
        """启用 Webhook"""
        webhook = self._webhooks.get(webhook_id)
        if webhook:
            webhook.enabled = True
            return True
        return False
    
    def disable(self, webhook_id: str) -> bool:
        """禁用 Webhook"""
        webhook = self._webhooks.get(webhook_id)
        if webhook:
            webhook.enabled = False
            return True
        return False
    
    def subscribe(self, event: str, handler: Callable):
        """订阅本地事件"""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
    
    def unsubscribe(self, event: str, handler: Callable) -> bool:
        """取消订阅"""
        if event in self._handlers:
            try:
                self._handlers[event].remove(handler)
                return True
            except ValueError:
                pass
        return False
    
    def _generate_signature(self, payload: str, secret: str, timestamp: str = None) -> str:
        """生成签名"""
        if not secret:
            return ""
        
        if timestamp:
            signed_payload = f"{timestamp}.{payload}"
        else:
            signed_payload = payload
        
        return hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """验证签名"""
        if not secret or not signature:
            return True
        
        expected = self._generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)
    
    def trigger(self, event: str, payload: Dict[str, Any]) -> List[Delivery]:
        """触发事件"""
        deliveries = []
        webhooks = self.list_webhooks(event=event, enabled_only=True)
        
        for webhook in webhooks:
            delivery = self._deliver_to_webhook(webhook, event, payload)
            deliveries.append(delivery)
        
        local_handlers = self._handlers.get(event, [])
        for handler in local_handlers:
            try:
                handler(event, payload)
            except Exception as e:
                self._logger.error(f"Local handler error for {event}: {e}")
        
        return deliveries
    
    def _deliver_to_webhook(self, webhook: Webhook, event: str, payload: Dict[str, Any]) -> Delivery:
        """投递到 Webhook"""
        import uuid
        import requests
        
        delivery_id = str(uuid.uuid4())[:8]
        delivery = Delivery(
            id=delivery_id,
            webhook_id=webhook.id,
            event=event,
            payload=payload
        )
        
        self._deliveries.append(delivery)
        
        headers = webhook.headers.copy()
        headers["Content-Type"] = webhook.content_type
        headers["X-Webhook-Event"] = event
        headers["X-Webhook-Delivery"] = delivery_id
        headers["X-Webhook-Timestamp"] = str(int(time.time()))
        
        if webhook.secret:
            timestamp = headers["X-Webhook-Timestamp"]
            payload_str = json.dumps(payload)
            signature = self._generate_signature(payload_str, webhook.secret, timestamp)
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        payload_str = json.dumps(payload)
        
        for attempt in range(webhook.retry_count + 1):
            try:
                response = requests.post(
                    webhook.url,
                    data=payload_str,
                    headers=headers,
                    timeout=webhook.timeout
                )
                
                delivery.attempts += 1
                delivery.last_attempt = time.time()
                delivery.response_code = response.status_code
                delivery.response_body = response.text[:1000] if response.text else ""
                
                if 200 <= response.status_code < 300:
                    delivery.status = DeliveryStatus.SUCCESS.value
                    self._logger.info(f"Webhook delivered successfully: {webhook.name}")
                    break
                else:
                    delivery.error = f"HTTP {response.status_code}"
                    
            except requests.Timeout:
                delivery.error = "Timeout"
            except requests.RequestException as e:
                delivery.error = str(e)
            
            if attempt < webhook.retry_count:
                delivery.status = DeliveryStatus.RETRYING.value
                time.sleep(webhook.retry_delay * (attempt + 1))
        
        if delivery.status != DeliveryStatus.SUCCESS.value:
            delivery.status = DeliveryStatus.FAILED.value
            self._logger.error(f"Webhook delivery failed: {webhook.name} - {delivery.error}")
        
        return delivery
    
    def get_deliveries(
        self,
        webhook_id: str = None,
        status: str = None,
        limit: int = 100
    ) -> List[Delivery]:
        """获取投递记录"""
        deliveries = self._deliveries
        
        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]
        
        if status:
            deliveries = [d for d in deliveries if d.status == status]
        
        return deliveries[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._deliveries)
        success = sum(1 for d in self._deliveries if d.status == DeliveryStatus.SUCCESS.value)
        failed = sum(1 for d in self._deliveries if d.status == DeliveryStatus.FAILED.value)
        pending = sum(1 for d in self._deliveries if d.status == DeliveryStatus.PENDING.value)
        
        return {
            "webhooks": len(self._webhooks),
            "total_deliveries": total,
            "success": success,
            "failed": failed,
            "pending": pending,
            "success_rate": success / total if total > 0 else 0
        }
    
    def test_webhook(self, webhook_id: str) -> Delivery:
        """测试 Webhook"""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return None
        
        payload = {
            "test": True,
            "timestamp": time.time(),
            "message": "This is a test webhook delivery"
        }
        
        return self._deliver_to_webhook(webhook, "test", payload)
    
    def stop(self):
        """停止模块"""
        self._logger.info("WebhookModule stopped")
