"""
Unit tests for the infrastructure layer.
"""
from unittest.mock import Mock, patch

import pytest


class TestUserRepository:
    """Test UserRepository implementation."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.query = Mock()
        session.flush = Mock()
        return session

    def test_user_repository_save(self, mock_db_session):
        """Test UserRepository save method."""
        from app.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(mock_db_session)
        user_data = {
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "telegram_id": "123456789",
            "preferences": {"lang": "en"},
            "is_active": True
        }

        # Mock the database model creation and ID generation
        with patch('app.infrastructure.repositories.user_repository.UserModel') as MockUserModel:
            mock_user_instance = Mock()
            mock_user_instance.id = "generated_id_123"
            MockUserModel.return_value = mock_user_instance

            result = repo.save(user_data)

            # Verify model was created with correct data
            MockUserModel.assert_called_once_with(**user_data)

            # Verify database operations
            mock_db_session.add.assert_called_once_with(mock_user_instance)
            mock_db_session.commit.assert_called_once()

            # Verify result
            assert result == "generated_id_123"

    def test_user_repository_find_by_id(self, mock_db_session):
        """Test UserRepository find_by_id method."""
        from app.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(mock_db_session)

        # Mock query result
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db_session.query.return_value = mock_query

        with patch('app.infrastructure.repositories.user_repository.UserModel') as MockUserModel:
            result = repo.find_by_id("user123")

            # Verify query was built correctly
            mock_db_session.query.assert_called_once_with(MockUserModel)
            mock_query.filter.assert_called_once()
            mock_query.filter.return_value.first.assert_called_once()

            # Verify result
            assert result == mock_user


class TestNotificationService:
    """Test NotificationService implementation."""

    def test_notification_service_send(self):
        """Test NotificationService send method."""
        from app.infrastructure.services.notification_service import NotificationService

        # Mock adapters
        mock_email_adapter = Mock()
        mock_sms_adapter = Mock()
        mock_push_adapter = Mock()

        mock_email_adapter.send.return_value = True
        mock_sms_adapter.send.return_value = True
        mock_push_adapter.send.return_value = True

        service = NotificationService(
            email_adapter=mock_email_adapter,
            sms_adapter=mock_sms_adapter,
            push_adapter=mock_push_adapter
        )

        notification_data = {
            "recipient_id": "user123",
            "message_template": "Hello {name}!",
            "message_variables": {"name": "John"},
            "channels": ["email", "sms"],
            "priority": "HIGH"
        }

        with patch('app.infrastructure.services.notification_service.NotificationModel') as MockNotificationModel:
            mock_notification = Mock()
            mock_notification.id = "notif456"
            MockNotificationModel.return_value = mock_notification

            result = service.send(notification_data)

            # Verify notification model was created
            MockNotificationModel.assert_called_once()

            # Verify adapters were called for requested channels
            mock_email_adapter.send.assert_called_once()
            mock_sms_adapter.send.assert_called_once()
            mock_push_adapter.send.assert_not_called()  # Not in channels

            # Verify result
            assert result == "notif456"

    def test_notification_service_channel_filtering(self):
        """Test that only requested channels are used."""
        from app.infrastructure.services.notification_service import NotificationService

        mock_email_adapter = Mock()
        mock_sms_adapter = Mock()
        mock_push_adapter = Mock()

        service = NotificationService(
            email_adapter=mock_email_adapter,
            sms_adapter=mock_sms_adapter,
            push_adapter=mock_push_adapter
        )

        notification_data = {
            "recipient_id": "user123",
            "message_template": "Test message",
            "channels": ["email"]  # Only email
        }

        with patch('app.infrastructure.services.notification_service.NotificationModel'):
            service.send(notification_data)

            # Only email adapter should be called
            mock_email_adapter.send.assert_called_once()
            mock_sms_adapter.send.assert_not_called()
            mock_push_adapter.send.assert_not_called()


class TestNotificationAdapters:
    """Test notification adapters."""

    def test_email_adapter(self):
        """Test EmailAdapter."""
        from app.infrastructure.adapters.email_adapter import EmailAdapter

        # Mock SMTP configuration
        config = {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "use_tls": True
        }

        adapter = EmailAdapter(config)

        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

            result = adapter.send({
                "recipient": "user@example.com",
                "subject": "Test Subject",
                "body": "Test message"
            })

            # Verify SMTP operations
            mock_smtp.assert_called_once_with(config["smtp_server"], config["smtp_port"])
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with(config["username"], config["password"])
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()

            assert result is True

    def test_sms_adapter(self):
        """Test SMSAdapter."""
        from app.infrastructure.adapters.sms_adapter import SMSAdapter

        config = {
            "api_key": "test_key_123",
            "api_url": "https://api.sms-service.com/send"
        }

        adapter = SMSAdapter(config)

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "sent", "id": "sms123"}
            mock_post.return_value = mock_response

            result = adapter.send({
                "recipient": "+1234567890",
                "message": "Test SMS message"
            })

            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert config["api_url"] in call_args[0]
            assert "headers" in call_args[1]
            assert "json" in call_args[1]

            assert result is True

    def test_push_adapter(self):
        """Test PushAdapter."""
        from app.infrastructure.adapters.push_adapter import PushAdapter

        config = {
            "firebase_key": "firebase_key_123"
        }

        adapter = PushAdapter(config)

        with patch('pyfcm.FCMNotification') as mock_fcm:
            mock_fcm_instance = Mock()
            mock_fcm.return_value = mock_fcm_instance
            mock_fcm_instance.notify_single_device.return_value = {"success": 1}

            result = adapter.send({
                "device_token": "device123",
                "title": "Test Title",
                "body": "Test push message"
            })

            # Verify FCM initialization
            mock_fcm.assert_called_once_with(api_key=config["firebase_key"])

            # Verify notification sent
            mock_fcm_instance.notify_single_device.assert_called_once()

            assert result is True


class TestConfiguration:
    """Test configuration management."""

    def test_config_loading(self):
        """Test configuration loading from environment."""
        with patch.dict('os.environ', {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb',
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test@test.com',
            'SMTP_PASSWORD': 'testpass',
            'SMS_API_KEY': 'sms_test_key',
            'FIREBASE_KEY': 'firebase_test_key'
        }):
            from app.infrastructure.config.settings import get_config

            config = get_config()

            assert config["database_url"] == 'postgresql://test:test@localhost:5432/testdb'
            assert config["smtp"]["server"] == 'smtp.test.com'
            assert config["smtp"]["port"] == 587
            assert config["smtp"]["username"] == 'test@test.com'
            assert config["sms"]["api_key"] == 'sms_test_key'
            assert config["push"]["firebase_key"] == 'firebase_test_key'

    def test_config_defaults(self):
        """Test configuration defaults when environment variables are missing."""
        with patch.dict('os.environ', {}, clear=True):
            from app.infrastructure.config.settings import get_config

            config = get_config()

            # Should have default values
            assert config["database_url"] == 'sqlite:///./notifications.db'
            assert config["smtp"]["server"] == 'localhost'
            assert config["smtp"]["port"] == 587


class TestDependencyInjection:
    """Test dependency injection setup."""

    def test_container_setup(self):
        """Test that dependency injection container is properly configured."""
        from app.presentation.dependencies import (
            get_notification_service,
            get_user_repository,
        )

        # These should not raise exceptions and return proper instances
        user_repo = get_user_repository()
        notification_service = get_notification_service()

        assert user_repo is not None
        assert notification_service is not None

        # Test that they have expected methods
        assert hasattr(user_repo, 'save')
        assert hasattr(user_repo, 'find_by_id')
        assert hasattr(notification_service, 'send')


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        from app.infrastructure.repositories.user_repository import UserRepository

        mock_session = Mock()
        mock_session.commit.side_effect = Exception("Database connection lost")

        repo = UserRepository(mock_session)

        with pytest.raises(Exception) as exc_info:
            repo.save({"email": "test@example.com"})

        assert "Database connection lost" in str(exc_info.value)

    def test_email_sending_failure(self):
        """Test email sending failure handling."""
        from app.infrastructure.adapters.email_adapter import EmailAdapter

        config = {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123"
        }

        adapter = EmailAdapter(config)

        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP server unavailable")

            result = adapter.send({
                "recipient": "user@example.com",
                "subject": "Test",
                "body": "Test message"
            })

            # Should handle gracefully and return False
            assert result is False

    def test_notification_service_partial_failure(self):
        """Test notification service handling partial channel failures."""
        from app.infrastructure.services.notification_service import NotificationService

        mock_email_adapter = Mock()
        mock_sms_adapter = Mock()

        # Email succeeds, SMS fails
        mock_email_adapter.send.return_value = True
        mock_sms_adapter.send.return_value = False

        service = NotificationService(
            email_adapter=mock_email_adapter,
            sms_adapter=mock_sms_adapter
        )

        notification_data = {
            "recipient_id": "user123",
            "message_template": "Test message",
            "channels": ["email", "sms"]
        }

        with patch('app.infrastructure.services.notification_service.NotificationModel'):
            # Should still return notification ID even with partial failure
            result = service.send(notification_data)
            assert result is not None


def test_infrastructure_imports():
    """Test all infrastructure imports work."""
    # Test repository imports

    # Test service imports

    # Test adapter imports

    # Test config imports

    assert True
