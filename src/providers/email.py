"""Email notification provider implementation."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from email_validator import EmailNotValidError, validate_email

from src.base import NotificationProvider
from src.core import logger
from src.exceptions import (
    AuthenticationError,
    ConfigurationError,
)
from src.models import NotificationMessage, NotificationResult, NotificationType, User


class EmailProvider(NotificationProvider):
    """Email provider for sending notifications via SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
    ):
        """
        Initialize Email provider.

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            username: Username for authentication
            password: Password for authentication
            from_email: Sender email address
            use_tls: Whether to use TLS encryption
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    @classmethod
    def from_env(cls) -> "EmailProvider":
        """Create provider from environment variables."""
        smtp_host = os.getenv("EMAIL_SMTP_HOST")
        smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        username = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASSWORD")
        from_email = os.getenv("EMAIL_FROM")

        if not all([smtp_host, username, password, from_email]):
            raise ConfigurationError("Missing required email configuration")

        assert smtp_host is not None
        assert username is not None
        assert password is not None
        assert from_email is not None

        return cls(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            username=username,
            password=password,
            from_email=from_email,
        )

    async def send(
        self, user: User, message: NotificationMessage
    ) -> NotificationResult:
        """Send email notification."""
        if not self.is_user_reachable(user):
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message="User email is not available",
                error="No email address provided",
            )

        try:
            # Prepare message
            rendered_message = message.render()

            # Check that email is not None
            if user.email is None:
                raise ValueError("User email is required for email notifications")

            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = user.email
            msg["Subject"] = rendered_message["subject"]

            # Add message content
            msg.attach(MIMEText(rendered_message["content"], "plain", "utf-8"))

            # Send email
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
                metadata={
                    "recipient": user.email,
                    "subject": rendered_message["subject"],
                },
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message="Authentication failed",
                error=str(e),
            )

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message="SMTP error occurred",
                error=str(e),
            )

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message="Unexpected error occurred",
                error=str(e),
            )

    def is_user_reachable(self, user: User) -> bool:
        """Check if user can receive email notifications."""
        if not user.email:
            return False

        try:
            validate_email(user.email)
            return True
        except EmailNotValidError:
            return False

    @property
    def provider_name(self) -> str:
        """Provider name."""
        return "Email"

    async def validate_config(self) -> bool:
        """Validate provider configuration."""
        try:
            # Check connection to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.username, self.password)

            # Validate sender email address
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
