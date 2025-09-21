"""
Unit tests for domain value objects.
"""

import pytest

from app.domain.value_objects.delivery import DeliveryStatus, RetryPolicy
from app.domain.value_objects.notification import (
    MessageTemplate,
    NotificationPriority,
)
from app.domain.value_objects.user import Email, PhoneNumber, UserId


class TestUserId:
    """Test cases for UserId value object."""

    def test_valid_user_id(self):
        """Test creation of valid UserId."""
        user_id = UserId("user-123")
        assert user_id.value == "user-123"

    def test_invalid_user_id_empty(self):
        """Test that empty UserId raises ValueError."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            UserId("")

    def test_invalid_user_id_none(self):
        """Test that None UserId raises ValueError."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            UserId(None)

    def test_user_id_equality(self):
        """Test UserId equality."""
        user_id1 = UserId("user-123")
        user_id2 = UserId("user-123")
        user_id3 = UserId("user-456")

        assert user_id1 == user_id2
        assert user_id1 != user_id3

    def test_user_id_string_representation(self):
        """Test UserId string representation."""
        user_id = UserId("user-123")
        assert str(user_id) == "user-123"


class TestEmail:
    """Test cases for Email value object."""

    def test_valid_email(self):
        """Test creation of valid Email."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"

    def test_invalid_email_format(self):
        """Test that invalid email format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")

    def test_invalid_email_empty(self):
        """Test that empty email raises ValueError."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            Email("")

    def test_email_normalization(self):
        """Test email normalization to lowercase."""
        email = Email("TEST@EXAMPLE.COM")
        assert email.value == "test@example.com"


class TestPhoneNumber:
    """Test cases for PhoneNumber value object."""

    def test_valid_phone_number(self):
        """Test creation of valid PhoneNumber."""
        phone = PhoneNumber("+1234567890")
        assert phone.value == "+1234567890"

    def test_invalid_phone_number_format(self):
        """Test that invalid phone format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid phone number format"):
            PhoneNumber("123-456")

    def test_invalid_phone_number_empty(self):
        """Test that empty phone number raises ValueError."""
        with pytest.raises(ValueError, match="Phone number cannot be empty"):
            PhoneNumber("")

    def test_phone_number_normalization(self):
        """Test phone number normalization."""
        phone = PhoneNumber("  +1 234 567 890  ")
        assert phone.value == "+1234567890"


class TestMessageTemplate:
    """Test cases for MessageTemplate value object."""

    def test_valid_message_template(self):
        """Test creation of valid MessageTemplate."""
        template = MessageTemplate(
            template="Hello {{name}}!",
            variables={"name": "John"}
        )
        assert template.template == "Hello {{name}}!"
        assert template.variables == {"name": "John"}

    def test_message_template_without_variables(self):
        """Test MessageTemplate without variables."""
        template = MessageTemplate(template="Hello World!")
        assert template.template == "Hello World!"
        assert template.variables == {}

    def test_empty_template_raises_error(self):
        """Test that empty template raises ValueError."""
        with pytest.raises(ValueError, match="Template cannot be empty"):
            MessageTemplate(template="")

    def test_render_template(self):
        """Test template rendering."""
        template = MessageTemplate(
            template="Hello {{name}}, your order {{order_id}} is ready!",
            variables={"name": "John", "order_id": "12345"}
        )
        rendered = template.render()
        assert rendered == "Hello John, your order 12345 is ready!"

    def test_render_template_missing_variable(self):
        """Test template rendering with missing variable."""
        template = MessageTemplate(
            template="Hello {{name}}, your order {{order_id}} is ready!",
            variables={"name": "John"}  # missing order_id
        )
        rendered = template.render()
        # Should keep the placeholder for missing variables
        assert "{{order_id}}" in rendered


class TestNotificationPriority:
    """Test cases for NotificationPriority value object."""

    def test_valid_priority_values(self):
        """Test creation of valid NotificationPriority values."""
        low = NotificationPriority("LOW")
        medium = NotificationPriority("MEDIUM")
        high = NotificationPriority("HIGH")
        urgent = NotificationPriority("URGENT")

        assert low.value == "LOW"
        assert medium.value == "MEDIUM"
        assert high.value == "HIGH"
        assert urgent.value == "URGENT"

    def test_invalid_priority_value(self):
        """Test that invalid priority value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid priority"):
            NotificationPriority("INVALID")

    def test_priority_ordering(self):
        """Test priority ordering."""
        low = NotificationPriority("LOW")
        medium = NotificationPriority("MEDIUM")
        high = NotificationPriority("HIGH")
        urgent = NotificationPriority("URGENT")

        assert low < medium < high < urgent
        assert urgent > high > medium > low


class TestDeliveryStatus:
    """Test cases for DeliveryStatus value object."""

    def test_valid_status_values(self):
        """Test creation of valid DeliveryStatus values."""
        pending = DeliveryStatus("PENDING")
        sent = DeliveryStatus("SENT")
        delivered = DeliveryStatus("DELIVERED")
        failed = DeliveryStatus("FAILED")
        retrying = DeliveryStatus("RETRYING")

        assert pending.value == "PENDING"
        assert sent.value == "SENT"
        assert delivered.value == "DELIVERED"
        assert failed.value == "FAILED"
        assert retrying.value == "RETRYING"

    def test_invalid_status_value(self):
        """Test that invalid status value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid delivery status"):
            DeliveryStatus("INVALID")

    def test_is_final_status(self):
        """Test identification of final status values."""
        delivered = DeliveryStatus("DELIVERED")
        failed = DeliveryStatus("FAILED")
        pending = DeliveryStatus("PENDING")
        retrying = DeliveryStatus("RETRYING")

        assert delivered.is_final()
        assert failed.is_final()
        assert not pending.is_final()
        assert not retrying.is_final()


class TestRetryPolicy:
    """Test cases for RetryPolicy value object."""

    def test_default_retry_policy(self):
        """Test creation of default RetryPolicy."""
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.initial_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.exponential_base == 2.0

    def test_custom_retry_policy(self):
        """Test creation of custom RetryPolicy."""
        policy = RetryPolicy(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=1.5
        )
        assert policy.max_attempts == 5
        assert policy.initial_delay == 2.0
        assert policy.max_delay == 120.0
        assert policy.exponential_base == 1.5

    def test_calculate_delay(self):
        """Test delay calculation."""
        policy = RetryPolicy(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0
        )

        # First retry (attempt 1): 1.0 * (2 ^ 0) = 1.0
        assert policy.calculate_delay(1) == 1.0

        # Second retry (attempt 2): 1.0 * (2 ^ 1) = 2.0
        assert policy.calculate_delay(2) == 2.0

        # Third retry (attempt 3): 1.0 * (2 ^ 2) = 4.0
        assert policy.calculate_delay(3) == 4.0

        # Fourth retry should be capped at max_delay
        assert policy.calculate_delay(4) == 10.0

    def test_should_retry(self):
        """Test retry decision logic."""
        policy = RetryPolicy(max_attempts=3)

        assert policy.should_retry(1)  # First retry
        assert policy.should_retry(2)  # Second retry
        assert policy.should_retry(3)  # Third retry
        assert not policy.should_retry(4)  # Exceeded max attempts
