"""
Comprehensive tests for all Infrastructure Adapters to maximize coverage.
"""
import smtplib
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestEmailNotificationAdapter:
    """Test EmailNotificationAdapter comprehensively."""

    @pytest.fixture
    def email_adapter(self):
        """Create EmailNotificationAdapter instance."""
        from app.infrastructure.adapters.email_adapter import EmailNotificationAdapter

        return EmailNotificationAdapter(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            username="test@gmail.com",
            password="password",
            from_email="noreply@test.com",
            use_tls=True,
            timeout=30
        )

    @pytest.fixture
    def mock_user_with_email(self):
        """Create mock user with email."""
        user = Mock()
        user.has_email.return_value = True
        user.is_active = True
        user.email.value = "user@gmail.com"
        user.name.value = "Test User"
        return user

    @pytest.fixture
    def mock_user_without_email(self):
        """Create mock user without email."""
        user = Mock()
        user.has_email.return_value = False
        user.is_active = True
        return user

    @pytest.fixture
    def rendered_message(self):
        """Create rendered message."""
        message = Mock()
        message.subject = "Test Subject"
        message.content = "Test content"
        return message

    def test_adapter_initialization(self, email_adapter):
        """Test EmailNotificationAdapter initialization."""
        assert email_adapter.name == "EmailNotificationAdapter"
        assert email_adapter._smtp_host == "smtp.gmail.com"
        assert email_adapter._smtp_port == 587
        assert email_adapter._username == "test@gmail.com"
        assert email_adapter._password == "password"
        assert email_adapter._from_email == "noreply@test.com"
        assert email_adapter._use_tls is True
        assert email_adapter._timeout == 30

    def test_get_channel_type(self, email_adapter):
        """Test get_channel_type returns EMAIL."""
        from app.domain.value_objects.notification import NotificationType

        channel_type = email_adapter.get_channel_type()
        assert channel_type == NotificationType.EMAIL

    def test_can_handle_user_with_email(self, email_adapter, mock_user_with_email):
        """Test can_handle_user returns True for user with email."""
        assert email_adapter.can_handle_user(mock_user_with_email) is True

    def test_can_handle_user_without_email(self, email_adapter, mock_user_without_email):
        """Test can_handle_user returns False for user without email."""
        assert email_adapter.can_handle_user(mock_user_without_email) is False

    def test_can_handle_inactive_user(self, email_adapter, mock_user_with_email):
        """Test can_handle_user returns False for inactive user."""
        mock_user_with_email.is_active = False
        assert email_adapter.can_handle_user(mock_user_with_email) is False

    @pytest.mark.asyncio
    async def test_send_success(self, email_adapter, mock_user_with_email, rendered_message):
        """Test successful email sending."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_server.send_message.return_value = {}

            result = await email_adapter.send(mock_user_with_email, rendered_message)

            assert result.success is True
            assert result.provider == "EmailNotificationAdapter"
            assert result.message == "Email sent successfully"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_send_user_cannot_handle(self, email_adapter, mock_user_without_email, rendered_message):
        """Test sending to user that cannot be handled."""
        result = await email_adapter.send(mock_user_without_email, rendered_message)

        assert result.success is False
        assert result.provider == "EmailNotificationAdapter"
        assert "User cannot receive email notifications" in result.message
        assert result.error is not None
        assert result.error.code == "USER_NOT_SUITABLE"

    @pytest.mark.asyncio
    async def test_send_smtp_error(self, email_adapter, mock_user_with_email, rendered_message):
        """Test email sending with SMTP error."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = smtplib.SMTPException("SMTP Error")

            result = await email_adapter.send(mock_user_with_email, rendered_message)

            assert result.success is False
            assert result.provider == "EmailNotificationAdapter"
            assert "SMTP Error" in result.message
            assert result.error is not None
            assert result.error.code == "SMTP_ERROR"

    @pytest.mark.asyncio
    async def test_send_timeout_error(self, email_adapter, mock_user_with_email, rendered_message):
        """Test email sending with timeout."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = TimeoutError("Timeout")

            result = await email_adapter.send(mock_user_with_email, rendered_message)

            assert result.success is False
            assert result.provider == "EmailNotificationAdapter"
            assert "timeout" in result.message.lower()
            assert result.error is not None
            assert result.error.code == "TIMEOUT"

    @pytest.mark.asyncio
    async def test_send_with_tls_disabled(self, mock_user_with_email, rendered_message):
        """Test sending with TLS disabled."""
        from app.infrastructure.adapters.email_adapter import EmailNotificationAdapter

        adapter = EmailNotificationAdapter(
            smtp_host="smtp.test.com",
            smtp_port=25,
            username="test",
            password="pass",
            from_email="from@test.com",
            use_tls=False
        )

        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_server.send_message.return_value = {}

            result = await adapter.send(mock_user_with_email, rendered_message)

            assert result.success is True
            # Verify TLS was not called
            mock_server.starttls.assert_not_called()


class TestSMSNotificationAdapter:
    """Test SMSNotificationAdapter comprehensively."""

    @pytest.fixture
    def sms_adapter(self):
        """Create SMSNotificationAdapter instance."""
        from app.infrastructure.adapters.sms_adapter import SMSNotificationAdapter

        return SMSNotificationAdapter(
            api_url="https://api.sms.test",
            api_key="test-key",
            sender_id="TEST",
            timeout=30
        )

    @pytest.fixture
    def mock_user_with_phone(self):
        """Create mock user with phone."""
        user = Mock()
        user.has_phone.return_value = True
        user.is_active = True
        user.phone.value = "+1234567890"
        user.name.value = "Test User"
        return user

    @pytest.fixture
    def mock_user_without_phone(self):
        """Create mock user without phone."""
        user = Mock()
        user.has_phone.return_value = False
        user.is_active = True
        return user

    @pytest.fixture
    def rendered_message(self):
        """Create rendered message for SMS."""
        message = Mock()
        message.content = "Test SMS content"
        return message

    def test_adapter_initialization(self, sms_adapter):
        """Test SMSNotificationAdapter initialization."""
        assert sms_adapter.name == "SMSNotificationAdapter"
        assert sms_adapter._api_url == "https://api.sms.test"
        assert sms_adapter._api_key == "test-key"
        assert sms_adapter._sender_id == "TEST"
        assert sms_adapter._timeout == 30

    def test_get_channel_type(self, sms_adapter):
        """Test get_channel_type returns SMS."""
        from app.domain.value_objects.notification import NotificationType

        channel_type = sms_adapter.get_channel_type()
        assert channel_type == NotificationType.SMS

    def test_can_handle_user_with_phone(self, sms_adapter, mock_user_with_phone):
        """Test can_handle_user returns True for user with phone."""
        assert sms_adapter.can_handle_user(mock_user_with_phone) is True

    def test_can_handle_user_without_phone(self, sms_adapter, mock_user_without_phone):
        """Test can_handle_user returns False for user without phone."""
        assert sms_adapter.can_handle_user(mock_user_without_phone) is False

    def test_can_handle_inactive_user(self, sms_adapter, mock_user_with_phone):
        """Test can_handle_user returns False for inactive user."""
        mock_user_with_phone.is_active = False
        assert sms_adapter.can_handle_user(mock_user_with_phone) is False

    @pytest.mark.asyncio
    async def test_send_success(self, sms_adapter, mock_user_with_phone, rendered_message):
        """Test successful SMS sending."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"message_id": "sms-123", "status": "sent"}
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await sms_adapter.send(mock_user_with_phone, rendered_message)

            assert result.success is True
            assert result.provider == "SMSNotificationAdapter"
            assert result.message == "SMS sent successfully"
            assert result.metadata["message_id"] == "sms-123"

    @pytest.mark.asyncio
    async def test_send_user_cannot_handle(self, sms_adapter, mock_user_without_phone, rendered_message):
        """Test sending to user that cannot be handled."""
        result = await sms_adapter.send(mock_user_without_phone, rendered_message)

        assert result.success is False
        assert result.provider == "SMSNotificationAdapter"
        assert "User cannot receive SMS notifications" in result.message
        assert result.error is not None
        assert result.error.code == "USER_NOT_SUITABLE"

    @pytest.mark.asyncio
    async def test_send_api_error(self, sms_adapter, mock_user_with_phone, rendered_message):
        """Test SMS sending with API error."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text.return_value = "Invalid request"
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await sms_adapter.send(mock_user_with_phone, rendered_message)

            assert result.success is False
            assert result.provider == "SMSNotificationAdapter"
            assert "SMS API error" in result.message
            assert result.error is not None
            assert result.error.code == "API_ERROR"

    @pytest.mark.asyncio
    async def test_send_timeout_error(self, sms_adapter, mock_user_with_phone, rendered_message):
        """Test SMS sending with timeout."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = TimeoutError("Timeout")

            result = await sms_adapter.send(mock_user_with_phone, rendered_message)

            assert result.success is False
            assert result.provider == "SMSNotificationAdapter"
            assert "timeout" in result.message.lower()
            assert result.error is not None
            assert result.error.code == "TIMEOUT"


class TestTelegramNotificationAdapter:
    """Test TelegramNotificationAdapter comprehensively."""

    @pytest.fixture
    def telegram_adapter(self):
        """Create TelegramNotificationAdapter instance."""
        from app.infrastructure.adapters.telegram_adapter import (
            TelegramNotificationAdapter,
        )

        return TelegramNotificationAdapter(
            bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            api_base_url="https://api.telegram.org",
            timeout=30
        )

    @pytest.fixture
    def mock_user_with_telegram(self):
        """Create mock user with telegram."""
        user = Mock()
        user.has_telegram.return_value = True
        user.is_active = True
        user.telegram_chat_id.value = 123456789
        user.name.value = "Test User"
        return user

    @pytest.fixture
    def mock_user_without_telegram(self):
        """Create mock user without telegram."""
        user = Mock()
        user.has_telegram.return_value = False
        user.is_active = True
        return user

    @pytest.fixture
    def rendered_message(self):
        """Create rendered message for Telegram."""
        message = Mock()
        message.content = "Test Telegram message"
        return message

    def test_adapter_initialization(self, telegram_adapter):
        """Test TelegramNotificationAdapter initialization."""
        assert telegram_adapter.name == "TelegramNotificationAdapter"
        assert telegram_adapter._bot_token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        assert telegram_adapter._api_base_url == "https://api.telegram.org"
        assert telegram_adapter._timeout == 30

    def test_get_channel_type(self, telegram_adapter):
        """Test get_channel_type returns TELEGRAM."""
        from app.domain.value_objects.notification import NotificationType

        channel_type = telegram_adapter.get_channel_type()
        assert channel_type == NotificationType.TELEGRAM

    def test_can_handle_user_with_telegram(self, telegram_adapter, mock_user_with_telegram):
        """Test can_handle_user returns True for user with telegram."""
        assert telegram_adapter.can_handle_user(mock_user_with_telegram) is True

    def test_can_handle_user_without_telegram(self, telegram_adapter, mock_user_without_telegram):
        """Test can_handle_user returns False for user without telegram."""
        assert telegram_adapter.can_handle_user(mock_user_without_telegram) is False

    def test_can_handle_inactive_user(self, telegram_adapter, mock_user_with_telegram):
        """Test can_handle_user returns False for inactive user."""
        mock_user_with_telegram.is_active = False
        assert telegram_adapter.can_handle_user(mock_user_with_telegram) is False

    @pytest.mark.asyncio
    async def test_send_success(self, telegram_adapter, mock_user_with_telegram, rendered_message):
        """Test successful Telegram message sending."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"message_id": 123, "date": 1640995200}
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await telegram_adapter.send(mock_user_with_telegram, rendered_message)

            assert result.success is True
            assert result.provider == "TelegramNotificationAdapter"
            assert result.message == "Telegram message sent successfully"
            assert result.metadata["message_id"] == 123

    @pytest.mark.asyncio
    async def test_send_user_cannot_handle(self, telegram_adapter, mock_user_without_telegram, rendered_message):
        """Test sending to user that cannot be handled."""
        result = await telegram_adapter.send(mock_user_without_telegram, rendered_message)

        assert result.success is False
        assert result.provider == "TelegramNotificationAdapter"
        assert "User cannot receive Telegram notifications" in result.message
        assert result.error is not None
        assert result.error.code == "USER_NOT_SUITABLE"

    @pytest.mark.asyncio
    async def test_send_api_error(self, telegram_adapter, mock_user_with_telegram, rendered_message):
        """Test Telegram sending with API error."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.json.return_value = {
                "ok": False,
                "error_code": 400,
                "description": "Bad Request: chat not found"
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await telegram_adapter.send(mock_user_with_telegram, rendered_message)

            assert result.success is False
            assert result.provider == "TelegramNotificationAdapter"
            assert "Telegram API error" in result.message
            assert result.error is not None
            assert result.error.code == "API_ERROR"

    @pytest.mark.asyncio
    async def test_send_timeout_error(self, telegram_adapter, mock_user_with_telegram, rendered_message):
        """Test Telegram sending with timeout."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = TimeoutError("Timeout")

            result = await telegram_adapter.send(mock_user_with_telegram, rendered_message)

            assert result.success is False
            assert result.provider == "TelegramNotificationAdapter"
            assert "timeout" in result.message.lower()
            assert result.error is not None
            assert result.error.code == "TIMEOUT"

    @pytest.mark.asyncio
    async def test_send_with_parse_mode(self, telegram_adapter, mock_user_with_telegram, rendered_message):
        """Test sending with custom parse mode."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"message_id": 123}
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await telegram_adapter.send(
                mock_user_with_telegram,
                rendered_message,
                parse_mode="Markdown"
            )

            assert result.success is True
            # Verify parse_mode was passed in request
            call_args = mock_post.call_args
            assert call_args[1]["json"]["parse_mode"] == "Markdown"


class TestAdapterErrorHandling:
    """Test error handling across all adapters."""

    @pytest.mark.asyncio
    async def test_adapter_network_errors(self):
        """Test network error handling in adapters."""
        from app.infrastructure.adapters.sms_adapter import SMSNotificationAdapter

        adapter = SMSNotificationAdapter("https://api.test", "key", "sender")
        user = Mock()
        user.has_phone.return_value = True
        user.is_active = True
        user.phone.value = "+1234567890"

        message = Mock()
        message.content = "Test"

        # Test various network errors
        network_errors = [
            ConnectionError("Connection failed"),
            OSError("Network unreachable"),
            Exception("Unknown network error")
        ]

        for error in network_errors:
            with patch('aiohttp.ClientSession.post', side_effect=error):
                result = await adapter.send(user, message)
                assert result.success is False
                assert result.error is not None
                assert "error" in result.message.lower()


def test_all_adapters_import():
    """Test that all adapters can be imported successfully."""
    from app.infrastructure.adapters.email_adapter import EmailNotificationAdapter
    from app.infrastructure.adapters.sms_adapter import SMSNotificationAdapter
    from app.infrastructure.adapters.telegram_adapter import TelegramNotificationAdapter

    # Basic instantiation test
    email = EmailNotificationAdapter("smtp.test", 587, "user", "pass", "from@test.com")
    sms = SMSNotificationAdapter("https://api.test", "key", "sender")
    telegram = TelegramNotificationAdapter("token", "https://api.telegram.org")

    assert all([email, sms, telegram])
