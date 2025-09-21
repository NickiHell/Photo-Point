"""
In-memory repository implementations for development and testing.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from ...domain.entities.user import User
from ...domain.entities.notification import Notification
from ...domain.entities.delivery import Delivery
from ...domain.value_objects.user import UserId
from ...domain.value_objects.notification import NotificationId
from ...domain.value_objects.delivery import DeliveryId, DeliveryStatus
from ...domain.repositories import UserRepository, NotificationRepository, DeliveryRepository


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository."""
    
    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
    
    async def save(self, user: User) -> None:
        """Save user entity."""
        self._users[user.id.value] = user
    
    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id.value)
    
    async def get_all_active(self) -> List[User]:
        """Get all active users."""
        return [user for user in self._users.values() if user.is_active]
    
    async def delete(self, user_id: UserId) -> None:
        """Delete user by ID."""
        if user_id.value in self._users:
            del self._users[user_id.value]


class InMemoryNotificationRepository(NotificationRepository):
    """In-memory implementation of NotificationRepository."""
    
    def __init__(self) -> None:
        self._notifications: Dict[str, Notification] = {}
    
    async def save(self, notification: Notification) -> None:
        """Save notification entity."""
        self._notifications[notification.id.value] = notification
    
    async def get_by_id(self, notification_id: NotificationId) -> Optional[Notification]:
        """Get notification by ID."""
        return self._notifications.get(notification_id.value)
    
    async def get_pending(self, limit: Optional[int] = None) -> List[Notification]:
        """Get pending notifications ready to be sent."""
        now = datetime.utcnow()
        pending_notifications = [
            notification for notification in self._notifications.values()
            if notification.is_ready_to_send() and notification.scheduled_at <= now
        ]
        
        # Sort by priority and scheduled time
        pending_notifications.sort(
            key=lambda n: (n.priority.value, n.scheduled_at)
        )
        
        if limit:
            pending_notifications = pending_notifications[:limit]
        
        return pending_notifications
    
    async def get_by_recipient(self, recipient_id: UserId) -> List[Notification]:
        """Get notifications for specific recipient."""
        return [
            notification for notification in self._notifications.values()
            if notification.recipient_id.value == recipient_id.value
        ]
    
    async def delete(self, notification_id: NotificationId) -> None:
        """Delete notification by ID."""
        if notification_id.value in self._notifications:
            del self._notifications[notification_id.value]


class InMemoryDeliveryRepository(DeliveryRepository):
    """In-memory implementation of DeliveryRepository."""
    
    def __init__(self) -> None:
        self._deliveries: Dict[str, Delivery] = {}
    
    async def save(self, delivery: Delivery) -> None:
        """Save delivery entity."""
        self._deliveries[delivery.id.value] = delivery
    
    async def get_by_id(self, delivery_id: DeliveryId) -> Optional[Delivery]:
        """Get delivery by ID."""
        return self._deliveries.get(delivery_id.value)
    
    async def get_by_notification(self, notification_id: NotificationId) -> List[Delivery]:
        """Get deliveries for specific notification."""
        return [
            delivery for delivery in self._deliveries.values()
            if delivery.notification.id.value == notification_id.value
        ]
    
    async def get_pending_retries(self) -> List[Delivery]:
        """Get deliveries that need to be retried."""
        return [
            delivery for delivery in self._deliveries.values()
            if delivery.status == DeliveryStatus.RETRYING
        ]
    
    async def get_statistics(self, days: int = 7) -> dict:
        """Get delivery statistics for the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_deliveries = [
            delivery for delivery in self._deliveries.values()
            if delivery.created_at.replace(tzinfo=None) >= cutoff_date
        ]
        
        total_deliveries = len(recent_deliveries)
        successful_deliveries = len([
            d for d in recent_deliveries 
            if d.status == DeliveryStatus.DELIVERED
        ])
        failed_deliveries = len([
            d for d in recent_deliveries 
            if d.status == DeliveryStatus.FAILED
        ])
        pending_deliveries = len([
            d for d in recent_deliveries 
            if d.status in [DeliveryStatus.PENDING, DeliveryStatus.SENT, DeliveryStatus.RETRYING]
        ])
        
        # Calculate average delivery time for successful deliveries
        successful_with_time = [
            d for d in recent_deliveries 
            if d.status == DeliveryStatus.DELIVERED and d.get_total_delivery_time()
        ]
        avg_delivery_time = None
        if successful_with_time:
            avg_delivery_time = sum(d.get_total_delivery_time() for d in successful_with_time) / len(successful_with_time)
        
        # Count by provider
        provider_stats = {}
        for delivery in recent_deliveries:
            for attempt in delivery.attempts:
                provider = attempt.provider
                if provider not in provider_stats:
                    provider_stats[provider] = {"total": 0, "successful": 0}
                provider_stats[provider]["total"] += 1
                if attempt.result.success:
                    provider_stats[provider]["successful"] += 1
        
        return {
            "period_days": days,
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": failed_deliveries,
            "pending_deliveries": pending_deliveries,
            "success_rate": (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0,
            "average_delivery_time": avg_delivery_time,
            "provider_statistics": provider_stats
        }