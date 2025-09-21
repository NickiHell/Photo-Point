"""
Data Transfer Objects for the application layer.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


# Request DTOs
@dataclass
class CreateUserDTO:
    """DTO for creating a user."""

    email: str | None = None
    phone_number: str | None = None
    telegram_id: str | None = None
    preferences: dict[str, Any] = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}


@dataclass
class UpdateUserDTO:
    """DTO for updating a user."""

    user_id: str
    email: str | None = None
    phone_number: str | None = None
    telegram_id: str | None = None
    is_active: bool | None = None
    preferences: dict[str, Any] | None = None


@dataclass
class SendNotificationDTO:
    """DTO for sending a notification."""

    recipient_id: str
    message_template: str
    message_variables: dict[str, Any] = None
    channels: list[str] = None
    priority: str = "MEDIUM"
    scheduled_at: datetime | None = None
    retry_policy: dict[str, Any] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.message_variables is None:
            self.message_variables = {}
        if self.channels is None:
            self.channels = ["email"]
        if self.retry_policy is None:
            self.retry_policy = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SendBulkNotificationDTO:
    """DTO for sending bulk notifications."""

    recipient_ids: list[str]
    message_template: str
    message_variables: dict[str, Any] = None
    channels: list[str] = None
    priority: str = "MEDIUM"
    scheduled_at: datetime | None = None
    retry_policy: dict[str, Any] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.message_variables is None:
            self.message_variables = {}
        if self.channels is None:
            self.channels = ["email"]
        if self.retry_policy is None:
            self.retry_policy = {}
        if self.metadata is None:
            self.metadata = {}


# Response DTOs
@dataclass
class UserResponseDTO:
    """Response DTO for user information."""

    id: str
    email: str | None
    phone_number: str | None
    telegram_id: str | None
    is_active: bool
    preferences: dict[str, Any]
    created_at: datetime


@dataclass
class NotificationResponseDTO:
    """Response DTO for notification information."""

    id: str
    recipient_id: str
    message_template: str
    channels: list[str]
    priority: str
    scheduled_at: datetime
    created_at: datetime
    status: str


@dataclass
class BulkNotificationResponseDTO:
    """Response DTO for bulk notification operation."""

    notifications: list[NotificationResponseDTO]
    total_count: int


@dataclass
class DeliveryInfoDTO:
    """DTO for delivery information."""

    delivery_id: str
    channel: str
    provider: str
    status: str
    attempts: int
    created_at: datetime
    completed_at: datetime | None


@dataclass
class NotificationStatusResponseDTO:
    """Response DTO for notification status."""

    notification_id: str
    status: str
    created_at: datetime
    deliveries: list[DeliveryInfoDTO]
