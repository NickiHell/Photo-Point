"""
Tests for Infrastructure adapters (Email, SMS, Telegram).
Testing Email, SMS and Telegram notification adapters functionality.
"""

import smtplib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import domain objects
from app.domain.entities.user import User
from app.domain.value_objects.notification import (
    RenderedMessage,
)
from app.domain.value_objects.user import (
    Email,
    PhoneNumber,
    TelegramChatId,
    UserId,
    UserName,
)

# Import adapters
from app.infrastructure.adapters.email_adapter import EmailNotificationAdapter
from app.infrastructure.adapters.sms_adapter import SMSNotificationAdapter
from app.infrastructure.adapters.telegram_adapter import TelegramNotificationAdapter


def create_test_email(email_str: str) -> Email:
    """Create email without deliverability check."""
    import email_validator

    result = email_validator.validate_email(email_str, check_deliverability=False)
    email_obj = Email.__new__(Email)
    email_obj._value = result.email
    return email_obj


class TestEmailNotificationAdapter:
    """Test Email notification adapter comprehensively."""

    def setup_method(self):
        """Setup test dependencies."""
        self.adapter = EmailNotificationAdapter(
            smtp_host="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="password123",
            from_email="noreply@test.com",
            use_tls=True,
            timeout=30,
        )

    def test_email_adapter_initialization(self):
        """Test adapter initialization and properties."""
        assert self.adapter.name == "EmailNotificationAdapter"
        assert self.adapter._smtp_host == "smtp.test.com"
        assert self.adapter._smtp_port == 587
        assert self.adapter._username == "test@test.com"
        assert self.adapter._use_tls is True
        assert self.adapter._timeout == 30

    def test_get_channel_type(self):
        """Test channel type returns EMAIL."""
        from app.domain.value_objects.notification import NotificationType

        assert self.adapter.get_channel_type() == NotificationType.EMAIL

    def test_can_handle_user_with_email(self):
        """Test user validation for email capability."""
        user = User(
            user_id=UserId("user-1"),
            name=UserName("Test User"),
            email=create_test_email("test@example.com"),
            is_active=True,
        )

        assert self.adapter.can_handle_user(user) is True

    def test_can_handle_user_without_email(self):
        """Test user validation fails without email."""
        user = User(
            user_id=UserId("user-2"), name=UserName("No Email User"), is_active=True
        )

        assert self.adapter.can_handle_user(user) is False

    def test_can_handle_inactive_user(self):
        """Test inactive users are rejected."""
        user = User(
            user_id=UserId("user-3"),
            name=UserName("Inactive User"),
            email=create_test_email("inactive@example.com"),
            is_active=False,
        )

        assert self.adapter.can_handle_user(user) is False

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_notification_success(self, mock_smtp_class):
        """Test successful email sending."""
        # Setup mock SMTP
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=None)

        # Create test user and message
        user = User(
            user_id=UserId("user-send"),
            name=UserName("Send User"),
            email=create_test_email("send@example.com"),
        )

        message = RenderedMessage(subject="Test Subject", content="Test email content")

        # Send notification using correct method name
        result = await self.adapter.send(user, message)

        # Verify success
        assert result.success is True
        assert result.provider == "EmailNotificationAdapter"
        assert "Email sent successfully" in result.message

        # Verify SMTP calls
        mock_smtp_class.assert_called_once_with("smtp.test.com", 587, timeout=30)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@test.com", "password123")
        mock_smtp.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_notification_smtp_error(self, mock_smtp_class):
        """Test email sending with SMTP error."""
        # Setup mock to raise exception
        mock_smtp_class.side_effect = smtplib.SMTPException("SMTP connection failed")

        user = User(
            user_id=UserId("user-error"),
            name=UserName("Error User"),
            email=create_test_email("error@example.com"),
        )

        message = RenderedMessage(subject="Error Test", content="Error test content")

        # Send notification
        result = await self.adapter.send(user, message)

        # Verify failure
        assert result.success is False
        assert result.provider == "EmailNotificationAdapter"
        assert "SMTP" in result.message or "error" in result.message

    @pytest.mark.asyncio
    async def test_send_notification_no_email(self):
        """Test sending to user without email."""
        user = User(user_id=UserId("user-no-email"), name=UserName("No Email User"))

        message = RenderedMessage(subject="No Email Test", content="Test content")

        result = await self.adapter.send(user, message)

        # Verify failure
        assert result.success is False
        assert "Cannot send email to user" in result.message

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_notification_with_tls_disabled(self, mock_smtp_class):
        """Test email sending without TLS."""
        # Create adapter without TLS
        adapter_no_tls = EmailNotificationAdapter(
            smtp_host="smtp.test.com",
            smtp_port=25,
            username="test@test.com",
            password="password123",
            from_email="noreply@test.com",
            use_tls=False,
        )

        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=None)

        user = User(
            user_id=UserId("tls-user"),
            name=UserName("TLS User"),
            email=create_test_email("tls@example.com"),
        )

        message = RenderedMessage(subject="TLS Test", content="TLS test content")

        result = await adapter_no_tls.send(user, message)

        # Verify TLS was not called
        mock_smtp.starttls.assert_not_called()
        assert result.success is True

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_notification_auth_error(self, mock_smtp_class):
        """Test SMTP authentication error."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=None)

        # Setup auth error
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )

        user = User(
            user_id=UserId("auth-user"),
            name=UserName("Auth User"),
            email=create_test_email("auth@example.com"),
        )

        message = RenderedMessage(subject="Auth Test", content="Auth test content")

        result = await self.adapter.send(user, message)

        # Verify failure
        assert result.success is False
        assert (
            "authentication" in result.message.lower()
            or "error" in result.message.lower()
        )


class TestSMSNotificationAdapter:
    """Test SMS notification adapter comprehensively."""

    def setup_method(self):
        """Setup test dependencies."""
        self.adapter = SMSNotificationAdapter(
            account_sid="test_sid",
            auth_token="test_token",
            from_phone="+1234567890",
            max_message_length=1600,
        )

    def test_sms_adapter_initialization(self):
        """Test adapter initialization."""
        assert self.adapter.name == "SMSNotificationAdapter"
        assert self.adapter._account_sid == "test_sid"
        assert self.adapter._auth_token == "test_token"
        assert self.adapter._from_phone == "+1234567890"
        assert self.adapter._max_message_length == 1600

    def test_get_channel_type(self):
        """Test channel type returns SMS."""
        from app.domain.value_objects.notification import NotificationType

        assert self.adapter.get_channel_type() == NotificationType.SMS

    def test_can_handle_user_with_phone(self):
        """Test user validation for SMS capability."""
        user = User(
            user_id=UserId("sms-user-1"),
            name=UserName("SMS User"),
            phone=PhoneNumber("+1234567890"),
            is_active=True,
        )

        assert self.adapter.can_handle_user(user) is True

    def test_can_handle_user_without_phone(self):
        """Test user validation fails without phone."""
        user = User(
            user_id=UserId("sms-user-2"), name=UserName("No Phone User"), is_active=True
        )

        assert self.adapter.can_handle_user(user) is False

    def test_can_handle_inactive_user(self):
        """Test inactive users are rejected."""
        user = User(
            user_id=UserId("sms-user-3"),
            name=UserName("Inactive SMS User"),
            phone=PhoneNumber("+1234567890"),
            is_active=False,
        )

        assert self.adapter.can_handle_user(user) is False

    @pytest.mark.asyncio
    @patch("app.infrastructure.adapters.sms_adapter.SMSNotificationAdapter._get_client")
    async def test_send_notification_success(self, mock_get_client):
        """Test successful SMS sending."""
        # Setup mock Twilio client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_message = MagicMock()
        mock_message.sid = "test_message_sid"
        mock_message.status = "queued"
        mock_client.messages.create.return_value = mock_message

        user = User(
            user_id=UserId("sms-send-user"),
            name=UserName("SMS Send User"),
            phone=PhoneNumber("+9876543210"),
        )

        message = RenderedMessage(subject="SMS Subject", content="SMS test content")

        # Send notification
        result = await self.adapter.send(user, message)

        # Verify success
        assert result.success is True
        assert result.provider == "SMSNotificationAdapter"
        assert "SMS sent successfully" in result.message

        # Verify Twilio calls
        mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_no_phone(self):
        """Test sending to user without phone."""
        user = User(user_id=UserId("no-phone-user"), name=UserName("No Phone User"))

        message = RenderedMessage(subject="No Phone", content="Test content")

        result = await self.adapter.send(user, message)

        # Verify failure
        assert result.success is False
        assert "Cannot send SMS to user" in result.message

    def test_normalize_phone_number(self):
        """Test phone number normalization."""
        # Access private method for testing
        result1 = self.adapter._normalize_phone_number("+1234567890")
        assert result1 == "+1234567890"

        result2 = self.adapter._normalize_phone_number("81234567890")
        assert result2 == "+71234567890"  # Russian number conversion

        result3 = self.adapter._normalize_phone_number("71234567890")
        assert result3 == "+71234567890"

    @pytest.mark.asyncio
    @patch("app.infrastructure.adapters.sms_adapter.SMSNotificationAdapter._get_client")
    async def test_send_long_message_truncation(self, mock_get_client):
        """Test long message truncation."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_message = MagicMock()
        mock_message.sid = "truncate_sid"
        mock_message.status = "queued"
        mock_client.messages.create.return_value = mock_message

        user = User(
            user_id=UserId("long-msg-user"),
            name=UserName("Long Message User"),
            phone=PhoneNumber("+1111111111"),
        )

        # Create message longer than max length
        long_content = "A" * 2000  # Longer than 1600 limit
        message = RenderedMessage(subject="Long Message", content=long_content)

        result = await self.adapter.send(user, message)

        # Verify success and truncation
        assert result.success is True

        # Check that create was called with truncated message
        call_args = mock_client.messages.create.call_args
        sent_body = call_args.kwargs["body"]
        assert len(sent_body) <= 1600


class TestTelegramNotificationAdapter:
    """Test Telegram notification adapter comprehensively."""

    def setup_method(self):
        """Setup test dependencies."""
        self.adapter = TelegramNotificationAdapter(
            bot_token="test_bot_token", timeout=30, max_message_length=4096
        )

    def test_telegram_adapter_initialization(self):
        """Test adapter initialization."""
        assert self.adapter.name == "TelegramNotificationAdapter"
        assert self.adapter._bot_token == "test_bot_token"
        assert self.adapter._timeout == 30
        assert self.adapter._max_message_length == 4096
        assert "test_bot_token" in self.adapter._base_url

    def test_get_channel_type(self):
        """Test channel type returns TELEGRAM."""
        from app.domain.value_objects.notification import NotificationType

        assert self.adapter.get_channel_type() == NotificationType.TELEGRAM

    def test_can_handle_user_with_telegram(self):
        """Test user validation for Telegram capability."""
        user = User(
            user_id=UserId("tg-user-1"),
            name=UserName("Telegram User"),
            telegram_chat_id=TelegramChatId("123456789"),
            is_active=True,
        )

        assert self.adapter.can_handle_user(user) is True

    def test_can_handle_user_without_telegram(self):
        """Test user validation fails without Telegram."""
        user = User(
            user_id=UserId("tg-user-2"),
            name=UserName("No Telegram User"),
            is_active=True,
        )

        assert self.adapter.can_handle_user(user) is False

    def test_can_handle_inactive_user(self):
        """Test inactive users are rejected."""
        user = User(
            user_id=UserId("tg-user-3"),
            name=UserName("Inactive TG User"),
            telegram_chat_id=TelegramChatId("987654321"),
            is_active=False,
        )

        assert self.adapter.can_handle_user(user) is False

    @pytest.mark.asyncio
    @patch(
        "app.infrastructure.adapters.telegram_adapter.TelegramNotificationAdapter._make_request"
    )
    async def test_send_notification_success(self, mock_make_request):
        """Test successful Telegram message sending."""
        # Setup mock response
        mock_make_request.return_value = {"ok": True, "result": {"message_id": 123}}

        user = User(
            user_id=UserId("tg-send-user"),
            name=UserName("TG Send User"),
            telegram_chat_id=TelegramChatId("123456789"),
        )

        message = RenderedMessage(subject="TG Subject", content="Telegram test content")

        # Send notification
        result = await self.adapter.send(user, message)

        # Verify success
        assert result.success is True
        assert result.provider == "TelegramNotificationAdapter"
        assert "message sent successfully" in result.message or "123" in result.message

        # Verify HTTP call
        mock_make_request.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "app.infrastructure.adapters.telegram_adapter.TelegramNotificationAdapter._make_request"
    )
    async def test_send_notification_telegram_error(self, mock_make_request):
        """Test Telegram sending with API error."""
        # Setup mock to raise exception
        mock_make_request.side_effect = Exception("Bad Request: chat not found")

        user = User(
            user_id=UserId("tg-error-user"),
            name=UserName("TG Error User"),
            telegram_chat_id=TelegramChatId("123456789"),  # Use valid numeric ID
        )

        message = RenderedMessage(subject="TG Error", content="Error test")

        result = await self.adapter.send(user, message)

        # Verify failure
        assert result.success is False
        assert "failed" in result.message.lower() or "error" in result.message.lower()

    @pytest.mark.asyncio
    async def test_send_notification_no_telegram(self):
        """Test sending to user without Telegram."""
        user = User(user_id=UserId("no-tg-user"), name=UserName("No Telegram User"))

        message = RenderedMessage(subject="No TG", content="Test content")

        result = await self.adapter.send(user, message)

        # Verify failure
        assert result.success is False
        assert "Cannot send Telegram message to user" in result.message

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_make_request_method(self, mock_post):
        """Test _make_request method directly."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"ok": True, "result": {}})
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock()

        # Call _make_request directly
        result = await self.adapter._make_request(
            "sendMessage", {"chat_id": "123", "text": "test"}
        )

        # Verify result
        assert result["ok"] is True
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "app.infrastructure.adapters.telegram_adapter.TelegramNotificationAdapter._make_request"
    )
    async def test_send_long_message_truncation(self, mock_make_request):
        """Test long message truncation for Telegram."""
        mock_make_request.return_value = {"ok": True, "result": {"message_id": 456}}

        user = User(
            user_id=UserId("tg-long-user"),
            name=UserName("TG Long User"),
            telegram_chat_id=TelegramChatId("123456789"),
        )

        # Create message longer than 4096 limit
        long_content = "B" * 5000
        message = RenderedMessage(subject="Long TG", content=long_content)

        result = await self.adapter.send(user, message)

        # Verify success and truncation
        assert result.success is True

        # Check that make_request was called with truncated message
        call_args = mock_make_request.call_args
        sent_data = call_args[0][1]  # Second argument is the data
        assert len(sent_data["text"]) <= 4096


class TestAdaptersErrorHandling:
    """Test error handling across all adapters."""

    def test_adapters_instantiation(self):
        """Test all adapters can be instantiated."""
        # Test adapter instantiation without errors
        email_adapter = EmailNotificationAdapter(
            smtp_host="test.smtp.com",
            smtp_port=465,
            username="test@example.com",
            password="test_pass",
            from_email="sender@example.com",
            use_tls=False,
            timeout=60,
        )

        sms_adapter = SMSNotificationAdapter(
            account_sid="AC123",
            auth_token="token123",
            from_phone="+15551234567",
            max_message_length=320,
        )

        telegram_adapter = TelegramNotificationAdapter(
            bot_token="bot123:token", timeout=60, max_message_length=2048
        )

        # Test all adapters exist
        assert email_adapter is not None
        assert sms_adapter is not None
        assert telegram_adapter is not None


def test_adapters_coverage_boost():
    """Test adapter helper functions."""
    # Test basic instantiation
    email = EmailNotificationAdapter("host", 587, "user", "pass", "from@test.com")
    sms = SMSNotificationAdapter("sid", "token", "+1234567890")
    telegram = TelegramNotificationAdapter("token")

    assert email.name == "EmailNotificationAdapter"
    assert sms.name == "SMSNotificationAdapter"
    assert telegram.name == "TelegramNotificationAdapter"
