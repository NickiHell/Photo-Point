"""
Tortoise ORM models for database persistence.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from tortoise import fields
from tortoise.models import Model


class UserModel(Model):
    """User database model."""

    id = fields.CharField(max_length=50, pk=True)
    email = fields.CharField(max_length=255, null=True, unique=True)
    phone_number = fields.CharField(max_length=20, null=True)
    telegram_id = fields.CharField(max_length=20, null=True)
    is_active = fields.BooleanField(default=True)
    preferences = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)

    # Relationships
    notifications: fields.ReverseRelation["NotificationModel"]

    class Meta:
        table = "users"

    def __str__(self) -> str:
        return f"User: {self.id}"


class NotificationModel(Model):
    """Notification database model."""

    id = fields.CharField(max_length=50, pk=True)
    recipient = fields.ForeignKeyField("models.UserModel", related_name="notifications")
    message_template = fields.TextField()
    message_variables = fields.JSONField(default=dict)
    channels = fields.JSONField()  # List of channel names
    priority = fields.CharField(max_length=20)
    scheduled_at = fields.DatetimeField()
    sent_at = fields.DatetimeField(null=True)
    retry_policy = fields.JSONField(default=dict)
    notification_metadata = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)

    # Relationships
    deliveries: fields.ReverseRelation["DeliveryModel"]

    class Meta:
        table = "notifications"

    def __str__(self) -> str:
        return f"Notification: {self.id}"


class DeliveryModel(Model):
    """Delivery database model."""

    id = fields.CharField(max_length=50, pk=True)
    notification = fields.ForeignKeyField(
        "models.NotificationModel", related_name="deliveries"
    )
    channel = fields.CharField(max_length=20)
    provider = fields.CharField(max_length=50)
    status = fields.CharField(max_length=20)
    created_at = fields.DatetimeField(auto_now_add=True)
    completed_at = fields.DatetimeField(null=True)

    # Relationships
    attempts: fields.ReverseRelation["DeliveryAttemptModel"]

    class Meta:
        table = "deliveries"

    def __str__(self) -> str:
        return f"Delivery: {self.id}"


class DeliveryAttemptModel(Model):
    """Delivery attempt database model."""

    id = fields.IntField(pk=True)
    delivery = fields.ForeignKeyField("models.DeliveryModel", related_name="attempts")
    attempt_number = fields.IntField()
    provider = fields.CharField(max_length=50)
    attempted_at = fields.DatetimeField(auto_now_add=True)
    success = fields.BooleanField()
    error_message = fields.TextField(null=True)
    response_data = fields.JSONField(default=dict)

    class Meta:
        table = "delivery_attempts"

    def __str__(self) -> str:
        return f"DeliveryAttempt: {self.id}"
