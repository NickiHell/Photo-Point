"""
Repository interfaces for the domain layer.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.user import User
from ..entities.notification import Notification
from ..entities.delivery import Delivery
from ..value_objects.user import UserId
from ..value_objects.notification import NotificationId
from ..value_objects.delivery import DeliveryId


class UserRepository(ABC):
    """Repository interface for User entities."""
    
    @abstractmethod
    async def save(self, user: User) -> None:
        """Save user entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_all_active(self) -> List[User]:
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
    async def get_by_id(self, notification_id: NotificationId) -> Optional[Notification]:
        """Get notification by ID."""
        pass
    
    @abstractmethod
    async def get_pending(self, limit: Optional[int] = None) -> List[Notification]:
        """Get pending notifications ready to be sent."""
        pass
    
    @abstractmethod
    async def get_by_recipient(self, recipient_id: UserId) -> List[Notification]:
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
    async def get_by_id(self, delivery_id: DeliveryId) -> Optional[Delivery]:
        """Get delivery by ID."""
        pass
    
    @abstractmethod
    async def get_by_notification(self, notification_id: NotificationId) -> List[Delivery]:
        """Get deliveries for specific notification."""
        pass
    
    @abstractmethod
    async def get_pending_retries(self) -> List[Delivery]:
        """Get deliveries that need to be retried."""
        pass
    
    @abstractmethod
    async def get_statistics(self, days: int = 7) -> dict:
        """Get delivery statistics for the last N days."""
        pass