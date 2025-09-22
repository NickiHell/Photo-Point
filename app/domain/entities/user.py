"""
User entity and related domain objects.
"""

from ..value_objects.user import Email, PhoneNumber, TelegramChatId, UserId, UserName
from . import Entity


class User(Entity):
    """User entity representing a notification recipient."""

    def __init__(
        self,
        user_id: UserId = None,
        name: UserName = None,
        email: Email | None = None,
        phone: PhoneNumber | None = None,
        telegram_chat_id: TelegramChatId | None = None,
        is_active: bool = True,
        # Compat parameters for tests
        id: UserId = None,
        phone_number: PhoneNumber | None = None,
        telegram_id: TelegramChatId | None = None,
        preferences: dict | None = None,
    ) -> None:
        # Handle both parameter naming conventions
        entity_id = id if id is not None else user_id
        if entity_id is None:
            raise ValueError("Must provide either id or user_id")

        super().__init__(entity_id)
        self._name = name
        self._email = email
        self._phone = phone_number if phone_number is not None else phone
        self._telegram_chat_id = (
            telegram_id if telegram_id is not None else telegram_chat_id
        )
        self._is_active = is_active
        self._preferences: set[str] = set()  # Preferred notification channels

        # Initialize preferences if provided
        if preferences:
            for channel in preferences:
                self.add_preference(channel)

    @property
    def name(self) -> UserName:
        return self._name

    @property
    def email(self) -> Email | None:
        return self._email

    @property
    def phone(self) -> PhoneNumber | None:
        return self._phone

    @property
    def telegram_chat_id(self) -> TelegramChatId | None:
        return self._telegram_chat_id

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def preferences(self) -> set[str]:
        """Return user preferences as a set."""
        return self._preferences.copy()

    @property
    def phone_number(self) -> PhoneNumber | None:
        """Alias for phone for compatibility."""
        return self._phone

    @property
    def telegram_id(self) -> TelegramChatId | None:
        """Alias for telegram_chat_id for compatibility."""
        return self._telegram_chat_id

    def update_name(self, name: UserName) -> None:
        """Update user name."""
        self._name = name
        self._mark_updated()

    def update_email(self, email: Email | None) -> None:
        """Update user email."""
        self._email = email
        self._mark_updated()

    def update_phone(self, phone: PhoneNumber | None) -> None:
        """Update user phone number."""
        self._phone = phone
        self._mark_updated()

    def update_telegram_chat_id(self, telegram_chat_id: TelegramChatId | None) -> None:
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

    def get_available_channels(self) -> set[str]:
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
