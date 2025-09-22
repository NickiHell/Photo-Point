"""
SMS notification adapter using Twilio.
"""

import logging
import re

from ...domain.entities.user import User
from ...domain.services import NotificationProviderInterface
from ...domain.value_objects.delivery import DeliveryError, DeliveryResult
from ...domain.value_objects.notification import NotificationType, RenderedMessage

logger = logging.getLogger(__name__)


class SMSNotificationAdapter(NotificationProviderInterface):
    """SMS notification provider adapter using Twilio."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_phone: str,
        max_message_length: int = 1600,
    ) -> None:
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._from_phone = from_phone
        self._max_message_length = max_message_length

        # Initialize Twilio client lazily to avoid import errors in tests
        self._client = None

    def _get_client(self):
        """Get Twilio client instance."""
        if self._client is None:
            try:
                from twilio.rest import Client

                self._client = Client(self._account_sid, self._auth_token)
            except ImportError:
                logger.error(
                    "Twilio library not installed. Install with: pip install twilio"
                )
                raise
        return self._client

    @property
    def name(self) -> str:
        return "SMSNotificationAdapter"

    def get_channel_type(self) -> NotificationType:
        return NotificationType.SMS

    def can_handle_user(self, user: User) -> bool:
        """Check if user has phone configured."""
        return user.has_phone() and user.is_active

    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number format."""
        # Remove all non-digit characters except +
        cleaned = re.sub(r"[^\d+]", "", phone)

        # Ensure it starts with +
        if not cleaned.startswith("+"):
            if cleaned.startswith("8"):
                cleaned = "+7" + cleaned[1:]  # Russian numbers
            elif cleaned.startswith("7"):
                cleaned = "+" + cleaned
            else:
                cleaned = "+" + cleaned

        return cleaned

    async def send(self, user: User, message: RenderedMessage) -> DeliveryResult:
        """Send SMS notification to user."""
        if not self.can_handle_user(user):
            error = DeliveryError(
                code="USER_NOT_REACHABLE",
                message="User does not have phone configured or is inactive",
            )
            return DeliveryResult(
                success=False,
                provider=self.name,
                message="Cannot send SMS to user",
                error=error,
            )

        try:
            client = self._get_client()

            # Prepare message content (SMS doesn't use subject)
            content = message.content.value
            if len(content) > self._max_message_length:
                content = content[: self._max_message_length - 3] + "..."

            # Normalize phone number
            to_phone = self._normalize_phone_number(user.phone.value if user.phone else "")

            # Send SMS
            message_obj = client.messages.create(
                body=content, from_=self._from_phone, to=to_phone
            )

            logger.info(f"SMS sent successfully to {to_phone}, SID: {message_obj.sid}")

            return DeliveryResult(
                success=True,
                provider=self.name,
                message=f"SMS sent successfully to {to_phone}",
                metadata={
                    "recipient": to_phone,
                    "message_sid": message_obj.sid,
                    "status": message_obj.status,
                },
            )

        except ImportError:
            logger.error("Twilio library not available")
            error = DeliveryError(
                code="DEPENDENCY_ERROR", message="Twilio library not installed"
            )
            return DeliveryResult(
                success=False,
                provider=self.name,
                message="Twilio library not available",
                error=error,
            )

        except Exception as e:
            # Handle Twilio-specific errors
            error_code = "TWILIO_ERROR"
            error_message = "Twilio API error"

            # Try to extract more specific error information
            if hasattr(e, "status"):
                if e.status == 401:
                    error_code = "AUTHENTICATION_ERROR"
                    error_message = "Invalid Twilio credentials"
                elif e.status == 429:
                    error_code = "RATE_LIMIT_ERROR"
                    error_message = "Twilio rate limit exceeded"
                elif hasattr(e, "code") and e.code == 21614:
                    error_code = "INVALID_PHONE_NUMBER"
                    error_message = "Invalid phone number"

            logger.error(f"SMS sending failed: {e}")
            error = DeliveryError(
                code=error_code, message=error_message, details={"twilio_error": str(e)}
            )
            return DeliveryResult(
                success=False, provider=self.name, message=error_message, error=error
            )

    async def validate_configuration(self) -> bool:
        """Validate SMS provider configuration."""
        try:
            client = self._get_client()

            # Try to fetch account information to validate credentials
            account = client.api.accounts(self._account_sid).fetch()

            if account.status != "active":
                logger.error(f"Twilio account status: {account.status}")
                return False

            # Validate from phone number format
            if not self._from_phone.startswith("+"):
                logger.error("From phone number must start with '+'")
                return False

            return True

        except ImportError:
            logger.error("Twilio library not installed")
            return False
        except Exception as e:
            logger.error(f"SMS configuration validation failed: {e}")
            return False
