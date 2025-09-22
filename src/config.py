"""
Конфигурация системы уведомлений.
"""

import logging
import os

from dotenv import load_dotenv
from notification_service.src.providers.email import EmailProvider

from src.exceptions import ConfigurationError
from src.providers.sms import SMSProvider
from src.providers.telegram import TelegramProvider
from src.service import NotificationService

# Загружаем переменные окружения
load_dotenv()


def setup_logging(level: str = "INFO") -> None:
    """Настройка логирования."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_email_provider() -> EmailProvider | None:
    """Создать Email провайдера из переменных окружения."""
    try:
        return EmailProvider.from_env()
    except ConfigurationError as e:
        logging.warning(f"Email provider not configured: {e}")
        return None


def create_sms_provider() -> SMSProvider | None:
    """Создать SMS провайдера из переменных окружения."""
    try:
        return SMSProvider.from_env()
    except ConfigurationError as e:
        logging.warning(f"SMS provider not configured: {e}")
        return None


def create_telegram_provider() -> TelegramProvider | None:
    """Создать Telegram провайдера из переменных окружения."""
    try:
        return TelegramProvider.from_env()
    except ConfigurationError as e:
        logging.warning(f"Telegram provider not configured: {e}")
        return None


def create_notification_service(
    provider_order: list[str] | None = None,
) -> NotificationService:
    """
    Создать сервис уведомлений с доступными провайдерами.

    Args:
        provider_order: Порядок провайдеров по приоритету.
                       Если не указан, используется ["email", "telegram", "sms"]

    Returns:
        Настроенный сервис уведомлений
    """
    if provider_order is None:
        provider_order = ["email", "telegram", "sms"]

    # Создаем провайдеров
    provider_creators = {
        "email": create_email_provider,
        "sms": create_sms_provider,
        "telegram": create_telegram_provider,
    }

    providers = []
    for provider_name in provider_order:
        if provider_name in provider_creators:
            provider = provider_creators[provider_name]()
            if provider is not None:
                providers.append(provider)
                logging.info(f"Added {provider_name} provider to service")
            else:
                logging.warning(f"Skipping {provider_name} provider - not configured")
        else:
            logging.warning(f"Unknown provider: {provider_name}")

    if not providers:
        raise ConfigurationError(
            "No providers configured. Please check your environment variables."
        )

    logging.info(f"Created notification service with {len(providers)} providers")
    return NotificationService(providers)


class Config:
    """Класс для управления конфигурацией."""

    # Настройки логирования
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Настройки сервиса
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))
    MAX_CONCURRENT_NOTIFICATIONS = int(os.getenv("MAX_CONCURRENT", "10"))

    # Порядок провайдеров (разделен запятыми)
    PROVIDER_ORDER = os.getenv("PROVIDER_ORDER", "email,telegram,sms").split(",")

    # Email настройки
    EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_FROM = os.getenv("EMAIL_FROM")
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"

    # SMS настройки (Twilio)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    # Telegram настройки
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_TIMEOUT = int(os.getenv("TELEGRAM_TIMEOUT", "30"))

    @classmethod
    def validate(cls) -> None:
        """Проверить конфигурацию."""
        issues = []

        # Проверяем Email конфигурацию
        if any(
            [cls.EMAIL_SMTP_HOST, cls.EMAIL_USER, cls.EMAIL_PASSWORD, cls.EMAIL_FROM]
        ):
            if not all(
                [
                    cls.EMAIL_SMTP_HOST,
                    cls.EMAIL_USER,
                    cls.EMAIL_PASSWORD,
                    cls.EMAIL_FROM,
                ]
            ):
                issues.append("Incomplete Email configuration")

        # Проверяем SMS конфигурацию
        if any(
            [cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN, cls.TWILIO_PHONE_NUMBER]
        ):
            if not all(
                [cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN, cls.TWILIO_PHONE_NUMBER]
            ):
                issues.append("Incomplete SMS/Twilio configuration")

        # Проверяем Telegram конфигурацию
        if not cls.TELEGRAM_BOT_TOKEN and "telegram" in cls.PROVIDER_ORDER:
            issues.append("Telegram bot token is missing")

        # Проверяем, что хотя бы один провайдер настроен
        has_email = all(
            [cls.EMAIL_SMTP_HOST, cls.EMAIL_USER, cls.EMAIL_PASSWORD, cls.EMAIL_FROM]
        )
        has_sms = all(
            [cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN, cls.TWILIO_PHONE_NUMBER]
        )
        has_telegram = bool(cls.TELEGRAM_BOT_TOKEN)

        if not any([has_email, has_sms, has_telegram]):
            issues.append("No notification providers are configured")

        if issues:
            raise ConfigurationError("Configuration issues found: " + "; ".join(issues))

        logging.info("Configuration validation passed")

    @classmethod
    def get_summary(cls) -> dict:
        """Получить сводку конфигурации."""
        return {
            "log_level": cls.LOG_LEVEL,
            "max_retries": cls.MAX_RETRIES,
            "retry_delay": cls.RETRY_DELAY,
            "max_concurrent": cls.MAX_CONCURRENT_NOTIFICATIONS,
            "provider_order": cls.PROVIDER_ORDER,
            "email_configured": bool(cls.EMAIL_SMTP_HOST and cls.EMAIL_USER),
            "sms_configured": bool(cls.TWILIO_ACCOUNT_SID and cls.TWILIO_AUTH_TOKEN),
            "telegram_configured": bool(cls.TELEGRAM_BOT_TOKEN),
        }
