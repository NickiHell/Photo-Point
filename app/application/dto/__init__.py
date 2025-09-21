"""
Data Transfer Objects for the application layer.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field, EmailStr

from ..domain.value_objects.notification import NotificationPriority
from ..domain.value_objects.delivery import DeliveryStrategy


# Request DTOs (for incoming data)
class CreateUserRequest(BaseModel):
    """Request to create a new user."""
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, regex=r'^\+[1-9]\d{1,14}$')
    telegram_chat_id: Optional[str] = None
    preferences: List[str] = Field(default_factory=list)


class UpdateUserRequest(BaseModel):
    """Request to update user information."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, regex=r'^\+[1-9]\d{1,14}$')
    telegram_chat_id: Optional[str] = None
    preferences: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""
    recipient_id: str
    subject: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=10000)
    template_data: Dict[str, Any] = Field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL
    strategy: DeliveryStrategy = DeliveryStrategy.FIRST_SUCCESS
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class BulkNotificationRequest(BaseModel):
    """Request to send bulk notifications."""
    recipient_ids: List[str] = Field(..., min_items=1)
    subject: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=10000)
    template_data: Dict[str, Any] = Field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL
    strategy: DeliveryStrategy = DeliveryStrategy.FIRST_SUCCESS
    max_concurrent: int = Field(10, ge=1, le=100)


# Response DTOs (for outgoing data)
@dataclass
class UserResponse:
    """Response containing user information."""
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    telegram_chat_id: Optional[str]
    is_active: bool
    preferences: List[str]
    available_channels: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class NotificationResponse:
    """Response containing notification information."""
    id: str
    recipient_id: str
    subject: str
    content: str
    priority: str
    is_cancelled: bool
    scheduled_at: datetime
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class DeliveryAttemptResponse:
    """Response containing delivery attempt information."""
    provider: str
    channel: str
    attempted_at: datetime
    success: bool
    message: str
    error: Optional[str]
    delivery_time: Optional[float]


@dataclass
class DeliveryResponse:
    """Response containing delivery information."""
    id: str
    notification_id: str
    user_id: str
    status: str
    strategy: str
    attempts: List[DeliveryAttemptResponse]
    total_attempts: int
    successful_providers: List[str]
    failed_providers: List[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_delivery_time: Optional[float]
    created_at: datetime
    updated_at: datetime


@dataclass
class ServiceStatusResponse:
    """Response containing service status information."""
    service_status: str
    total_providers: int
    available_providers: int
    providers: List[Dict[str, Any]]
    uptime: float
    statistics: Dict[str, Any]


@dataclass
class OperationResponse:
    """Generic operation response."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: List[str] = None