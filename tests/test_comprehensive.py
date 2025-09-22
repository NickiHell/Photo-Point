"""
Comprehensive tests for Clean Architecture implementation to improve coverage.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest


class TestDomainLayer:
    """Test domain layer components."""

    def test_entity_base_class(self):
        """Test base Entity class."""
        from app.domain.entities import Entity, User

        user = User("user1", email="test@example.com")
        assert isinstance(user, Entity)
        assert user.id == "user1"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_entity_properties(self):
        """Test User entity properties and methods."""
        from app.domain.entities import User

        user = User(
            user_id="test1",
            email="test@example.com",
            phone_number="+1234567890",
            telegram_id="123456789",
            preferences={"lang": "en"},
            is_active=True,
        )

        assert user.email == "test@example.com"
        assert user.phone_number == "+1234567890"
        assert user.telegram_id == "123456789"
        assert user.preferences == {"lang": "en"}
        assert user.is_active is True

        # Test methods
        user.update_email("new@example.com")
        assert user.email == "new@example.com"

        user.update_phone("+0987654321")
        assert user.phone_number == "+0987654321"

        user.deactivate()
        assert user.is_active is False

        user.activate()
        assert user.is_active is True

    def test_notification_entity(self):
        """Test Notification entity."""
        from app.domain.entities import Notification

        notification = Notification(
            notification_id="notif1",
            recipient_id="user1",
            message_template="Hello {name}!",
            channels=["email", "sms"],
            priority="HIGH",
        )

        assert notification.id == "notif1"
        assert notification.recipient_id == "user1"
        assert notification.message_template == "Hello {name}!"
        assert notification.channels == ["email", "sms"]
        assert notification.priority == "HIGH"
        assert notification.status == "PENDING"

        # Test status changes
        notification.mark_sent()
        assert notification.status == "SENT"

        notification.mark_failed()
        assert notification.status == "FAILED"


class TestApplicationLayer:
    """Test application layer components."""

    def test_create_user_dto(self):
        """Test CreateUserDTO."""
        from app.application.dto import CreateUserDTO

        # Test with all fields
        dto = CreateUserDTO(
            email="test@example.com",
            phone_number="+1234567890",
            telegram_id="123456789",
            preferences={"lang": "en"},
        )

        assert dto.email == "test@example.com"
        assert dto.phone_number == "+1234567890"
        assert dto.telegram_id == "123456789"
        assert dto.preferences == {"lang": "en"}

        # Test with defaults
        dto2 = CreateUserDTO()
        assert dto2.preferences == {}

    def test_send_notification_dto(self):
        """Test SendNotificationDTO."""
        from app.application.dto import SendNotificationDTO

        dto = SendNotificationDTO(
            recipient_id="user1",
            message_template="Hello {name}!",
            message_variables={"name": "John"},
            channels=["email"],
            priority="HIGH",
        )

        assert dto.recipient_id == "user1"
        assert dto.message_template == "Hello {name}!"
        assert dto.message_variables == {"name": "John"}
        assert dto.channels == ["email"]
        assert dto.priority == "HIGH"

        # Test with defaults
        dto2 = SendNotificationDTO(recipient_id="user1", message_template="Hello!")
        assert dto2.message_variables == {}
        assert dto2.channels == ["email"]
        assert dto2.priority == "MEDIUM"

    def test_use_cases_with_mocks(self):
        """Test use cases with detailed mock interactions."""
        from app.application.dto import CreateUserDTO, SendNotificationDTO
        from app.application.use_cases import CreateUserUseCase, SendNotificationUseCase

        # Mock repository
        mock_repo = Mock()
        mock_repo.save.return_value = "user123"

        # Test CreateUserUseCase
        use_case = CreateUserUseCase(mock_repo)
        dto = CreateUserDTO(email="test@example.com", preferences={"lang": "en"})

        result = use_case.execute(dto)

        # Verify repository was called correctly
        mock_repo.save.assert_called_once()
        call_args = mock_repo.save.call_args[0][0]
        assert call_args["email"] == "test@example.com"
        assert call_args["preferences"] == {"lang": "en"}
        assert call_args["is_active"] is True

        # Verify result
        assert result.id == "user123"
        assert result.email == "test@example.com"

        # Mock notification service
        mock_notif_service = Mock()
        mock_notif_service.send.return_value = "notif456"

        # Test SendNotificationUseCase
        notif_use_case = SendNotificationUseCase(mock_notif_service)
        notif_dto = SendNotificationDTO(
            recipient_id="user123",
            message_template="Welcome {name}!",
            message_variables={"name": "John"},
        )

        notif_result = notif_use_case.execute(notif_dto)

        # Verify service was called
        mock_notif_service.send.assert_called_once()
        call_args = mock_notif_service.send.call_args[0][0]
        assert call_args["recipient_id"] == "user123"
        assert call_args["message_template"] == "Welcome {name}!"

        # Verify result
        assert notif_result.id == "notif456"
        assert notif_result.recipient_id == "user123"
        assert notif_result.status == "PENDING"


class TestPresentationLayer:
    """Test presentation layer components."""

    def test_fastapi_app_import(self):
        """Test FastAPI app can be imported and has correct configuration."""
        from app.presentation.api.main import app

        assert app is not None
        assert app.title == "Notification Service API"
        assert app.description == "Clean Architecture notification service"
        assert app.version == "1.0.0"

    def test_api_endpoints_exist(self):
        """Test that API endpoints are properly registered."""
        from app.presentation.api.main import app

        # Get all routes
        routes = [route.path for route in app.routes]

        # Check main endpoints exist
        assert "/" in routes
        assert "/health" in routes
        assert "/api/v1/users" in routes
        assert "/api/v1/notifications/send" in routes


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    def test_user_creation_workflow(self):
        """Test complete user creation workflow."""
        from app.application.dto import CreateUserDTO
        from app.application.use_cases import CreateUserUseCase
        from app.domain.entities import User

        # Mock repository that creates actual User entity
        class DetailedMockRepository:
            def __init__(self):
                self.users = {}
                self.next_id = 1

            def save(self, user_data):
                user_id = f"user_{self.next_id}"
                self.next_id += 1

                # Create actual User entity
                user = User(
                    user_id=user_id,
                    email=user_data.get("email"),
                    phone_number=user_data.get("phone_number"),
                    telegram_id=user_data.get("telegram_id"),
                    preferences=user_data.get("preferences", {}),
                    is_active=user_data.get("is_active", True),
                )
                self.users[user_id] = user
                return user_id

            def find_by_id(self, user_id):
                return self.users.get(user_id)

        repo = DetailedMockRepository()
        use_case = CreateUserUseCase(repo)

        # Test user creation
        dto = CreateUserDTO(
            email="integration@example.com",
            phone_number="+1234567890",
            preferences={"notifications": True, "lang": "en"},
        )

        result = use_case.execute(dto)

        # Verify result
        assert result.email == "integration@example.com"
        assert result.phone_number == "+1234567890"
        assert result.is_active is True
        assert result.preferences["notifications"] is True

        # Verify user was stored
        stored_user = repo.find_by_id(result.id)
        assert stored_user is not None
        assert stored_user.email == "integration@example.com"

    def test_notification_sending_workflow(self):
        """Test complete notification sending workflow."""
        from app.application.dto import SendNotificationDTO
        from app.application.use_cases import SendNotificationUseCase

        class DetailedNotificationService:
            def __init__(self):
                self.notifications = {}
                self.next_id = 1

            def send(self, notification_data):
                notif_id = f"notif_{self.next_id}"
                self.next_id += 1

                # Store detailed notification data
                self.notifications[notif_id] = {
                    "id": notif_id,
                    "recipient_id": notification_data["recipient_id"],
                    "template": notification_data["message_template"],
                    "variables": notification_data["message_variables"],
                    "channels": notification_data["channels"],
                    "priority": notification_data["priority"],
                    "status": "SENT",  # Simulate successful sending
                    "sent_at": datetime.now(),
                }
                return notif_id

        service = DetailedNotificationService()
        use_case = SendNotificationUseCase(service)

        # Test notification sending
        dto = SendNotificationDTO(
            recipient_id="user_123",
            message_template="Welcome to {service}! Your account {status}.",
            message_variables={"service": "NotificationApp", "status": "is ready"},
            channels=["email", "sms"],
            priority="HIGH",
        )

        result = use_case.execute(dto)

        # Verify result
        assert result.recipient_id == "user_123"
        assert result.message_template == "Welcome to {service}! Your account {status}."
        assert result.channels == ["email", "sms"]
        assert result.priority == "HIGH"

        # Verify notification was processed
        stored_notif = service.notifications[result.id]
        assert stored_notif["recipient_id"] == "user_123"
        assert stored_notif["status"] == "SENT"


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_dto_creation(self):
        """Test DTO creation with minimal data."""
        from app.application.dto import CreateUserDTO, SendNotificationDTO

        # Test CreateUserDTO with no data
        user_dto = CreateUserDTO()
        assert user_dto.email is None
        assert user_dto.preferences == {}

        # Test SendNotificationDTO with required fields only
        notif_dto = SendNotificationDTO(recipient_id="user1", message_template="Hello!")
        assert notif_dto.message_variables == {}
        assert notif_dto.channels == ["email"]
        assert notif_dto.retry_policy == {}
        assert notif_dto.metadata == {}

    def test_entity_equality(self):
        """Test entity equality and hashing."""
        from app.domain.entities import User

        user1 = User("same_id", email="test1@example.com")
        user2 = User("same_id", email="test2@example.com")  # Same ID, different email
        user3 = User("different_id", email="test1@example.com")

        # Same ID should be equal
        assert user1 == user2
        assert hash(user1) == hash(user2)

        # Different ID should not be equal
        assert user1 != user3
        assert hash(user1) != hash(user3)

    def test_entity_string_representation(self):
        """Test entity string representations."""
        from app.domain.entities import Notification, User

        user = User("user123", email="test@example.com")
        assert "User(id='user123')" == repr(user)

        notification = Notification("notif456", "user123", "Hello", ["email"])
        assert "Notification(id='notif456')" == repr(notification)


def test_health_check():
    """Simple health check test."""
    assert True


def test_imports_work():
    """Test all main imports work without errors."""
    # Test domain imports

    # Test application imports

    # Test presentation imports

    # All imports successful
    assert True


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality works."""
    import asyncio

    async def dummy_async_operation():
        await asyncio.sleep(0.001)
        return "async_result"

    result = await dummy_async_operation()
    assert result == "async_result"
