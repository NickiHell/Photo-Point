"""
Notification-related value objects.
"""
from enum import Enum
from typing import Any

from . import ValueObject


class NotificationId(ValueObject):
    """Notification identifier value object."""

    def __init__(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Notification ID cannot be empty")
        self._value = value.strip()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class NotificationType(str, Enum):
    """Types of notification channels."""
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MessageSubject(ValueObject):
    """Message subject value object."""

    def __init__(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Message subject cannot be empty")

        cleaned = value.strip()
        if len(cleaned) > 500:
            raise ValueError("Message subject is too long (max 500 characters)")

        self._value = cleaned

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class MessageContent(ValueObject):
    """Message content value object."""

    def __init__(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Message content cannot be empty")

        cleaned = value.strip()
        if len(cleaned) > 10000:  # Reasonable limit for message content
            raise ValueError("Message content is too long (max 10000 characters)")

        self._value = cleaned

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class MessageTemplate(ValueObject):
    """Message template with data for rendering."""

    def __init__(self, subject: str, content: str, template_data: dict[str, Any] | None = None) -> None:
        self._subject = MessageSubject(subject)
        self._content = MessageContent(content)
        self._template_data = template_data or {}

    @property
    def subject(self) -> MessageSubject:
        return self._subject

    @property
    def content(self) -> MessageContent:
        return self._content

    @property
    def template_data(self) -> dict[str, Any]:
        return self._template_data.copy()

    def render(self) -> "RenderedMessage":
        """Render the template with data."""
        try:
            rendered_subject = self._subject.value.format(**self._template_data)
            rendered_content = self._content.value.format(**self._template_data)
            return RenderedMessage(rendered_subject, rendered_content)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
        except ValueError as e:
            raise ValueError(f"Template rendering error: {e}")


class RenderedMessage(ValueObject):
    """Fully rendered message ready for sending."""

    def __init__(self, subject: str, content: str) -> None:
        self._subject = MessageSubject(subject)
        self._content = MessageContent(content)

    @property
    def subject(self) -> MessageSubject:
        return self._subject

    @property
    def content(self) -> MessageContent:
        return self._content
