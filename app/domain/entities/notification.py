"""
Notification entity and related domain objects.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from . import Entity
from ..value_objects.notification import (
    NotificationId, NotificationType, NotificationPriority, 
    MessageTemplate, RenderedMessage
)
from ..value_objects.user import UserId


class Notification(Entity):
    """Notification entity representing a message to be sent."""
    
    def __init__(
        self,
        notification_id: NotificationId,
        recipient_id: UserId,
        message_template: MessageTemplate,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(notification_id)
        self._recipient_id = recipient_id
        self._message_template = message_template
        self._priority = priority
        self._scheduled_at = scheduled_at or datetime.now(timezone.utc)
        self._expires_at = expires_at
        self._metadata = metadata or {}
        self._is_cancelled = False
    
    @property
    def recipient_id(self) -> UserId:
        return self._recipient_id
    
    @property
    def message_template(self) -> MessageTemplate:
        return self._message_template
    
    @property
    def priority(self) -> NotificationPriority:
        return self._priority
    
    @property
    def scheduled_at(self) -> datetime:
        return self._scheduled_at
    
    @property
    def expires_at(self) -> Optional[datetime]:
        return self._expires_at
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata.copy()
    
    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled
    
    def render_message(self) -> RenderedMessage:
        """Render the notification message."""
        return self._message_template.render()
    
    def update_priority(self, priority: NotificationPriority) -> None:
        """Update notification priority."""
        if self._is_cancelled:
            raise ValueError("Cannot update cancelled notification")
        
        self._priority = priority
        self._mark_updated()
    
    def reschedule(self, scheduled_at: datetime) -> None:
        """Reschedule notification."""
        if self._is_cancelled:
            raise ValueError("Cannot reschedule cancelled notification")
        
        if scheduled_at <= datetime.now(timezone.utc):
            raise ValueError("Cannot schedule notification in the past")
        
        self._scheduled_at = scheduled_at
        self._mark_updated()
    
    def cancel(self) -> None:
        """Cancel the notification."""
        if not self._is_cancelled:
            self._is_cancelled = True
            self._mark_updated()
    
    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if self._expires_at is None:
            return False
        return datetime.now(timezone.utc) > self._expires_at
    
    def is_ready_to_send(self) -> bool:
        """Check if notification is ready to be sent."""
        now = datetime.now(timezone.utc)
        return (
            not self._is_cancelled
            and not self.is_expired()
            and self._scheduled_at <= now
        )
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to notification."""
        self._metadata[key] = value
        self._mark_updated()
    
    def remove_metadata(self, key: str) -> None:
        """Remove metadata from notification."""
        if key in self._metadata:
            del self._metadata[key]
            self._mark_updated()