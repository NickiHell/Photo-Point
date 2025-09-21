"""
Email провайдер для отправки уведомлений через SMTP.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from email_validator import EmailNotValidError, validate_email

from src.base import NotificationProvider
from src.exceptions import (
    AuthenticationError,
    ConfigurationError,
)
from src.models import NotificationMessage, NotificationResult, NotificationType, User

logger = logging.getLogger(__name__)


class EmailProvider(NotificationProvider):
    """Email провайдер для отправки уведомлений через SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True
    ):
        """
        Инициализация Email провайдера.

        Args:
            smtp_host: SMTP сервер
            smtp_port: Порт SMTP сервера
            username: Имя пользователя для аутентификации
            password: Пароль для аутентификации
            from_email: Email отправителя
            use_tls: Использовать ли TLS шифрование
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    @classmethod
    def from_env(cls) -> "EmailProvider":
        """Создать провайдера из переменных окружения."""
        smtp_host = os.getenv("EMAIL_SMTP_HOST")
        smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        username = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASSWORD")
        from_email = os.getenv("EMAIL_FROM")

        if not all([smtp_host, username, password, from_email]):
            raise ConfigurationError("Missing required email configuration")

        return cls(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            username=username,
            password=password,
            from_email=from_email
        )

    async def send(self, user: User, message: NotificationMessage) -> NotificationResult:
        """Отправить email уведомление."""
        if not self.is_user_reachable(user):
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message="User email is not available",
                error="No email address provided"
            )

        try:
            # Подготовка сообщения
            rendered_message = message.render()

            # Создание email сообщения
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = user.email
            msg['Subject'] = rendered_message['subject']

            # Добавление текста сообщения
            msg.attach(MIMEText(rendered_message['content'], 'plain', 'utf-8'))

            # Отправка email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {user.email}")
            return NotificationResult(
                success=True,
                provider=NotificationType.EMAIL,
                message=f"Email sent to {user.email}",
                metadata={"recipient": user.email, "subject": rendered_message['subject']}
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message="Authentication failed",
                error=str(e)
            )

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message="SMTP error occurred",
                error=str(e)
            )

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message="Unexpected error occurred",
                error=str(e)
            )

    def is_user_reachable(self, user: User) -> bool:
        """Проверить, можно ли отправить email этому пользователю."""
        if not user.email:
            return False

        try:
            validate_email(user.email)
            return True
        except EmailNotValidError:
            return False

    @property
    def provider_name(self) -> str:
        """Имя провайдера."""
        return "Email"

    async def validate_config(self) -> bool:
        """Проверить корректность конфигурации провайдера."""
        try:
            # Проверка подключения к SMTP серверу
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.username, self.password)

            # Проверка валидности email отправителя
            validate_email(self.from_email)

            return True

        except smtplib.SMTPAuthenticationError:
            raise AuthenticationError("SMTP authentication failed")
        except smtplib.SMTPException as e:
            raise ConfigurationError(f"SMTP configuration error: {e}")
        except EmailNotValidError:
            raise ConfigurationError("Invalid from_email address")
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")
