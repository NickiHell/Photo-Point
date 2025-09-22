"""
Repository interface for delivery entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.delivery import Delivery
from app.domain.value_objects.delivery import DeliveryId
from app.domain.value_objects.notification import NotificationId


class DeliveryRepository(ABC):
    """Abstract repository for managing delivery entities."""

    @abstractmethod
    async def get_by_id(self, delivery_id: DeliveryId) -> Optional[Delivery]:
        """Get a delivery by ID."""
        pass

    @abstractmethod
    async def save(self, delivery: Delivery) -> Delivery:
        """Save a delivery."""
        pass

    @abstractmethod
    async def list_by_notification(
        self, notification_id: NotificationId
    ) -> List[Delivery]:
        """List deliveries for a notification."""
        pass

    @abstractmethod
    async def list_pending(self, limit: int = 100, offset: int = 0) -> List[Delivery]:
        """List pending deliveries."""
        pass
