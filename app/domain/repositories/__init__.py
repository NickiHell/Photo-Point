"""Repository interfaces for domain objects."""

from abc import ABC, abstractmethod

from ..entities.delivery import Delivery
from ..entities.notification import Notification
from ..entities.user import User
from ..value_objects.delivery import DeliveryId
from ..value_objects.notification import NotificationId
from ..value_objects.user import UserId


class UserRepository(ABC):
    """Repository interface for User entities."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Save user entity."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UserId) -> User | None:
        """Get user by ID."""
        pass

    @abstractmethod
    async def get_all_active(self) -> list[User]:
        """Get all active users."""
        pass

    @abstractmethod
    async def delete(self, user_id: UserId) -> None:
        """Delete user by ID."""
        pass


class NotificationRepository(ABC):
    """Repository interface for Notification entities."""

    @abstractmethod
    async def save(self, notification: Notification) -> None:
        """Save notification entity."""
        pass

    @abstractmethod
    async def get_by_id(self, notification_id: NotificationId) -> Notification | None:
        """Get notification by ID."""
        pass

    @abstractmethod
    async def get_pending(self, limit: int | None = None) -> list[Notification]:
        """Get pending notifications ready to be sent."""
        pass

    @abstractmethod
    async def get_by_recipient(self, recipient_id: UserId) -> list[Notification]:
        """Get notifications for specific recipient."""
        pass

    @abstractmethod
    async def delete(self, notification_id: NotificationId) -> None:
        """Delete notification by ID."""
        pass


class DeliveryRepository(ABC):
    """Repository interface for Delivery entities."""

    @abstractmethod
    async def save(self, delivery: Delivery) -> None:
        """Save delivery entity."""
        pass

    @abstractmethod
    async def get_by_id(self, delivery_id: DeliveryId) -> Delivery | None:
        """Get delivery by ID."""
        pass

    @abstractmethod
    async def get_by_notification(
        self, notification_id: NotificationId
    ) -> list[Delivery]:
        """Get deliveries for specific notification."""
        pass

    @abstractmethod
    async def get_pending_retries(self) -> list[Delivery]:
        """Get deliveries that need to be retried."""
        pass

    @abstractmethod
    async def get_statistics(self, days: int = 7) -> dict:
        """Get delivery statistics for the last N days."""
        pass
