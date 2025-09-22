"""
Comprehensive tests for all Use Cases to achieve maximum coverage.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest


@dataclass
class MockUserResponse:
    """Mock user response for testing."""

    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    telegram_chat_id: str | None = None
    is_active: bool = True
    preferences: list[Any] | None = None
    available_channels: list[Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = []
        if self.available_channels is None:
            self.available_channels = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class TestCreateUserUseCase:
    """Test CreateUserUseCase comprehensively."""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        return repo

    @pytest.fixture
    def create_user_use_case(self, mock_user_repository):
        """Create use case with mocked dependencies."""
        from app.application.use_cases.user_management import CreateUserUseCase

        return CreateUserUseCase(mock_user_repository)

    @pytest.fixture
    def create_user_request(self):
        """Sample create user request."""
        from app.application.dto import CreateUserRequest

        return CreateUserRequest(
            name="Test User",
            email="test@gmail.com",  # Use real domain for email validation
            phone="+1234567890",
            telegram_chat_id="123456789",
            preferences=["email_notifications", "sms_notifications"],
        )

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, create_user_use_case, create_user_request, mock_user_repository
    ):
        """Test successful user creation."""
        # Execute
        result = await create_user_use_case.execute(create_user_request)

        # Verify
        assert result.success is True
        assert result.message == "User created successfully"
        assert result.data is not None

        # Verify repository was called
        mock_user_repository.save.assert_called_once()

        # Verify response data
        user_data = result.data
        assert user_data.name == "Test User"
        assert user_data.email == "test@gmail.com"
        assert user_data.phone == "+1234567890"
        assert user_data.telegram_chat_id == "123456789"
        assert user_data.is_active is True
        assert len(user_data.preferences) == 2

    @pytest.mark.asyncio
    async def test_create_user_minimal_data(
        self, create_user_use_case, mock_user_repository
    ):
        """Test user creation with minimal data."""
        from app.application.dto import CreateUserRequest

        request = CreateUserRequest(name="Minimal User")

        result = await create_user_use_case.execute(request)

        assert result.success is True
        assert result.data.name == "Minimal User"
        assert result.data.email is None
        assert result.data.phone is None
        assert result.data.telegram_chat_id is None
        assert len(result.data.preferences) == 0

        mock_user_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(
        self, create_user_use_case, mock_user_repository
    ):
        """Test user creation with invalid email."""
        from app.application.dto import CreateUserRequest

        request = CreateUserRequest(name="Test User", email="invalid-email")

        result = await create_user_use_case.execute(request)

        assert result.success is False
        assert "Invalid input data" in result.message
        assert len(result.errors) > 0

        # Repository should not be called
        mock_user_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_repository_error(
        self, create_user_use_case, create_user_request, mock_user_repository
    ):
        """Test repository error handling."""
        mock_user_repository.save.side_effect = Exception("Database error")

        result = await create_user_use_case.execute(create_user_request)

        assert result.success is False
        assert result.message == "Failed to create user"
        assert "Database error" in result.errors

    @pytest.mark.asyncio
    async def test_create_user_with_all_channels(
        self, create_user_use_case, mock_user_repository
    ):
        """Test user creation with all communication channels."""
        from app.application.dto import CreateUserRequest

        request = CreateUserRequest(
            name="Full Channel User",
            email="full@gmail.com",
            phone="+1987654321",
            telegram_chat_id="987654321",
            preferences=[
                "email_notifications",
                "sms_notifications",
                "push_notifications",
            ],
        )

        result = await create_user_use_case.execute(request)

        assert result.success is True
        assert result.data.email == "full@gmail.com"
        assert result.data.phone == "+1987654321"
        assert result.data.telegram_chat_id == "987654321"
        assert len(result.data.preferences) == 3


class TestGetUserUseCase:
    """Test GetUserUseCase comprehensively."""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def get_user_use_case(self, mock_user_repository):
        """Get user use case with mocked dependencies."""
        from app.application.use_cases.user_management import GetUserUseCase

        return GetUserUseCase(mock_user_repository)

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import (
            Email,
            PhoneNumber,
            TelegramChatId,
            UserId,
            UserName,
        )

        user = User(
            user_id=UserId("test-user-id"),
            name=UserName("Test User"),
            email=Email("test@gmail.com"),
            phone=PhoneNumber("+1234567890"),
            telegram_chat_id=TelegramChatId("123456789"),
            is_active=True,
        )
        user.add_preference("email_notifications")
        return user

    @pytest.mark.asyncio
    async def test_get_user_success(
        self, get_user_use_case, mock_user_repository, sample_user
    ):
        """Test successful user retrieval."""
        mock_user_repository.get_by_id.return_value = sample_user

        result = await get_user_use_case.execute("test-user-id")

        assert result.success is True
        assert result.message == "User retrieved successfully"
        assert result.data.name == "Test User"
        assert result.data.email == "test@gmail.com"

        mock_user_repository.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, get_user_use_case, mock_user_repository):
        """Test user not found scenario."""
        mock_user_repository.get_by_id.return_value = None

        result = await get_user_use_case.execute("nonexistent-id")

        assert result.success is False
        assert result.message == "User not found"
        assert "User with given ID does not exist" in result.errors

    @pytest.mark.asyncio
    async def test_get_user_invalid_id(self, get_user_use_case, mock_user_repository):
        """Test invalid user ID."""
        result = await get_user_use_case.execute("")

        assert result.success is False
        assert result.message == "Invalid user ID"

    @pytest.mark.asyncio
    async def test_get_user_repository_error(
        self, get_user_use_case, mock_user_repository
    ):
        """Test repository error handling."""
        mock_user_repository.get_by_id.side_effect = Exception(
            "Database connection failed"
        )

        result = await get_user_use_case.execute("test-user-id")

        assert result.success is False
        assert result.message == "Failed to retrieve user"
        assert "Database connection failed" in result.errors


class TestUpdateUserUseCase:
    """Test UpdateUserUseCase comprehensively."""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def update_user_use_case(self, mock_user_repository):
        """Update user use case with mocked dependencies."""
        from app.application.use_cases.user_management import UpdateUserUseCase

        return UpdateUserUseCase(mock_user_repository)

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import (
            Email,
            PhoneNumber,
            TelegramChatId,
            UserId,
            UserName,
        )

        user = User(
            user_id=UserId("test-user-id"),
            name=UserName("Original User"),
            email=Email("original@gmail.com"),
            phone=PhoneNumber("+1111111111"),
            telegram_chat_id=TelegramChatId("111111111"),
            is_active=True,
        )
        user.add_preference("original_preference")
        return user

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, update_user_use_case, mock_user_repository, sample_user
    ):
        """Test successful user update."""
        from app.application.dto import UpdateUserRequest

        mock_user_repository.get_by_id.return_value = sample_user

        request = UpdateUserRequest(
            name="Updated User",
            email="updated@gmail.com",
            phone="+2222222222",
            telegram_chat_id="222222222",
            is_active=False,
            preferences=["new_preference1", "new_preference2"],
        )

        result = await update_user_use_case.execute("test-user-id", request)

        assert result.success is True
        assert result.message == "User updated successfully"

        # Verify repository calls
        mock_user_repository.get_by_id.assert_called_once()
        mock_user_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_partial(
        self, update_user_use_case, mock_user_repository, sample_user
    ):
        """Test partial user update."""
        from app.application.dto import UpdateUserRequest

        mock_user_repository.get_by_id.return_value = sample_user

        # Only update name
        request = UpdateUserRequest(name="Partially Updated")

        result = await update_user_use_case.execute("test-user-id", request)

        assert result.success is True
        # Original email should be preserved
        assert (
            "original@gmail.com" in str(result.data.email)
            or result.data.email == "original@gmail.com"
        )

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self, update_user_use_case, mock_user_repository
    ):
        """Test update user not found."""
        from app.application.dto import UpdateUserRequest

        mock_user_repository.get_by_id.return_value = None

        request = UpdateUserRequest(name="Updated User")

        result = await update_user_use_case.execute("nonexistent-id", request)

        assert result.success is False
        assert result.message == "User not found"

    @pytest.mark.asyncio
    async def test_update_user_clear_optional_fields(
        self, update_user_use_case, mock_user_repository, sample_user
    ):
        """Test clearing optional fields."""
        from app.application.dto import UpdateUserRequest

        mock_user_repository.get_by_id.return_value = sample_user

        # Clear optional fields by setting to empty string
        request = UpdateUserRequest(email="", phone="", telegram_chat_id="")

        result = await update_user_use_case.execute("test-user-id", request)

        assert result.success is True


class TestGetAllActiveUsersUseCase:
    """Test GetAllActiveUsersUseCase comprehensively."""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def get_all_active_users_use_case(self, mock_user_repository):
        """Get all active users use case."""
        from app.application.use_cases.user_management import GetAllActiveUsersUseCase

        return GetAllActiveUsersUseCase(mock_user_repository)

    @pytest.fixture
    def sample_users(self):
        """Sample users list."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        users = []
        for i in range(3):
            user = User(
                user_id=UserId(f"user-{i}"),
                name=UserName(f"User {i}"),
                email=Email(f"user{i}@gmail.com"),
                is_active=True,
            )
            users.append(user)
        return users

    @pytest.mark.asyncio
    async def test_get_all_active_users_success(
        self, get_all_active_users_use_case, mock_user_repository, sample_users
    ):
        """Test successful retrieval of active users."""
        mock_user_repository.get_all_active.return_value = sample_users

        result = await get_all_active_users_use_case.execute()

        assert result.success is True
        assert "Retrieved 3 active users" in result.message
        assert len(result.data) == 3

        mock_user_repository.get_all_active.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_active_users_empty(
        self, get_all_active_users_use_case, mock_user_repository
    ):
        """Test retrieval when no active users exist."""
        mock_user_repository.get_all_active.return_value = []

        result = await get_all_active_users_use_case.execute()

        assert result.success is True
        assert "Retrieved 0 active users" in result.message
        assert len(result.data) == 0

    @pytest.mark.asyncio
    async def test_get_all_active_users_repository_error(
        self, get_all_active_users_use_case, mock_user_repository
    ):
        """Test repository error handling."""
        mock_user_repository.get_all_active.side_effect = Exception("Query failed")

        result = await get_all_active_users_use_case.execute()

        assert result.success is False
        assert result.message == "Failed to retrieve users"
        assert "Query failed" in result.errors


class TestSendNotificationUseCase:
    """Test SendNotificationUseCase comprehensively."""

    @pytest.fixture
    def mock_repositories_and_service(self):
        """Mock all dependencies."""
        user_repo = AsyncMock()
        notification_repo = AsyncMock()
        delivery_repo = AsyncMock()
        delivery_service = Mock()

        return {
            "user_repository": user_repo,
            "notification_repository": notification_repo,
            "delivery_repository": delivery_repo,
            "delivery_service": delivery_service,
        }

    @pytest.fixture
    def send_notification_use_case(self, mock_repositories_and_service):
        """Send notification use case with mocked dependencies."""
        from app.application.use_cases.notification_sending import (
            SendNotificationUseCase,
        )

        return SendNotificationUseCase(
            mock_repositories_and_service["user_repository"],
            mock_repositories_and_service["notification_repository"],
            mock_repositories_and_service["delivery_repository"],
            mock_repositories_and_service["delivery_service"],
        )

    @pytest.fixture
    def sample_user(self):
        """Sample user for notification testing."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        user = User(
            user_id=UserId("recipient-user-id"),
            name=UserName("Recipient User"),
            email=Email("recipient@gmail.com"),
            is_active=True,
        )
        # Mock can_receive_notifications method
        user.can_receive_notifications = Mock(return_value=True)
        return user

    @pytest.fixture
    def send_notification_request(self):
        """Sample send notification request."""
        from app.application.dto import SendNotificationRequest

        return SendNotificationRequest(
            recipient_id="recipient-user-id",
            subject="Test Notification",
            content="This is a test notification for {user_name}",
            template_data={"user_name": "Recipient User"},
            priority="HIGH",
        )

    @pytest.mark.asyncio
    async def test_send_notification_success(
        self,
        send_notification_use_case,
        mock_repositories_and_service,
        sample_user,
        send_notification_request,
    ):
        """Test successful notification sending."""
        # Setup mocks
        mock_repositories_and_service[
            "user_repository"
        ].get_by_id.return_value = sample_user
        mock_repositories_and_service[
            "delivery_service"
        ].get_ordered_providers_for_user.return_value = []

        # Mock delivery execution
        with patch.object(
            send_notification_use_case, "_execute_delivery"
        ) as mock_execute_delivery:
            from app.application.dto import DeliveryResponse

            mock_delivery_response = DeliveryResponse(
                id="delivery-id",
                notification_id="notification-id",
                user_id="recipient-user-id",
                status="completed",
                strategy="FIRST_SUCCESS",
                attempts=[],
                total_attempts=0,
                successful_providers=[],
                failed_providers=[],
                started_at=datetime.now(),
                completed_at=datetime.now(),
                total_delivery_time=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            mock_delivery_response.success = True
            mock_execute_delivery.return_value = mock_delivery_response

            result = await send_notification_use_case.execute(send_notification_request)

            assert result.success is True
            assert result.message == "Notification processed successfully"

            # Verify repository calls
            mock_repositories_and_service[
                "user_repository"
            ].get_by_id.assert_called_once()
            mock_repositories_and_service[
                "notification_repository"
            ].save.assert_called_once()
            mock_repositories_and_service[
                "delivery_repository"
            ].save.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_user_not_found(
        self,
        send_notification_use_case,
        mock_repositories_and_service,
        send_notification_request,
    ):
        """Test notification sending to non-existent user."""
        mock_repositories_and_service["user_repository"].get_by_id.return_value = None

        result = await send_notification_use_case.execute(send_notification_request)

        assert result.success is False
        assert result.message == "Recipient not found"
        assert "User with given ID does not exist" in result.errors

    @pytest.mark.asyncio
    async def test_send_notification_user_cannot_receive(
        self,
        send_notification_use_case,
        mock_repositories_and_service,
        sample_user,
        send_notification_request,
    ):
        """Test notification sending to user who cannot receive notifications."""
        sample_user.can_receive_notifications = Mock(return_value=False)
        mock_repositories_and_service[
            "user_repository"
        ].get_by_id.return_value = sample_user

        result = await send_notification_use_case.execute(send_notification_request)

        assert result.success is False
        assert result.message == "User cannot receive notifications"

    @pytest.mark.asyncio
    async def test_send_notification_invalid_recipient_id(
        self, send_notification_use_case, mock_repositories_and_service
    ):
        """Test notification sending with invalid recipient ID."""
        from app.application.dto import SendNotificationRequest

        request = SendNotificationRequest(
            recipient_id="",  # Invalid ID
            subject="Test",
            content="Test",
        )

        result = await send_notification_use_case.execute(request)

        assert result.success is False
        assert result.message == "Invalid input data"


class TestSendBulkNotificationUseCase:
    """Test SendBulkNotificationUseCase comprehensively."""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_send_notification_use_case(self):
        """Mock send notification use case."""
        return AsyncMock()

    @pytest.fixture
    def send_bulk_notification_use_case(
        self, mock_user_repository, mock_send_notification_use_case
    ):
        """Send bulk notification use case."""
        from app.application.use_cases.notification_sending import (
            SendBulkNotificationUseCase,
        )

        return SendBulkNotificationUseCase(
            mock_user_repository, mock_send_notification_use_case
        )

    @pytest.fixture
    def sample_users(self):
        """Sample users for bulk testing."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        users = []
        for i in range(3):
            user = User(
                user_id=UserId(f"bulk-user-{i}"),
                name=UserName(f"Bulk User {i}"),
                email=Email(f"bulk{i}@gmail.com"),
                is_active=True,
            )
            users.append(user)
        return users

    @pytest.fixture
    def bulk_notification_request(self):
        """Sample bulk notification request."""
        from app.application.dto import BulkNotificationRequest

        return BulkNotificationRequest(
            recipient_ids=["bulk-user-0", "bulk-user-1", "bulk-user-2"],
            subject="Bulk Test Notification",
            content="Hello {user_name}, this is a bulk notification!",
            template_data={"source": "bulk_test"},
            priority="MEDIUM",
            max_concurrent=2,
        )

    @pytest.mark.asyncio
    async def test_send_bulk_notification_success(
        self,
        send_bulk_notification_use_case,
        mock_user_repository,
        mock_send_notification_use_case,
        sample_users,
        bulk_notification_request,
    ):
        """Test successful bulk notification sending."""

        # Setup user repository mock
        async def get_user_by_id(user_id):
            for user in sample_users:
                if str(user.id.value) == str(user_id.value):
                    return user
            return None

        mock_user_repository.get_by_id.side_effect = get_user_by_id

        # Setup send notification use case mock
        from app.application.dto import DeliveryResponse, OperationResponse

        successful_response = OperationResponse(
            success=True,
            message="Success",
            data=DeliveryResponse(
                id="delivery-id",
                notification_id="notification-id",
                user_id="user-id",
                status="completed",
                strategy="FIRST_SUCCESS",
                attempts=[],
                total_attempts=1,
                successful_providers=["email"],
                failed_providers=[],
                started_at=datetime.now(),
                completed_at=datetime.now(),
                total_delivery_time=1.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        )
        mock_send_notification_use_case.execute.return_value = successful_response

        result = await send_bulk_notification_use_case.execute(
            bulk_notification_request
        )

        assert result.success is True
        assert "Bulk notification completed" in result.message
        assert result.data["total_users"] == 3
        assert result.data["success_rate"] == 100.0

        # Verify send notification was called for each user
        assert mock_send_notification_use_case.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_send_bulk_notification_no_valid_recipients(
        self,
        send_bulk_notification_use_case,
        mock_user_repository,
        bulk_notification_request,
    ):
        """Test bulk notification with no valid recipients."""
        mock_user_repository.get_by_id.return_value = None

        result = await send_bulk_notification_use_case.execute(
            bulk_notification_request
        )

        assert result.success is False
        assert result.message == "No valid recipients found"

    @pytest.mark.asyncio
    async def test_send_bulk_notification_partial_success(
        self,
        send_bulk_notification_use_case,
        mock_user_repository,
        mock_send_notification_use_case,
        sample_users,
        bulk_notification_request,
    ):
        """Test bulk notification with partial success."""

        # Only first user exists
        async def get_user_by_id(user_id):
            if str(user_id.value) == "bulk-user-0":
                return sample_users[0]
            return None

        mock_user_repository.get_by_id.side_effect = get_user_by_id

        # Mock successful response
        from app.application.dto import DeliveryResponse, OperationResponse

        successful_response = OperationResponse(
            success=True,
            message="Success",
            data=DeliveryResponse(
                id="delivery-id",
                notification_id="notification-id",
                user_id="bulk-user-0",
                status="completed",
                strategy="FIRST_SUCCESS",
                attempts=[],
                total_attempts=1,
                successful_providers=["email"],
                failed_providers=[],
                started_at=datetime.now(),
                completed_at=datetime.now(),
                total_delivery_time=1.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        )
        mock_send_notification_use_case.execute.return_value = successful_response

        result = await send_bulk_notification_use_case.execute(
            bulk_notification_request
        )

        assert result.success is True
        assert result.data["total_users"] == 1  # Only one valid user

        # Only one call should be made
        assert mock_send_notification_use_case.execute.call_count == 1


# Additional edge case tests
class TestUseCaseEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_use_case_with_none_inputs(self):
        """Test use cases with None inputs."""
        from app.application.dto import CreateUserRequest
        from app.application.use_cases.user_management import CreateUserUseCase

        mock_repo = AsyncMock()
        use_case = CreateUserUseCase(mock_repo)

        # Test with None name
        request = CreateUserRequest(name=None)
        result = await use_case.execute(request)

        # Should handle gracefully
        assert result.success is False

    @pytest.mark.asyncio
    async def test_concurrent_use_case_execution(self):
        """Test concurrent execution of use cases."""
        import asyncio

        from app.application.use_cases.user_management import GetUserUseCase

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        use_case = GetUserUseCase(mock_repo)

        # Execute multiple operations concurrently
        tasks = [use_case.execute(f"user-{i}") for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete
        assert len(results) == 5
        for result in results:
            assert not isinstance(result, Exception)
            assert result.success is False  # Users not found


def test_use_case_imports():
    """Test all use case imports work."""
    from app.application.use_cases.notification_sending import (
        SendBulkNotificationUseCase,
        SendNotificationUseCase,
    )
    from app.application.use_cases.user_management import (
        CreateUserUseCase,
        GetAllActiveUsersUseCase,
        GetUserUseCase,
        UpdateUserUseCase,
    )

    # All imports successful
    assert CreateUserUseCase is not None
    assert GetUserUseCase is not None
    assert UpdateUserUseCase is not None
    assert GetAllActiveUsersUseCase is not None
    assert SendNotificationUseCase is not None
    assert SendBulkNotificationUseCase is not None
