"""
User entity and related domain objects.
"""
from typing import Optional, Set
from datetime import datetime

from . import Entity
from ..value_objects.user import UserId, UserName, Email, PhoneNumber, TelegramChatId


class User(Entity):
    """User entity representing a notification recipient."""
    
    def __init__(
        self,
        user_id: UserId,
        name: UserName,
        email: Optional[Email] = None,
        phone: Optional[PhoneNumber] = None,
        telegram_chat_id: Optional[TelegramChatId] = None,
        is_active: bool = True
    ) -> None:
        super().__init__(user_id)
        self._name = name
        self._email = email
        self._phone = phone
        self._telegram_chat_id = telegram_chat_id
        self._is_active = is_active
        self._preferences: Set[str] = set()  # Preferred notification channels
    
    @property
    def name(self) -> UserName:
        return self._name
    
    @property
    def email(self) -> Optional[Email]:
        return self._email
    
    @property
    def phone(self) -> Optional[PhoneNumber]:
        return self._phone
    
    @property
    def telegram_chat_id(self) -> Optional[TelegramChatId]:
        return self._telegram_chat_id
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @property
    def preferences(self) -> Set[str]:
        return self._preferences.copy()
    
    def update_name(self, name: UserName) -> None:
        """Update user name."""
        self._name = name
        self._mark_updated()
    
    def update_email(self, email: Optional[Email]) -> None:
        """Update user email."""
        self._email = email
        self._mark_updated()
    
    def update_phone(self, phone: Optional[PhoneNumber]) -> None:
        """Update user phone number."""
        self._phone = phone
        self._mark_updated()
    
    def update_telegram_chat_id(self, telegram_chat_id: Optional[TelegramChatId]) -> None:
        """Update user Telegram chat ID."""
        self._telegram_chat_id = telegram_chat_id
        self._mark_updated()
    
    def activate(self) -> None:
        """Activate user for notifications."""
        if not self._is_active:
            self._is_active = True
            self._mark_updated()
    
    def deactivate(self) -> None:
        """Deactivate user from receiving notifications."""
        if self._is_active:
            self._is_active = False
            self._mark_updated()
    
    def add_preference(self, channel: str) -> None:
        """Add notification channel preference."""
        if channel not in self._preferences:
            self._preferences.add(channel)
            self._mark_updated()
    
    def remove_preference(self, channel: str) -> None:
        """Remove notification channel preference."""
        if channel in self._preferences:
            self._preferences.remove(channel)
            self._mark_updated()
    
    def has_email(self) -> bool:
        """Check if user has email configured."""
        return self._email is not None
    
    def has_phone(self) -> bool:
        """Check if user has phone configured."""
        return self._phone is not None
    
    def has_telegram(self) -> bool:
        """Check if user has Telegram configured."""
        return self._telegram_chat_id is not None
    
    def get_available_channels(self) -> Set[str]:
        """Get available notification channels for this user."""
        channels = set()
        if self.has_email():
            channels.add("email")
        if self.has_phone():
            channels.add("sms")
        if self.has_telegram():
            channels.add("telegram")
        return channels
    
    def can_receive_notifications(self) -> bool:
        """Check if user can receive notifications."""
        return self._is_active and len(self.get_available_channels()) > 0