"""
Модели данных для системы уведомлений.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


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
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None


@dataclass
class NotificationMessage:
    """Модель сообщения уведомления."""
    subject: str
    content: str
    template_data: Optional[Dict[str, Any]] = None
    
    def render(self) -> Dict[str, str]:
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
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None