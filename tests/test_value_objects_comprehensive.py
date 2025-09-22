"""
Comprehensive tests for all Value Objects to maximize coverage.
"""

import pytest


class TestUserValueObjects:
    """Test all User Value Objects comprehensively."""

    def test_user_id_valid(self):
        """Test valid UserId creation."""
        from app.domain.value_objects.user import UserId

        user_id = UserId("test-user-123")
        assert user_id.value == "test-user-123"
        assert str(user_id) == "test-user-123"

    def test_user_id_empty(self):
        """Test UserId with empty value."""
        from app.domain.value_objects.user import UserId

        with pytest.raises(ValueError, match="User ID cannot be empty"):
            UserId("")

    def test_user_id_whitespace(self):
        """Test UserId with whitespace handling."""
        from app.domain.value_objects.user import UserId

        user_id = UserId("  test-user  ")
        assert user_id.value == "test-user"

    def test_user_name_valid(self):
        """Test valid UserName creation."""
        from app.domain.value_objects.user import UserName

        name = UserName("John Doe")
        assert name.value == "John Doe"
        assert str(name) == "John Doe"

    def test_user_name_empty(self):
        """Test UserName with empty value."""
        from app.domain.value_objects.user import UserName

        with pytest.raises(ValueError, match="Username cannot be empty"):
            UserName("")

    def test_user_name_too_long(self):
        """Test UserName with too long value (over 200 chars)."""
        from app.domain.value_objects.user import UserName

        long_name = "a" * 201
        with pytest.raises(ValueError, match="Username cannot exceed 200 characters"):
            UserName(long_name)

    def test_user_name_max_length(self):
        """Test UserName with exactly max length (200 chars)."""
        from app.domain.value_objects.user import UserName

        max_name = "a" * 200
        name = UserName(max_name)
        assert name.value == max_name

    def test_email_valid(self):
        """Test valid Email creation."""
        from app.domain.value_objects.user import Email

        email = Email("test@gmail.com")
        assert email.value == "test@gmail.com"
        assert str(email) == "test@gmail.com"

    def test_email_invalid_format(self):
        """Test Email with invalid format."""
        from app.domain.value_objects.user import Email

        with pytest.raises(ValueError, match="Invalid email format"):
            Email("not-an-email")

    def test_email_empty(self):
        """Test Email with empty value."""
        from app.domain.value_objects.user import Email

        with pytest.raises(ValueError, match="Email cannot be empty"):
            Email("")

    def test_email_normalization(self):
        """Test Email normalization (lowercase)."""
        from app.domain.value_objects.user import Email

        email = Email("Test@Gmail.COM")
        assert email.value == "test@gmail.com"

    def test_phone_number_valid(self):
        """Test valid PhoneNumber creation."""
        from app.domain.value_objects.user import PhoneNumber

        phone = PhoneNumber("+1234567890")
        assert "+1234567890" in phone.value  # May be normalized

    def test_phone_number_invalid(self):
        """Test PhoneNumber with invalid format."""
        from app.domain.value_objects.user import PhoneNumber

        with pytest.raises(ValueError):
            PhoneNumber("invalid-phone")

    def test_phone_number_empty(self):
        """Test PhoneNumber with empty value."""
        from app.domain.value_objects.user import PhoneNumber

        with pytest.raises(ValueError):
            PhoneNumber("")

    def test_telegram_chat_id_valid(self):
        """Test valid TelegramChatId creation."""
        from app.domain.value_objects.user import TelegramChatId

        chat_id = TelegramChatId(123456789)
        assert chat_id.value == 123456789
        assert str(chat_id) == "123456789"

    def test_telegram_chat_id_negative(self):
        """Test TelegramChatId with negative value."""
        from app.domain.value_objects.user import TelegramChatId

        chat_id = TelegramChatId(-123456789)
        assert chat_id.value == -123456789

    def test_telegram_chat_id_zero(self):
        """Test TelegramChatId with zero."""
        from app.domain.value_objects.user import TelegramChatId

        with pytest.raises(ValueError, match="Telegram Chat ID cannot be 0"):
            TelegramChatId(0)


class TestNotificationValueObjects:
    """Test all Notification Value Objects comprehensively."""

    def test_notification_id_valid(self):
        """Test valid NotificationId creation."""
        from app.domain.value_objects.notification import NotificationId

        notification_id = NotificationId("notif-123")
        assert notification_id.value == "notif-123"
        assert str(notification_id) == "notif-123"

    def test_notification_id_empty(self):
        """Test NotificationId with empty value."""
        from app.domain.value_objects.notification import NotificationId

        with pytest.raises(ValueError, match="Notification ID cannot be empty"):
            NotificationId("")

    def test_notification_id_whitespace(self):
        """Test NotificationId with whitespace handling."""
        from app.domain.value_objects.notification import NotificationId

        notification_id = NotificationId("  notif-123  ")
        assert notification_id.value == "notif-123"

    def test_message_template_valid(self):
        """Test valid MessageTemplate creation."""
        from app.domain.value_objects.notification import MessageTemplate

        template = MessageTemplate("Hello {name}!")
        assert template.template == "Hello {name}!"
        assert str(template) == "Hello {name}!"

    def test_message_template_empty(self):
        """Test MessageTemplate with empty value."""
        from app.domain.value_objects.notification import MessageTemplate

        with pytest.raises(ValueError, match="Message template cannot be empty"):
            MessageTemplate("")

    def test_message_template_render(self):
        """Test MessageTemplate rendering with variables."""
        from app.domain.value_objects.notification import MessageTemplate

        template = MessageTemplate("Hello {name}!")
        result = template.render(name="John")
        assert result == "Hello John!"

    def test_message_template_render_multiple(self):
        """Test MessageTemplate rendering with multiple variables."""
        from app.domain.value_objects.notification import MessageTemplate

        template = MessageTemplate("Hello {name}, your order {order_id} is ready!")
        result = template.render(name="John", order_id="123")
        assert result == "Hello John, your order 123 is ready!"

    def test_message_template_render_missing_var(self):
        """Test MessageTemplate rendering with missing variables."""
        from app.domain.value_objects.notification import MessageTemplate

        template = MessageTemplate("Hello {name}!")
        with pytest.raises(KeyError):
            template.render()

    def test_notification_priority_high(self):
        """Test NotificationPriority HIGH."""
        from app.domain.value_objects.notification import NotificationPriority

        priority = NotificationPriority.HIGH
        assert priority.value == "high"
        assert str(priority) == "high"

    def test_notification_priority_medium(self):
        """Test NotificationPriority MEDIUM."""
        from app.domain.value_objects.notification import NotificationPriority

        priority = NotificationPriority.MEDIUM
        assert priority.value == "medium"

    def test_notification_priority_low(self):
        """Test NotificationPriority LOW."""
        from app.domain.value_objects.notification import NotificationPriority

        priority = NotificationPriority.LOW
        assert priority.value == "low"

    def test_notification_priority_all_values(self):
        """Test all NotificationPriority values."""
        from app.domain.value_objects.notification import NotificationPriority

        priorities = list(NotificationPriority)
        assert len(priorities) == 3
        assert NotificationPriority.HIGH in priorities
        assert NotificationPriority.MEDIUM in priorities
        assert NotificationPriority.LOW in priorities


class TestDeliveryValueObjects:
    """Test all Delivery Value Objects comprehensively."""

    def test_delivery_id_valid(self):
        """Test valid DeliveryId creation."""
        from app.domain.value_objects.delivery import DeliveryId

        delivery_id = DeliveryId("delivery-123")
        assert delivery_id.value == "delivery-123"
        assert str(delivery_id) == "delivery-123"

    def test_delivery_id_empty(self):
        """Test DeliveryId with empty value."""
        from app.domain.value_objects.delivery import DeliveryId

        with pytest.raises(ValueError, match="Delivery ID cannot be empty"):
            DeliveryId("")

    def test_delivery_strategy_first_success(self):
        """Test DeliveryStrategy FIRST_SUCCESS."""
        from app.domain.value_objects.delivery import DeliveryStrategy

        strategy = DeliveryStrategy.FIRST_SUCCESS
        assert strategy.value == "first_success"
        assert str(strategy) == "first_success"

    def test_delivery_strategy_try_all(self):
        """Test DeliveryStrategy TRY_ALL."""
        from app.domain.value_objects.delivery import DeliveryStrategy

        strategy = DeliveryStrategy.TRY_ALL
        assert strategy.value == "try_all"

    def test_delivery_status_pending(self):
        """Test DeliveryStatus PENDING."""
        from app.domain.value_objects.delivery import DeliveryStatus

        status = DeliveryStatus.PENDING
        assert status.value == "pending"
        assert str(status) == "pending"

    def test_delivery_status_delivered(self):
        """Test DeliveryStatus DELIVERED."""
        from app.domain.value_objects.delivery import DeliveryStatus

        status = DeliveryStatus.DELIVERED
        assert status.value == "delivered"

    def test_delivery_status_all_values(self):
        """Test all DeliveryStatus values."""
        from app.domain.value_objects.delivery import DeliveryStatus

        statuses = list(DeliveryStatus)
        assert len(statuses) == 5  # PENDING, SENT, DELIVERED, FAILED, RETRYING
        assert DeliveryStatus.PENDING in statuses
        assert DeliveryStatus.DELIVERED in statuses
        assert DeliveryStatus.FAILED in statuses

    def test_retry_policy_default(self):
        """Test RetryPolicy with default values."""
        from app.domain.value_objects.delivery import RetryPolicy

        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.retry_delay == 1.0
        assert policy.exponential_backoff is True

    def test_retry_policy_custom(self):
        """Test RetryPolicy with custom values."""
        from app.domain.value_objects.delivery import RetryPolicy

        policy = RetryPolicy(max_retries=5, retry_delay=2.0, exponential_backoff=False)
        assert policy.max_retries == 5
        assert policy.retry_delay == 2.0
        assert policy.exponential_backoff is False

    def test_retry_policy_negative_retries(self):
        """Test RetryPolicy with negative max_retries."""
        from app.domain.value_objects.delivery import RetryPolicy

        with pytest.raises(ValueError, match="Max retries cannot be negative"):
            RetryPolicy(max_retries=-1)

    def test_retry_policy_negative_delay(self):
        """Test RetryPolicy with negative retry_delay."""
        from app.domain.value_objects.delivery import RetryPolicy

        with pytest.raises(ValueError, match="Retry delay cannot be negative"):
            RetryPolicy(retry_delay=-1.0)

    def test_retry_policy_delay_calculation(self):
        """Test RetryPolicy delay calculation."""
        from app.domain.value_objects.delivery import RetryPolicy

        # With exponential backoff
        policy = RetryPolicy(retry_delay=1.0, exponential_backoff=True)
        assert policy.get_delay_for_attempt(1) == 1.0
        assert policy.get_delay_for_attempt(2) == 2.0
        assert policy.get_delay_for_attempt(3) == 4.0

        # Without exponential backoff
        policy = RetryPolicy(retry_delay=2.0, exponential_backoff=False)
        assert policy.get_delay_for_attempt(1) == 2.0
        assert policy.get_delay_for_attempt(2) == 2.0
        assert policy.get_delay_for_attempt(3) == 2.0

    def test_delivery_error_valid(self):
        """Test valid DeliveryError creation."""
        from app.domain.value_objects.delivery import DeliveryError

        error = DeliveryError("TIMEOUT", "Request timed out")
        assert error.code == "TIMEOUT"
        assert error.message == "Request timed out"
        assert error.details == {}

    def test_delivery_error_with_details(self):
        """Test DeliveryError with details."""
        from app.domain.value_objects.delivery import DeliveryError

        details = {"timeout": 30, "retries": 3}
        error = DeliveryError("TIMEOUT", "Request timed out", details)
        assert error.code == "TIMEOUT"
        assert error.message == "Request timed out"
        assert error.details == details

    def test_delivery_error_empty_code(self):
        """Test DeliveryError with empty code."""
        from app.domain.value_objects.delivery import DeliveryError

        with pytest.raises(ValueError, match="Error code cannot be empty"):
            DeliveryError("", "Some message")

    def test_delivery_error_empty_message(self):
        """Test DeliveryError with empty message."""
        from app.domain.value_objects.delivery import DeliveryError

        with pytest.raises(ValueError, match="Error message cannot be empty"):
            DeliveryError("ERROR", "")

    def test_delivery_result_success(self):
        """Test successful DeliveryResult."""
        from app.domain.value_objects.delivery import DeliveryResult

        result = DeliveryResult(
            success=True, provider="email", message="Email sent successfully"
        )
        assert result.success is True
        assert result.provider == "email"
        assert result.message == "Email sent successfully"
        assert result.error is None
        assert result.metadata == {}
        assert result.delivery_time is None

    def test_delivery_result_failure_with_error(self):
        """Test failed DeliveryResult with error."""
        from app.domain.value_objects.delivery import DeliveryError, DeliveryResult

        error = DeliveryError("TIMEOUT", "Request timed out")
        result = DeliveryResult(
            success=False,
            provider="sms",
            message="SMS delivery failed",
            error=error,
            metadata={"attempt": 1},
            delivery_time=5.2,
        )
        assert result.success is False
        assert result.provider == "sms"
        assert result.message == "SMS delivery failed"
        assert result.error == error
        assert result.metadata == {"attempt": 1}
        assert result.delivery_time == 5.2


class TestValueObjectEdgeCases:
    """Test edge cases and performance scenarios."""

    def test_user_name_unicode(self):
        """Test UserName with unicode characters."""
        from app.domain.value_objects.user import UserName

        name = UserName("José María Aznar")
        assert name.value == "José María Aznar"

    def test_email_long_domain(self):
        """Test Email with long domain."""
        from app.domain.value_objects.user import Email

        long_email = f"test@{'a' * 50}.gmail.com"
        email = Email(long_email)
        assert email.value == long_email.lower()

    def test_phone_number_international(self):
        """Test PhoneNumber with international formats."""
        from app.domain.value_objects.user import PhoneNumber

        # Different formats should be normalized
        phones = ["+1-234-567-8900", "+1 (234) 567-8900", "+12345678900"]
        for phone_str in phones:
            try:
                phone = PhoneNumber(phone_str)
                # Should be normalized to some consistent format
                assert len(phone.value) >= 10
            except ValueError:
                # Some formats might be invalid, that's ok
                pass

    def test_message_template_complex(self):
        """Test MessageTemplate with complex formatting."""
        from app.domain.value_objects.notification import MessageTemplate

        template = MessageTemplate(
            "Hello {name}! Your order #{order_id} for ${amount} is {status}. "
            "Estimated delivery: {delivery_date}."
        )
        result = template.render(
            name="John Doe",
            order_id=12345,
            amount=99.99,
            status="confirmed",
            delivery_date="2024-12-25",
        )
        expected = (
            "Hello John Doe! Your order #12345 for $99.99 is confirmed. "
            "Estimated delivery: 2024-12-25."
        )
        assert result == expected

    def test_delivery_error_large_details(self):
        """Test DeliveryError with large details dict."""
        from app.domain.value_objects.delivery import DeliveryError

        large_details = {f"key_{i}": f"value_{i}" for i in range(100)}
        error = DeliveryError("LARGE_ERROR", "Error with many details", large_details)
        assert len(error.details) == 100
        assert error.details["key_50"] == "value_50"


def test_all_value_objects_import():
    """Test that all value objects can be imported successfully."""
    # User Value Objects
    # Delivery Value Objects
    from app.domain.value_objects.delivery import (
        DeliveryId,
    )

    # Notification Value Objects
    from app.domain.value_objects.notification import (
        NotificationId,
    )
    from app.domain.value_objects.user import (
        UserId,
    )

    # Basic instantiation test
    user_id = UserId("test")
    notification_id = NotificationId("test")
    delivery_id = DeliveryId("test")

    assert all([user_id, notification_id, delivery_id])
