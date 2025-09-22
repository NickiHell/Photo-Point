"""
Repository interface for notification entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.notification import Notification
from app.domain.value_objects.notification import NotificationId
from app.domain.value_objects.user import UserId


class NotificationRepository(ABC):
    """Abstract repository for managing notification entities."""

    @abstractmethod
    async def get_by_id(
        self, notification_id: NotificationId
    ) -> Optional[Notification]:
        """Get a notification by ID."""
        pass

    @abstractmethod
    async def save(self, notification: Notification) -> Notification:
        """Save a notification."""
        pass

    @abstractmethod
    async def list_by_recipient(
        self, recipient_id: UserId, limit: int = 100, offset: int = 0
    ) -> List[Notification]:
        """List notifications for a recipient."""
        pass

    @abstractmethod
    async def list_pending(
        self, limit: int = 100, offset: int = 0
    ) -> List[Notification]:
        """List pending notifications."""
        pass
