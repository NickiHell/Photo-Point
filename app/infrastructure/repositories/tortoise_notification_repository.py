"""
Notification repository implementation based on Tortoise ORM.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from app.domain.entities.notification import Notification
from app.domain.repositories.notification_repository import NotificationRepository
from app.domain.value_objects.notification import (
    MessageTemplate,
    NotificationId,
    NotificationPriority,
)
from app.domain.value_objects.user import UserId
from app.infrastructure.repositories.tortoise_models import NotificationModel


class TortoiseNotificationRepository(NotificationRepository):
    """Tortoise ORM implementation of the NotificationRepository."""

    async def get_by_id(
        self, notification_id: NotificationId
    ) -> Optional[Notification]:
        """Get a notification by ID."""
        notification_model = await NotificationModel.get_or_none(
            id=notification_id.value
        )
        if not notification_model:
            return None

        return await self._model_to_entity(notification_model)

    async def save(self, notification: Notification) -> Notification:
        """Save a notification."""
        notification_data = {
            "id": notification.id.value,
            "recipient_id": notification.recipient_id.value,
            "message_template": notification.message.content.value,
            "message_variables": notification.message.template_data,
            "channels": [channel.value for channel in notification.channels],
            "priority": notification.priority.value,
            "scheduled_at": notification.scheduled_at,
            "sent_at": notification.sent_at,
            "retry_policy": {
                "max_retries": notification.retry_policy.max_retries,
                "delay": notification.retry_policy.delay,
                "backoff_factor": notification.retry_policy.backoff_factor,
            },
            "notification_metadata": notification.metadata,
        }

        notification_model, created = await NotificationModel.update_or_create(
            id=notification.id.value, defaults=notification_data
        )

        return await self._model_to_entity(notification_model)

    async def list_pending(
        self, limit: int = 100, offset: int = 0
    ) -> List[Notification]:
        """List pending notifications."""
        now = datetime.utcnow()
        notification_models = (
            await NotificationModel.filter(scheduled_at__lte=now, sent_at__isnull=True)
            .limit(limit)
            .offset(offset)
        )

        return [
            await self._model_to_entity(notification_model)
            for notification_model in notification_models
        ]

    async def list_by_recipient(
        self, recipient_id: UserId, limit: int = 100, offset: int = 0
    ) -> List[Notification]:
        """List notifications by recipient."""
        notification_models = (
            await NotificationModel.filter(recipient_id=recipient_id.value)
            .limit(limit)
            .offset(offset)
        )

        return [
            await self._model_to_entity(notification_model)
            for notification_model in notification_models
        ]

    async def _model_to_entity(
        self, notification_model: NotificationModel
    ) -> Notification:
        """Convert a NotificationModel to a Notification entity."""
        from app.domain.entities.notification import NotificationType
        from app.domain.value_objects.delivery import RetryPolicy

        channels = [
            NotificationType(channel) for channel in notification_model.channels
        ]

        retry_policy_data = notification_model.retry_policy or {}
        retry_policy = RetryPolicy(
            max_retries=retry_policy_data.get("max_retries", 3),
            delay=retry_policy_data.get("delay", 60),
            backoff_factor=retry_policy_data.get("backoff_factor", 2),
        )

        return Notification(
            id=NotificationId(notification_model.id),
            recipient_id=UserId(notification_model.recipient_id),
            message=MessageTemplate(
                content=notification_model.message_template,
                template_data=notification_model.message_variables,
            ),
            channels=channels,
            priority=NotificationPriority(notification_model.priority),
            scheduled_at=notification_model.scheduled_at,
            sent_at=notification_model.sent_at,
            retry_policy=retry_policy,
            metadata=notification_model.notification_metadata or {},
        )
