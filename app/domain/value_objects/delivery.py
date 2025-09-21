"""
Delivery-related value objects.
"""
from enum import Enum
from typing import Any

from . import ValueObject


class DeliveryId(ValueObject):
    """Delivery identifier value object."""

    def __init__(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Delivery ID cannot be empty")
        self._value = value.strip()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class DeliveryStatus(str, Enum):
    """Status of message delivery."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class DeliveryStrategy(str, Enum):
    """Strategy for message delivery."""
    FIRST_SUCCESS = "first_success"  # Stop after first successful delivery
    TRY_ALL = "try_all"             # Try all available channels
    FAIL_FAST = "fail_fast"         # Stop after first failure


class RetryPolicy(ValueObject):
    """Retry policy configuration."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, exponential_backoff: bool = True) -> None:
        if max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if retry_delay < 0:
            raise ValueError("Retry delay cannot be negative")

        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._exponential_backoff = exponential_backoff

    @property
    def max_retries(self) -> int:
        return self._max_retries

    @property
    def retry_delay(self) -> float:
        return self._retry_delay

    @property
    def exponential_backoff(self) -> bool:
        return self._exponential_backoff

    def get_delay_for_attempt(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        if not self._exponential_backoff:
            return self._retry_delay
        return self._retry_delay * (2 ** (attempt - 1))


class DeliveryError(ValueObject):
    """Delivery error information."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        if not code or not code.strip():
            raise ValueError("Error code cannot be empty")
        if not message or not message.strip():
            raise ValueError("Error message cannot be empty")

        self._code = code.strip()
        self._message = message.strip()
        self._details = details or {}

    @property
    def code(self) -> str:
        return self._code

    @property
    def message(self) -> str:
        return self._message

    @property
    def details(self) -> dict[str, Any]:
        return self._details.copy()


class DeliveryResult(ValueObject):
    """Result of a delivery attempt."""

    def __init__(
        self,
        success: bool,
        provider: str,
        message: str,
        error: DeliveryError | None = None,
        metadata: dict[str, Any] | None = None,
        delivery_time: float | None = None
    ) -> None:
        self._success = success
        self._provider = provider
        self._message = message
        self._error = error
        self._metadata = metadata or {}
        self._delivery_time = delivery_time

    @property
    def success(self) -> bool:
        return self._success

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def message(self) -> str:
        return self._message

    @property
    def error(self) -> DeliveryError | None:
        return self._error

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata.copy()

    @property
    def delivery_time(self) -> float | None:
        return self._delivery_time
