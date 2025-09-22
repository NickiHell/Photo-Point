"""
Data Transfer Objects for the application layer.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


# Request DTOs
@dataclass
class CreateUserDTO:
    """DTO for creating a user."""

    email: str | None = None
    phone_number: str | None = None
    telegram_id: str | None = None
    preferences: dict[str, Any] | None = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
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
    message_variables: dict[str, Any] | None = None
    channels: list[str] | None = None
    priority: str = "MEDIUM"
    scheduled_at: datetime | None = None
    retry_policy: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.message_variables is None:
            self.message_variables = {}
        if self.channels is None:
            self.channels = ["email"]
        if self.retry_policy is None:
            self.retry_policy = {}
        if self.metadata is None:
            self.metadata = {}
        if self.retry_policy is None:
            self.retry_policy = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SendBulkNotificationDTO:
    """DTO for sending bulk notifications."""

    recipient_ids: list[str]
    message_template: str
    message_variables: dict[str, Any] | None = None
    channels: list[str] | None = None
    priority: str = "MEDIUM"
    scheduled_at: datetime | None = None
    retry_policy: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.message_variables is None:
            self.message_variables = {}
        if self.channels is None:
            self.channels = ["email"]
        if self.retry_policy is None:
            self.retry_policy = {}
        if self.metadata is None:
            self.metadata = {}
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


# Additional DTOs required by Use Cases
@dataclass
class CreateUserRequest:
    """Request DTO for creating a user."""

    name: str
    email: str | None = None
    phone: str | None = None
    telegram_chat_id: str | None = None
    preferences: list[str] | None = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = []


@dataclass
class UpdateUserRequest:
    """Request DTO for updating a user."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    telegram_chat_id: str | None = None
    is_active: bool | None = None
    preferences: list[str] | None = None


@dataclass
class UserResponse:
    """Response DTO for user information."""

    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    telegram_chat_id: str | None = None
    is_active: bool = True
    preferences: list[str] | None = None
    available_channels: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = []
        if self.available_channels is None:
            self.available_channels = []


@dataclass
class SendNotificationRequest:
    """Request DTO for sending a notification."""

    recipient_id: str
    subject: str
    content: str
    template_data: dict[str, Any] | None = None
    priority: str = "MEDIUM"
    channels: list[str] | None = None
    strategy: str | None = None  # Changed from delivery_strategy
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self):
        if self.template_data is None:
            self.template_data = {}
        if self.channels is None:
            self.channels = []


@dataclass
class BulkNotificationRequest:
    """Request DTO for bulk notification sending."""

    recipient_ids: list[str]
    subject: str
    content: str
    template_data: dict[str, Any] | None = None
    priority: str = "MEDIUM"
    channels: list[str] | None = None
    strategy: str = "FIRST_SUCCESS"  # Changed from delivery_strategy
    max_concurrent: int = 10
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self):
        if self.template_data is None:
            self.template_data = {}
        if self.channels is None:
            self.channels = []


@dataclass
class OperationResponse:
    """Generic operation response DTO."""

    success: bool
    message: str
    data: Any = None
    errors: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class NotificationTaskResponse:
    """Response DTO for queued notification task."""

    task_id: str
    recipient_id: str
    subject: str
    status: str
    queued_at: datetime
    estimated_start: datetime | None = None
    priority: str = "normal"


@dataclass
class BulkNotificationTaskResponse:
    """Response DTO for queued bulk notification task."""

    task_id: str
    valid_recipients_count: int
    invalid_recipients_count: int
    invalid_recipients: list[str]
    subject: str
    status: str
    queued_at: datetime
    max_concurrent: int = 10
    estimated_completion: datetime | None = None


@dataclass
class TaskStatusResponse:
    """Response DTO for Celery task status."""

    task_id: str
    status: str
    message: str
    result: Any = None
    error: str | None = None
    progress: dict[str, Any] | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self):
        if self.progress is None:
            self.progress = {}


@dataclass
class DeliveryAttemptResponse:
    """Response DTO for delivery attempt information."""

    id: str
    delivery_id: str
    provider: str
    channel: str
    status: str
    error_message: str | None = None
    response_data: dict[str, Any] | None = None
    attempted_at: datetime | None = None
    completed_at: datetime | None = None
    duration: float = 0.0
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.response_data is None:
            self.response_data = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DeliveryResponse:
    """Response DTO for delivery information."""

    id: str
    notification_id: str
    user_id: str
    status: str
    strategy: str
    attempts: list[DeliveryAttemptResponse]
    total_attempts: int
    successful_providers: list[str]
    failed_providers: list[str]
    started_at: datetime
    completed_at: datetime | None = None
    total_delivery_time: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    success: bool = False

    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []
        if self.successful_providers is None:
            self.successful_providers = []
        if self.failed_providers is None:
            self.failed_providers = []
