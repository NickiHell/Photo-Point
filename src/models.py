"""
Модели данных для системы уведомлений.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class NotificationType(str, Enum):
    """Типы уведомлений."""
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"


class NotificationStatus(str, Enum):
    """Статусы уведомлений."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class User:
    """Модель пользователя."""
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    telegram_chat_id: str | None = None


@dataclass
class NotificationMessage:
    """Модель сообщения уведомления."""
    subject: str
    content: str
    template_data: dict[str, Any] | None = None

    def render(self) -> dict[str, str]:
        """Подготавливает сообщение для отправки."""
        if self.template_data:
            subject = self.subject.format(**self.template_data)
            content = self.content.format(**self.template_data)
        else:
            subject = self.subject
            content = self.content

        return {
            "subject": subject,
            "content": content
        }


@dataclass
class NotificationResult:
    """Результат отправки уведомления."""
    success: bool
    provider: NotificationType
    message: str
    error: str | None = None
    metadata: dict[str, Any] | None = None
