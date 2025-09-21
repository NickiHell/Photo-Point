"""Use Cases for the application layer."""

from datetime import datetime
from typing import Protocol

from ..dto import (
    CreateUserDTO,
    NotificationResponseDTO,
    SendNotificationDTO,
    UserResponseDTO,
)
from ..dto import (
    UpdateUserDTO as UpdateUserDTO,  # Explicit re-export
)


class UserRepository(Protocol):
    """Protocol for user repository."""

    def save(self, user_data: dict) -> str:
        """Save user and return ID."""
        pass

    def find_by_id(self, user_id: str) -> dict:
        """Find user by ID."""
        pass

    def update(self, user_id: str, user_data: dict) -> dict:
        """Update user."""
        pass


class NotificationService(Protocol):
    """Protocol for notification service."""

    def send(self, notification_data: dict) -> str:
        """Send notification and return ID."""
        pass


class CreateUserUseCase:
    """Use case for creating users."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, request: CreateUserDTO) -> UserResponseDTO:
        """Create a new user."""
        user_data = {
            "email": request.email,
            "phone_number": request.phone_number,
            "telegram_id": request.telegram_id,
            "is_active": True,
            "preferences": request.preferences,
            "created_at": datetime.now()
        }

        user_id = self.user_repository.save(user_data)
        user_data["id"] = user_id

        return UserResponseDTO(
            id=user_id,
            email=request.email,
            phone_number=request.phone_number,
            telegram_id=request.telegram_id,
            is_active=True,
            preferences=request.preferences,
            created_at=user_data["created_at"]
        )


class SendNotificationUseCase:
    """Use case for sending notifications."""

    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service

    def execute(self, request: SendNotificationDTO) -> NotificationResponseDTO:
        """Send notification."""
        notification_data = {
            "recipient_id": request.recipient_id,
            "message_template": request.message_template,
            "message_variables": request.message_variables,
            "channels": request.channels,
            "priority": request.priority,
            "scheduled_at": request.scheduled_at or datetime.now(),
            "retry_policy": request.retry_policy,
            "metadata": request.metadata,
            "created_at": datetime.now(),
            "status": "PENDING"
        }

        notification_id = self.notification_service.send(notification_data)

        return NotificationResponseDTO(
            id=notification_id,
            recipient_id=request.recipient_id,
            message_template=request.message_template,
            channels=request.channels,
            priority=request.priority,
            scheduled_at=notification_data["scheduled_at"],
            created_at=notification_data["created_at"],
            status="PENDING"
        )
