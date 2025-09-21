"""
Data Transfer Objects for the application layer.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass


# Request DTOs
@dataclass
class CreateUserDTO:
    """DTO for creating a user."""
    email: Optional[str] = None
    phone_number: Optional[str] = None
    telegram_id: Optional[str] = None
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}


@dataclass
class UpdateUserDTO:
    """DTO for updating a user."""
    user_id: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    telegram_id: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


@dataclass
class SendNotificationDTO:
    """DTO for sending a notification."""
    recipient_id: str
    message_template: str
    message_variables: Dict[str, Any] = None
    channels: List[str] = None
    priority: str = "MEDIUM"
    scheduled_at: Optional[datetime] = None
    retry_policy: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
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
    recipient_ids: List[str]
    message_template: str
    message_variables: Dict[str, Any] = None
    channels: List[str] = None
    priority: str = "MEDIUM"
    scheduled_at: Optional[datetime] = None
    retry_policy: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
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
    email: Optional[str]
    phone_number: Optional[str]
    telegram_id: Optional[str]
    is_active: bool
    preferences: Dict[str, Any]
    created_at: datetime


@dataclass
class NotificationResponseDTO:
    """Response DTO for notification information."""
    id: str
    recipient_id: str
    message_template: str
    channels: List[str]
    priority: str
    scheduled_at: datetime
    created_at: datetime
    status: str


@dataclass
class BulkNotificationResponseDTO:
    """Response DTO for bulk notification operation."""
    notifications: List[NotificationResponseDTO]
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
    completed_at: Optional[datetime]


@dataclass 
class NotificationStatusResponseDTO:
    """Response DTO for notification status."""
    notification_id: str
    status: str
    created_at: datetime
    deliveries: List[DeliveryInfoDTO]