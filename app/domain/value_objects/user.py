"""
User-related value objects.
"""

import os
import re

from email_validator import EmailNotValidError, validate_email

from . import ValueObject


class UserId(ValueObject):
    """User identifier value object."""

    def __init__(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("User ID cannot be empty")
        if len(value) > 100:
            raise ValueError("User ID is too long (max 100 characters)")
        self._value = value.strip()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class Email(ValueObject):
    """Email address value object."""

    def __init__(self, value: str) -> None:
        try:
            # For testing, skip DNS validation if TEST_MODE is set
            check_deliverability = os.getenv("TEST_MODE") != "true"
            validation_result = validate_email(
                value, check_deliverability=check_deliverability
            )
            self._value = validation_result.email
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {value}") from e

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class PhoneNumber(ValueObject):
    """Phone number value object."""

    def __init__(self, value: str) -> None:
        # Basic phone number validation and normalization
        cleaned = re.sub(r"[^\d+]", "", value)

        if not cleaned:
            raise ValueError("Phone number cannot be empty")

        # Must start with + and contain at least 10 digits
        if not cleaned.startswith("+"):
            # Try to add country code for Russian numbers
            if cleaned.startswith("8"):
                cleaned = "+7" + cleaned[1:]
            elif cleaned.startswith("7"):
                cleaned = "+" + cleaned
            else:
                raise ValueError("Phone number must start with country code (+)")

        # Check minimum length
        if len(cleaned) < 11:  # +X and at least 10 digits
            raise ValueError("Phone number is too short")

        if len(cleaned) > 16:  # International standard
            raise ValueError("Phone number is too long")

        self._value = cleaned

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class TelegramChatId(ValueObject):
    """Telegram chat ID value object."""

    def __init__(self, value: str | int) -> None:
        if value is None:
            raise ValueError("Telegram chat ID cannot be empty")

        # Convert to string for uniform handling
        str_value = str(value)

        if not str_value or not str_value.strip():
            raise ValueError("Telegram chat ID cannot be empty")

        # Chat ID should be numeric (can be negative for groups)
        try:
            int_value = int(str_value)
            if int_value == 0:
                raise ValueError("Telegram chat ID cannot be 0")
        except (ValueError, TypeError) as e:
            if "cannot be 0" in str(e):
                raise  # Re-raise the "cannot be 0" error
            raise ValueError("Telegram chat ID must be numeric")

        self._value = str_value.strip()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class UserName(ValueObject):
    """User name value object."""

    def __init__(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("User name cannot be empty")

        cleaned = value.strip()
        if len(cleaned) > 200:
            raise ValueError("User name is too long (max 200 characters)")

        self._value = cleaned

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value
