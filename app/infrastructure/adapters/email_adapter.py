"""
Email notification adapter.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ...domain.entities.user import User
from ...domain.services import NotificationProviderInterface
from ...domain.value_objects.delivery import DeliveryError, DeliveryResult
from ...domain.value_objects.notification import NotificationType, RenderedMessage

logger = logging.getLogger(__name__)


class EmailNotificationAdapter(NotificationProviderInterface):
    """Email notification provider adapter."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
        timeout: int = 30,
    ) -> None:
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._use_tls = use_tls
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "EmailNotificationAdapter"

    def get_channel_type(self) -> NotificationType:
        return NotificationType.EMAIL

    def can_handle_user(self, user: User) -> bool:
        """Check if user has email configured."""
        return user.has_email() and user.is_active

    async def send(self, user: User, message: RenderedMessage) -> DeliveryResult:
        """Send email notification to user."""
        if not self.can_handle_user(user):
            error = DeliveryError(
                code="USER_NOT_REACHABLE",
                message="User does not have email configured or is inactive",
            )
            return DeliveryResult(
                success=False,
                provider=self.name,
                message="Cannot send email to user",
                error=error,
            )

        try:
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self._from_email
            msg["To"] = user.email.value if user.email else ""
            msg["Subject"] = message.subject.value

            # Add body
            msg.attach(MIMEText(message.content.value, "plain", "utf-8"))

            # Send email
            with smtplib.SMTP(
                self._smtp_host, self._smtp_port, timeout=self._timeout
            ) as server:
                if self._use_tls:
                    server.starttls()

                server.login(self._username, self._password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {user.email.value if user.email else 'unknown'}")

            return DeliveryResult(
                success=True,
                provider=self.name,
                message=f"Email sent successfully to {user.email.value if user.email else 'unknown'}",
                metadata={
                    "to": user.email.value if user.email else "",
                    "recipient": user.email.value if user.email else "",
                    "subject": message.subject.value,
                },
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            error = DeliveryError(
                code="AUTHENTICATION_ERROR",
                message="SMTP authentication failed",
                details={"smtp_error": str(e)},
            )
            return DeliveryResult(
                success=False,
                provider=self.name,
                message="Authentication failed",
                error=error,
            )

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            error = DeliveryError(
                code="SMTP_ERROR",
                message="SMTP operation failed",
                details={"smtp_error": str(e)},
            )
            return DeliveryResult(
                success=False,
                provider=self.name,
                message="SMTP error occurred",
                error=error,
            )

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            error = DeliveryError(
                code="UNEXPECTED_ERROR",
                message="Unexpected error occurred while sending email",
                details={"error": str(e)},
            )
            return DeliveryResult(
                success=False,
                provider=self.name,
                message="Unexpected error occurred",
                error=error,
            )

    async def validate_configuration(self) -> bool:
        """Validate email provider configuration."""
        try:
            with smtplib.SMTP(
                self._smtp_host, self._smtp_port, timeout=self._timeout
            ) as server:
                if self._use_tls:
                    server.starttls()
                server.login(self._username, self._password)
            return True

        except Exception as e:
            logger.error(f"Email configuration validation failed: {e}")
            return False
