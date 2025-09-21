"""
Base entity implementation.
"""
from abc import ABC
from typing import Any, Optional, Dict
from datetime import datetime, timezone


class Entity(ABC):
    """Base class for all entities."""
    
    def __init__(self, entity_id: Any) -> None:
        self._id = entity_id
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = self._created_at
    
    @property
    def id(self) -> Any:
        return self._id
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def _mark_updated(self) -> None:
        """Mark entity as updated."""
        self._updated_at = datetime.now(timezone.utc)
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id!r})"


class User(Entity):
    """User entity."""
    
    def __init__(self, user_id: str, email: Optional[str] = None, 
                 phone_number: Optional[str] = None, telegram_id: Optional[str] = None,
                 preferences: Optional[Dict[str, Any]] = None, is_active: bool = True):
        super().__init__(user_id)
        self._email = email
        self._phone_number = phone_number
        self._telegram_id = telegram_id
        self._preferences = preferences or {}
        self._is_active = is_active
    
    @property
    def email(self) -> Optional[str]:
        return self._email
    
    @property
    def phone_number(self) -> Optional[str]:
        return self._phone_number
    
    @property
    def telegram_id(self) -> Optional[str]:
        return self._telegram_id
    
    @property
    def preferences(self) -> Dict[str, Any]:
        return self._preferences.copy()
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def update_email(self, email: str) -> None:
        """Update user email."""
        self._email = email
        self._mark_updated()
    
    def update_phone(self, phone_number: str) -> None:
        """Update user phone number."""
        self._phone_number = phone_number
        self._mark_updated()
    
    def deactivate(self) -> None:
        """Deactivate user."""
        self._is_active = False
        self._mark_updated()
    
    def activate(self) -> None:
        """Activate user."""
        self._is_active = True
        self._mark_updated()


class Notification(Entity):
    """Notification entity."""
    
    def __init__(self, notification_id: str, recipient_id: str, message_template: str,
                 channels: list, priority: str = "MEDIUM"):
        super().__init__(notification_id)
        self._recipient_id = recipient_id
        self._message_template = message_template
        self._channels = channels or []
        self._priority = priority
        self._status = "PENDING"
    
    @property
    def recipient_id(self) -> str:
        return self._recipient_id
    
    @property
    def message_template(self) -> str:
        return self._message_template
    
    @property
    def channels(self) -> list:
        return self._channels.copy()
    
    @property
    def priority(self) -> str:
        return self._priority
    
    @property
    def status(self) -> str:
        return self._status
    
    def mark_sent(self) -> None:
        """Mark notification as sent."""
        self._status = "SENT"
        self._mark_updated()
    
    def mark_failed(self) -> None:
        """Mark notification as failed."""
        self._status = "FAILED"
        self._mark_updated()