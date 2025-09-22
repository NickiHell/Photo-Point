"""
Tests for SQLAlchemy repository implementations.
Testing repository functionality with proper entity construction.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.delivery import Delivery
from app.domain.entities.notification import Notification
from app.domain.entities.user import User
from app.domain.value_objects.delivery import DeliveryId, DeliveryStatus
from app.domain.value_objects.notification import (
    NotificationId,
    NotificationPriority,
)
from app.domain.value_objects.user import UserId
from app.infrastructure.repositories.models import (
    DeliveryModel,
    NotificationModel,
    UserModel,
)
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SQLAlchemyDeliveryRepository,
    SQLAlchemyNotificationRepository,
    SQLAlchemyUserRepository,
)


@pytest.mark.asyncio
class TestSQLAlchemyUserRepository:
    """Test SQLAlchemy User Repository functionality"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def user_repository(self, mock_session):
        return SQLAlchemyUserRepository(mock_session)

    @pytest.fixture
    def sample_user_model(self):
        return UserModel(
            id="user-123",
            email="test@gmail.com",  # Use real domain to avoid validation issues
            phone_number="+1234567890",
            telegram_id="123456789",
            is_active=True,
            preferences={"theme": "dark"},
            created_at=datetime(2025, 1, 1),
        )

    @pytest.fixture
    def minimal_user_model(self):
        return UserModel(
            id="user-minimal",
            email=None,
            phone_number=None,
            telegram_id=None,
            is_active=False,
            preferences={},
            created_at=datetime(2025, 1, 1),
        )

    def test_model_to_entity_with_full_data(self, user_repository, sample_user_model):
        """Test converting UserModel with all fields to User entity"""
        with patch("app.domain.value_objects.user.validate_email") as mock_validate:
            mock_validate.return_value = MagicMock()  # Mock successful validation
            entity = user_repository._model_to_entity(sample_user_model)

            assert entity.id.value == "user-123"
            assert entity.email.value == "test@gmail.com"
            assert entity.phone_number.value == "+1234567890"
            assert entity.telegram_id.value == "123456789"
            assert entity.is_active is True
            assert entity.preferences == {"theme": "dark"}

    def test_model_to_entity_with_minimal_data(
        self, user_repository, minimal_user_model
    ):
        """Test converting UserModel with None values"""
        entity = user_repository._model_to_entity(minimal_user_model)

        assert entity.id.value == "user-minimal"
        assert entity.email is None
        assert entity.phone_number is None
        assert entity.telegram_id is None
        assert entity.is_active is False
        assert entity.preferences == {}

    async def test_save_new_user(self, user_repository, mock_session):
        """Test saving new user entity"""
        # Mock no existing user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Create minimal user entity using factory method
        user = User.create(
            id=UserId("new-user"), email=None, phone_number=None, telegram_id=None
        )

        await user_repository.save(user)

        # Verify session operations
        mock_session.execute.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_save_existing_user(
        self, user_repository, sample_user_model, mock_session
    ):
        """Test updating existing user entity"""
        # Mock existing user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result

        user = User.create(
            id=UserId("user-123"), email=None, phone_number=None, telegram_id=None
        )

        await user_repository.save(user)

        # Verify user fields were updated
        assert sample_user_model.is_active is True
        mock_session.commit.assert_called_once()

    async def test_get_by_id_found(
        self, user_repository, sample_user_model, mock_session
    ):
        """Test getting user by ID when user exists"""
        # Mock user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result

        with patch("app.domain.value_objects.user.validate_email") as mock_validate:
            mock_validate.return_value = MagicMock()
            user = await user_repository.get_by_id(UserId("user-123"))

            assert user is not None
            assert user.id.value == "user-123"

    async def test_get_by_id_not_found(self, user_repository, mock_session):
        """Test getting user by ID when user doesn't exist"""
        # Mock no user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        user = await user_repository.get_by_id(UserId("nonexistent"))

        assert user is None

    async def test_get_all_active(self, user_repository, mock_session):
        """Test getting all active users"""
        # Mock multiple users found
        mock_users = [
            UserModel(
                id="user-1", email=None, is_active=True, created_at=datetime.now()
            ),
            UserModel(
                id="user-2", email=None, is_active=True, created_at=datetime.now()
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_session.execute.return_value = mock_result

        users = await user_repository.get_all_active()

        assert len(users) == 2
        assert all(user.is_active for user in users)

    async def test_delete_user(self, user_repository, mock_session):
        """Test deleting user by ID"""
        await user_repository.delete(UserId("user-123"))

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
class TestSQLAlchemyNotificationRepository:
    """Test SQLAlchemy Notification Repository functionality"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def notification_repository(self, mock_session):
        return SQLAlchemyNotificationRepository(mock_session)

    @pytest.fixture
    def sample_notification_model(self):
        return NotificationModel(
            id="notif-123",
            recipient_id="user-123",
            message_template="Hello world",
            message_variables={"name": "John"},
            channels=["email", "sms"],
            priority="HIGH",
            scheduled_at=datetime(2025, 1, 1, 12, 0),
            retry_policy={"max_attempts": 3},
            notification_metadata={"source": "api"},
            created_at=datetime(2025, 1, 1, 10, 0),
        )

    def test_notification_model_to_entity(
        self, notification_repository, sample_notification_model
    ):
        """Test converting NotificationModel to Notification entity"""
        entity = notification_repository._model_to_entity(sample_notification_model)

        assert entity.id.value == "notif-123"
        assert entity.recipient_id.value == "user-123"
        assert entity.message.template == "Hello world"
        assert entity.message.variables == {"name": "John"}
        assert entity.channels == ["email", "sms"]
        assert entity.priority == NotificationPriority.HIGH
        assert entity.retry_policy == {"max_attempts": 3}
        assert entity.metadata == {"source": "api"}

    async def test_save_new_notification(self, notification_repository, mock_session):
        """Test saving new notification"""
        # Mock no existing notification
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Create notification entity
        notification = Notification.create(
            id=NotificationId("new-notif"),
            recipient_id=UserId("user-123"),
            message_template="Test message",
            channels=["email"],
            priority=NotificationPriority.MEDIUM,
        )

        await notification_repository.save(notification)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_save_existing_notification(
        self, notification_repository, sample_notification_model, mock_session
    ):
        """Test updating existing notification"""
        # Mock existing notification found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_notification_model
        mock_session.execute.return_value = mock_result

        notification = Notification.create(
            id=NotificationId("notif-123"),
            recipient_id=UserId("user-123"),
            message_template="Updated message",
            channels=["email"],
            priority=NotificationPriority.LOW,
        )

        await notification_repository.save(notification)

        # Verify fields were updated
        assert sample_notification_model.message_template == "Updated message"
        assert sample_notification_model.priority == "LOW"
        mock_session.commit.assert_called_once()

    async def test_get_by_id_found(
        self, notification_repository, sample_notification_model, mock_session
    ):
        """Test getting notification by ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_notification_model
        mock_session.execute.return_value = mock_result

        notification = await notification_repository.get_by_id(
            NotificationId("notif-123")
        )

        assert notification is not None
        assert notification.id.value == "notif-123"
        assert notification.message.template == "Hello world"

    async def test_get_by_id_not_found(self, notification_repository, mock_session):
        """Test getting notification by ID when not found"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        notification = await notification_repository.get_by_id(
            NotificationId("nonexistent")
        )

        assert notification is None

    async def test_get_pending_notifications(
        self, notification_repository, mock_session
    ):
        """Test getting pending notifications"""
        mock_notifications = [
            NotificationModel(
                id="n1",
                recipient_id="u1",
                message_template="Test",
                channels=["email"],
                priority="MEDIUM",
                scheduled_at=datetime.now(),
                created_at=datetime.now(),
            ),
            NotificationModel(
                id="n2",
                recipient_id="u2",
                message_template="Test2",
                channels=["sms"],
                priority="LOW",
                scheduled_at=datetime.now(),
                created_at=datetime.now(),
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute.return_value = mock_result

        notifications = await notification_repository.get_pending(limit=10)

        assert len(notifications) == 2
        mock_session.execute.assert_called_once()

    async def test_delete_notification(self, notification_repository, mock_session):
        """Test deleting notification"""
        await notification_repository.delete(NotificationId("notif-123"))

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
class TestSQLAlchemyDeliveryRepository:
    """Test SQLAlchemy Delivery Repository functionality"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def delivery_repository(self, mock_session):
        return SQLAlchemyDeliveryRepository(mock_session)

    @pytest.fixture
    def sample_delivery_model_with_notification(self):
        # Create notification model first
        notification_model = NotificationModel(
            id="notif-123",
            recipient_id="user-123",
            message_template="Test message",
            message_variables={"key": "value"},
            channels=["email"],
            priority="MEDIUM",
            scheduled_at=datetime(2025, 1, 1),
            retry_policy={"max_attempts": 2},
            notification_metadata={"test": "data"},
            created_at=datetime(2025, 1, 1),
        )

        # Create delivery model
        delivery_model = DeliveryModel(
            id="delivery-123",
            notification_id="notif-123",
            channel="email",
            provider="smtp",
            status="PENDING",
            created_at=datetime(2025, 1, 1),
            completed_at=None,
        )

        # Set relationships
        delivery_model.notification = notification_model
        delivery_model.attempts = []

        return delivery_model

    def test_delivery_model_to_entity(
        self, delivery_repository, sample_delivery_model_with_notification
    ):
        """Test converting DeliveryModel to Delivery entity"""
        entity = delivery_repository._model_to_entity(
            sample_delivery_model_with_notification
        )

        assert entity.id.value == "delivery-123"
        assert entity.notification.id.value == "notif-123"
        assert entity.channel == "email"
        assert entity.provider == "smtp"
        assert entity.status == DeliveryStatus.PENDING

    async def test_save_new_delivery(self, delivery_repository, mock_session):
        """Test saving new delivery"""
        # Mock no existing delivery
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Create sample entities
        notification = Notification.create(
            id=NotificationId("notif-123"),
            recipient_id=UserId("user-123"),
            message_template="Test",
            channels=["email"],
            priority=NotificationPriority.MEDIUM,
        )

        delivery = Delivery.create(
            id=DeliveryId("delivery-123"),
            notification=notification,
            channel="email",
            provider="smtp",
        )

        await delivery_repository.save(delivery)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_get_by_id_found(
        self, delivery_repository, sample_delivery_model_with_notification, mock_session
    ):
        """Test getting delivery by ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = (
            sample_delivery_model_with_notification
        )
        mock_session.execute.return_value = mock_result

        delivery = await delivery_repository.get_by_id(DeliveryId("delivery-123"))

        assert delivery is not None
        assert delivery.id.value == "delivery-123"
        assert delivery.channel == "email"

    async def test_get_by_id_not_found(self, delivery_repository, mock_session):
        """Test getting delivery by ID when not found"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        delivery = await delivery_repository.get_by_id(DeliveryId("nonexistent"))

        assert delivery is None

    async def test_get_statistics(self, delivery_repository, mock_session):
        """Test getting delivery statistics"""
        # Mock delivery models with various statuses
        mock_deliveries = [
            DeliveryModel(
                id="d1",
                notification_id="n1",
                channel="email",
                provider="smtp",
                status="DELIVERED",
                created_at=datetime.now(),
            ),
            DeliveryModel(
                id="d2",
                notification_id="n2",
                channel="sms",
                provider="twilio",
                status="FAILED",
                created_at=datetime.now(),
            ),
            DeliveryModel(
                id="d3",
                notification_id="n3",
                channel="email",
                provider="smtp",
                status="PENDING",
                created_at=datetime.now(),
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_deliveries
        mock_session.execute.return_value = mock_result

        stats = await delivery_repository.get_statistics(days=7)

        assert stats["period_days"] == 7
        assert stats["total_deliveries"] == 3
        assert stats["successful_deliveries"] == 1
        assert stats["failed_deliveries"] == 1
        assert stats["pending_deliveries"] == 1
        assert "provider_statistics" in stats


class TestSQLAlchemyRepositoriesIntegration:
    """Integration tests for SQLAlchemy repositories coordination"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    def test_repository_initialization(self, mock_session):
        """Test that all repositories can be initialized with session"""
        user_repo = SQLAlchemyUserRepository(mock_session)
        notification_repo = SQLAlchemyNotificationRepository(mock_session)
        delivery_repo = SQLAlchemyDeliveryRepository(mock_session)

        assert user_repo.session is mock_session
        assert notification_repo.session is mock_session
        assert delivery_repo.session is mock_session


if __name__ == "__main__":
    # Run this test file directly for development
    pytest.main([__file__, "-v"])
