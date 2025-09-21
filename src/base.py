"""
Базовые интерфейсы для провайдеров уведомлений.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from src.models import User, NotificationMessage, NotificationResult


class NotificationProvider(ABC):
    """Базовый класс для всех провайдеров уведомлений."""
    
    @abstractmethod
    async def send(self, user: User, message: NotificationMessage) -> NotificationResult:
        """Отправить уведомление пользователю."""
        pass
    
    @abstractmethod
    def is_user_reachable(self, user: User) -> bool:
        """Проверить, можно ли отправить уведомление этому пользователю через данный провайдер."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Имя провайдера."""
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Проверить корректность конфигурации провайдера."""
        pass