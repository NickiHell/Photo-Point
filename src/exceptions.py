"""
Исключения для системы уведомлений.
"""


class NotificationError(Exception):
    """Базовое исключение для ошибок уведомлений."""

    pass


class ConfigurationError(NotificationError):
    """Ошибка конфигурации провайдера."""

    pass


class SendError(NotificationError):
    """Ошибка отправки уведомления."""

    pass


class UserNotReachableError(NotificationError):
    """Пользователь недоступен для данного типа уведомления."""

    pass


class RateLimitError(SendError):
    """Превышен лимит отправки."""

    pass


class AuthenticationError(ConfigurationError):
    """Ошибка аутентификации провайдера."""

    pass
