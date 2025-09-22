"""
In-memory implementations of repositories for testing.
"""

from datetime import datetime
from typing import Dict, List, Optional

from app.domain.entities.delivery import Delivery
from app.domain.entities.notification import Notification
from app.domain.entities.user import User
from app.domain.repositories.delivery_repository import DeliveryRepository
from app.domain.repositories.notification_repository import NotificationRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.delivery import DeliveryId
from app.domain.value_objects.notification import NotificationId
from app.domain.value_objects.user import Email, UserId


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository."""

    def __init__(self):
        """Initialize the repository."""
        self._users: Dict[str, User] = {}

    async def save(self, user: User) -> User:
        """Save a user."""
        self._users[user.id.value] = user
        return user

    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get a user by ID."""
        return self._users.get(user_id.value)

    async def get_by_email(self, email: Email) -> Optional[User]:
        """Get a user by email."""
        for user in self._users.values():
            if user.email and user.email.value == email.value:
                return user
        return None

    async def get_all_active(self) -> List[User]:
        """Get all active users."""
        return [user for user in self._users.values() if user.is_active]

    async def delete(self, user_id: UserId) -> bool:
        """Delete a user."""
        if user_id.value in self._users:
            del self._users[user_id.value]
            return True
        return False


class InMemoryNotificationRepository(NotificationRepository):
    """In-memory implementation of NotificationRepository."""

    def __init__(self):
        """Initialize the repository."""
        self._notifications: Dict[str, Notification] = {}

    async def save(self, notification: Notification) -> Notification:
        """Save a notification."""
        self._notifications[notification.id.value] = notification
        return notification

    async def get_by_id(
        self, notification_id: NotificationId
    ) -> Optional[Notification]:
        """Get a notification by ID."""
        return self._notifications.get(notification_id.value)

    async def get_pending(self) -> List[Notification]:
        """Get all pending notifications."""
        now = datetime.now()
        return [
            n
            for n in self._notifications.values()
            if not n.sent_at or (n.scheduled_for and n.scheduled_for > now)
        ]

    async def get_by_recipient(self, recipient_id: UserId) -> List[Notification]:
        """Get all notifications for a recipient."""
        return [
            n
            for n in self._notifications.values()
            if n.recipient_id.value == recipient_id.value
        ]

    async def get_pending_notifications(self, limit: int = 100) -> List[Notification]:
        """Get pending notifications."""
        return (await self.get_pending())[:limit]


class InMemoryDeliveryRepository(DeliveryRepository):
    """In-memory implementation of DeliveryRepository."""

    def __init__(self):
        """Initialize the repository."""
        self._deliveries: Dict[str, Delivery] = {}

    async def save(self, delivery: Delivery) -> Delivery:
        """Save a delivery."""
        self._deliveries[delivery.id.value] = delivery
        return delivery

    async def get_by_id(self, delivery_id: DeliveryId) -> Optional[Delivery]:
        """Get a delivery by ID."""
        return self._deliveries.get(delivery_id.value)

    async def get_by_notification(
        self, notification_id: NotificationId
    ) -> List[Delivery]:
        """Get deliveries for a notification."""
        return [
            d
            for d in self._deliveries.values()
            if d.notification_id.value == notification_id.value
        ]

    async def get_pending_retries(self) -> List[Delivery]:
        """Get deliveries pending retry."""
        return [d for d in self._deliveries.values() if d.status.value == "retrying"]

    async def get_statistics(self) -> Dict[str, int]:
        """Get delivery statistics."""
        stats = {
            "total": len(self._deliveries),
            "pending": 0,
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "retrying": 0,
        }

        for delivery in self._deliveries.values():
            status = delivery.status.value
            if status in stats:
                stats[status] += 1

        return stats

    async def get_deliveries_for_user(self, user_id: UserId) -> List[Delivery]:
        """Get deliveries for a user."""
        return [
            d
            for d in self._deliveries.values()
            if d.recipient_id.value == user_id.value
        ]
