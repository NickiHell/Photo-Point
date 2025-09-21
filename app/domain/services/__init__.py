"""
Domain services for notification business logic.
"""
from abc import ABC, abstractmethod
from typing import List, Set

from ..entities.notification import Notification
from ..entities.user import User
from ..value_objects.delivery import DeliveryResult
from ..value_objects.notification import NotificationType, RenderedMessage


class NotificationChannelService:
    """Service for determining available notification channels."""

    def get_available_channels_for_user(self, user: User) -> set[NotificationType]:
        """Get available notification channels for a user."""
        channels = set()

        if user.has_email():
            channels.add(NotificationType.EMAIL)
        if user.has_phone():
            channels.add(NotificationType.SMS)
        if user.has_telegram():
            channels.add(NotificationType.TELEGRAM)

        return channels

    def get_preferred_channels_for_user(self, user: User) -> list[NotificationType]:
        """Get preferred notification channels for a user in priority order."""
        available_channels = self.get_available_channels_for_user(user)
        user_preferences = user.preferences

        # Default priority order
        default_order = [NotificationType.EMAIL, NotificationType.TELEGRAM, NotificationType.SMS]

        # Filter by available channels and user preferences
        preferred_channels = []

        # First, add channels that user explicitly prefers
        for channel_str in user_preferences:
            try:
                channel = NotificationType(channel_str)
                if channel in available_channels and channel not in preferred_channels:
                    preferred_channels.append(channel)
            except ValueError:
                continue  # Invalid channel in preferences

        # Then, add remaining available channels in default order
        for channel in default_order:
            if channel in available_channels and channel not in preferred_channels:
                preferred_channels.append(channel)

        return preferred_channels


class NotificationProviderInterface(ABC):
    """Interface for notification providers."""

    @abstractmethod
    async def send(self, user: User, message: RenderedMessage) -> DeliveryResult:
        """Send notification to user."""
        pass

    @abstractmethod
    def can_handle_user(self, user: User) -> bool:
        """Check if provider can handle this user."""
        pass

    @abstractmethod
    def get_channel_type(self) -> NotificationType:
        """Get the channel type this provider handles."""
        pass

    @abstractmethod
    async def validate_configuration(self) -> bool:
        """Validate provider configuration."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name."""
        pass


class NotificationDeliveryService:
    """Service for orchestrating notification delivery."""

    def __init__(self, channel_service: NotificationChannelService) -> None:
        self._channel_service = channel_service
        self._providers: list[NotificationProviderInterface] = []

    def register_provider(self, provider: NotificationProviderInterface) -> None:
        """Register a notification provider."""
        self._providers.append(provider)

    def get_providers_for_user(self, user: User) -> list[NotificationProviderInterface]:
        """Get available providers for a user."""
        available_channels = self._channel_service.get_available_channels_for_user(user)

        providers = []
        for provider in self._providers:
            if (provider.get_channel_type() in available_channels and
                provider.can_handle_user(user)):
                providers.append(provider)

        return providers

    def get_ordered_providers_for_user(self, user: User) -> list[NotificationProviderInterface]:
        """Get providers for user ordered by preference."""
        preferred_channels = self._channel_service.get_preferred_channels_for_user(user)
        available_providers = self.get_providers_for_user(user)

        ordered_providers = []

        # Order providers by channel preference
        for channel in preferred_channels:
            for provider in available_providers:
                if (provider.get_channel_type() == channel and
                    provider not in ordered_providers):
                    ordered_providers.append(provider)

        return ordered_providers
