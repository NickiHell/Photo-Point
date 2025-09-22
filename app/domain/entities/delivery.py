"""
Delivery entity and related domain objects.
"""

from datetime import UTC, datetime

from ..value_objects.delivery import (
    DeliveryError,
    DeliveryId,
    DeliveryResult,
    DeliveryStatus,
    DeliveryStrategy,
    RetryPolicy,
)
from ..value_objects.notification import NotificationType
from . import Entity
from .notification import Notification
from .user import User


class DeliveryAttempt:
    """Value object representing a single delivery attempt."""

    def __init__(
        self,
        provider: str,
        channel: NotificationType,
        attempted_at: datetime,
        result: DeliveryResult,
    ) -> None:
        self.provider = provider
        self.channel = channel
        self.attempted_at = attempted_at
        self.result = result


class Delivery(Entity):
    """Delivery aggregate root managing notification delivery process."""

    def __init__(
        self,
        delivery_id: DeliveryId,
        notification: Notification,
        user: User,
        strategy: DeliveryStrategy = DeliveryStrategy.FIRST_SUCCESS,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        super().__init__(delivery_id)
        self._notification = notification
        self._user = user
        self._strategy = strategy
        self._retry_policy = retry_policy or RetryPolicy()
        self._status = DeliveryStatus.PENDING
        self._attempts: list[DeliveryAttempt] = []
        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None
        self._final_result: DeliveryResult | None = None

    @property
    def notification(self) -> Notification:
        return self._notification

    @property
    def user(self) -> User:
        return self._user

    @property
    def strategy(self) -> DeliveryStrategy:
        return self._strategy

    @property
    def retry_policy(self) -> RetryPolicy:
        return self._retry_policy

    @property
    def status(self) -> DeliveryStatus:
        return self._status

    @property
    def attempts(self) -> list[DeliveryAttempt]:
        return self._attempts.copy()

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def final_result(self) -> DeliveryResult | None:
        return self._final_result

    def start(self) -> None:
        """Start the delivery process."""
        if self._status != DeliveryStatus.PENDING:
            raise ValueError(f"Cannot start delivery in status: {self._status}")

        if not self._user.can_receive_notifications():
            self._fail_with_error("USER_INACTIVE", "User cannot receive notifications")
            return

        if not self._notification.is_ready_to_send():
            self._fail_with_error(
                "NOTIFICATION_NOT_READY", "Notification is not ready to send"
            )
            return

        self._status = (
            DeliveryStatus.SENT
        )  # Changed from SENDING to SENT as we don't have intermediate state
        self._started_at = datetime.now(UTC)
        self._mark_updated()

    def add_attempt(
        self, provider: str, channel: NotificationType, result: DeliveryResult
    ) -> None:
        """Add a delivery attempt."""
        if self._status not in [DeliveryStatus.SENT, DeliveryStatus.RETRYING]:
            raise ValueError(f"Cannot add attempt in status: {self._status}")

        attempt = DeliveryAttempt(
            provider=provider,
            channel=channel,
            attempted_at=datetime.now(UTC),
            result=result,
        )
        self._attempts.append(attempt)

        # Update delivery status based on result and strategy
        if result.success:
            self._complete_successfully(result)
        else:
            self._handle_failed_attempt(result)

        self._mark_updated()

    def retry(self) -> None:
        """Mark delivery for retry."""
        if self._status != DeliveryStatus.FAILED:
            raise ValueError(f"Cannot retry delivery in status: {self._status}")

        if len(self._attempts) >= self._retry_policy.max_retries:
            raise ValueError("Maximum retries exceeded")

        self._status = DeliveryStatus.RETRYING
        self._mark_updated()

    def cancel(self) -> None:
        """Cancel the delivery."""
        if self._status in [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED]:
            raise ValueError(f"Cannot cancel delivery in status: {self._status}")

        self._fail_with_error("CANCELLED", "Delivery was cancelled")

    def _complete_successfully(self, result: DeliveryResult) -> None:
        """Mark delivery as successfully completed."""
        self._status = DeliveryStatus.DELIVERED
        self._completed_at = datetime.now(UTC)
        self._final_result = result

    def _handle_failed_attempt(self, result: DeliveryResult) -> None:
        """Handle a failed delivery attempt."""
        # Check if we should continue trying based on strategy
        if self._strategy == DeliveryStrategy.FAIL_FAST:
            self._fail_with_result(result)
        elif self._should_continue_trying():
            self._status = DeliveryStatus.RETRYING
        else:
            self._fail_with_result(result)

    def _fail_with_result(self, result: DeliveryResult) -> None:
        """Mark delivery as failed with result."""
        self._status = DeliveryStatus.FAILED
        self._completed_at = datetime.now(UTC)
        self._final_result = result

    def _fail_with_error(self, code: str, message: str) -> None:
        """Mark delivery as failed with error."""
        error = DeliveryError(code=code, message=message)
        result = DeliveryResult(
            success=False, provider="system", message=message, error=error
        )
        self._fail_with_result(result)

    def _should_continue_trying(self) -> bool:
        """Check if we should continue trying to deliver."""
        if self._strategy == DeliveryStrategy.TRY_ALL:
            # Continue if there are more channels to try
            attempted_channels = {attempt.channel for attempt in self._attempts}
            available_channels = self._user.get_available_channels()
            return len(attempted_channels) < len(available_channels)

        # For FIRST_SUCCESS, check retry policy
        return len(self._attempts) < self._retry_policy.max_retries

    def get_successful_attempts(self) -> list[DeliveryAttempt]:
        """Get all successful delivery attempts."""
        return [attempt for attempt in self._attempts if attempt.result.success]

    def get_failed_attempts(self) -> list[DeliveryAttempt]:
        """Get all failed delivery attempts."""
        return [attempt for attempt in self._attempts if not attempt.result.success]

    def get_total_delivery_time(self) -> float | None:
        """Get total delivery time in seconds."""
        if self._started_at is None:
            return None

        end_time = self._completed_at or datetime.now(UTC)
        return (end_time - self._started_at).total_seconds()

    def is_completed(self) -> bool:
        """Check if delivery is completed (either successfully or failed)."""
        return self._status in [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED]
