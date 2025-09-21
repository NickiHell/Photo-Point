"""
Comprehensive tests for SQLAlchemy repository implementations.
These tests target 142 lines of sqlalchemy_repositories.py (currently 0% coverage)
to provide significant coverage boost toward 90% goal.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.delivery import Delivery
from app.domain.entities.notification import Notification
from app.domain.entities.user import User
from app.domain.value_objects.delivery import DeliveryId, DeliveryStatus
from app.domain.value_objects.notification import (
    MessageTemplate,
    NotificationId,
    NotificationPriority,
)
from app.domain.value_objects.user import Email, PhoneNumber, TelegramChatId, UserId
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


class TestSQLAlchemyUserRepository:
    """Test SQLAlchemy User Repository - targeting ~50 lines coverage"""

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
            email="test@example.com",
            phone_number="+1234567890",
            telegram_id="123456789",
            is_active=True,
            preferences={"theme": "dark"},
            created_at=datetime(2025, 1, 1)
        )

    @pytest.fixture
    def sample_user_entity(self):
        return User(
            id=UserId("user-123"),
            email=Email("test@example.com"),
            phone_number=PhoneNumber("+1234567890"),
            telegram_id=TelegramChatId("123456789"),
            is_active=True,
            preferences={"theme": "dark"},
            created_at=datetime(2025, 1, 1)
        )

    def test_model_to_entity_conversion(self, user_repository, sample_user_model):
        """Test conversion from UserModel to User entity"""
        entity = user_repository._model_to_entity(sample_user_model)

        assert entity.id.value == "user-123"
        assert entity.email.value == "test@example.com"
        assert entity.phone_number.value == "+1234567890"
        assert entity.telegram_id.value == "123456789"
        assert entity.is_active is True
        assert entity.preferences == {"theme": "dark"}
        assert entity.created_at == datetime(2025, 1, 1)

    def test_model_to_entity_with_none_values(self, user_repository):
        """Test conversion with None optional fields"""
        model = UserModel(
            id="user-123",
            email=None,
            phone_number=None,
            telegram_id=None,
            is_active=False,
            preferences=None,
            created_at=datetime(2025, 1, 1)
        )

        entity = user_repository._model_to_entity(model)

        assert entity.id.value == "user-123"
        assert entity.email is None
        assert entity.phone_number is None
        assert entity.telegram_id is None
        assert entity.is_active is False
        assert entity.preferences == {}

    def test_entity_to_model_conversion(self, user_repository, sample_user_entity):
        """Test conversion from User entity to UserModel"""
        model = user_repository._entity_to_model(sample_user_entity)

        assert model.id == "user-123"
        assert model.email == "test@example.com"
        assert model.phone_number == "+1234567890"
        assert model.telegram_id == "123456789"
        assert model.is_active is True
        assert model.preferences == {"theme": "dark"}
        assert model.created_at == datetime(2025, 1, 1)

    def test_entity_to_model_with_none_values(self, user_repository):
        """Test conversion with None optional fields"""
        entity = User(
            id=UserId("user-123"),
            email=None,
            phone_number=None,
            telegram_id=None,
            is_active=False,
            preferences={"setting": "value"},
            created_at=datetime(2025, 1, 1)
        )

        model = user_repository._entity_to_model(entity)

        assert model.id == "user-123"
        assert model.email is None
        assert model.phone_number is None
        assert model.telegram_id is None
        assert model.is_active is False
        assert model.preferences == {"setting": "value"}

    async def test_save_new_user(self, user_repository, sample_user_entity, mock_session):
        """Test saving new user entity"""
        # Mock no existing user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await user_repository.save(sample_user_entity)

        # Verify session operations
        mock_session.execute.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_save_existing_user(self, user_repository, sample_user_entity, sample_user_model, mock_session):
        """Test updating existing user entity"""
        # Mock existing user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result

        await user_repository.save(sample_user_entity)

        # Verify user fields were updated
        assert sample_user_model.email == "test@example.com"
        assert sample_user_model.is_active is True
        mock_session.commit.assert_called_once()

    async def test_get_by_id_found(self, user_repository, sample_user_model, mock_session):
        """Test getting user by ID when user exists"""
        # Mock user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result

        user = await user_repository.get_by_id(UserId("user-123"))

        assert user is not None
        assert user.id.value == "user-123"
        assert user.email.value == "test@example.com"

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
            UserModel(id="user-1", email="user1@test.com", is_active=True, created_at=datetime.now()),
            UserModel(id="user-2", email="user2@test.com", is_active=True, created_at=datetime.now())
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


class TestSQLAlchemyNotificationRepository:
    """Test SQLAlchemy Notification Repository - targeting ~45 lines coverage"""

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
            message_template="Hello {name}",
            message_variables={"name": "John"},
            channels=["email", "sms"],
            priority="HIGH",
            scheduled_at=datetime(2025, 1, 1, 12, 0),
            retry_policy={"max_attempts": 3},
            metadata={"source": "api"},
            created_at=datetime(2025, 1, 1, 10, 0)
        )

    @pytest.fixture
    def sample_notification_entity(self):
        return Notification(
            id=NotificationId("notif-123"),
            recipient_id=UserId("user-123"),
            message=MessageTemplate("Hello {name}", {"name": "John"}),
            channels=["email", "sms"],
            priority=NotificationPriority.HIGH,
            scheduled_at=datetime(2025, 1, 1, 12, 0),
            retry_policy={"max_attempts": 3},
            metadata={"source": "api"},
            created_at=datetime(2025, 1, 1, 10, 0)
        )

    def test_notification_model_to_entity(self, notification_repository, sample_notification_model):
        """Test converting NotificationModel to Notification entity"""
        entity = notification_repository._model_to_entity(sample_notification_model)

        assert entity.id.value == "notif-123"
        assert entity.recipient_id.value == "user-123"
        assert entity.message.template == "Hello {name}"
        assert entity.message.variables == {"name": "John"}
        assert entity.channels == ["email", "sms"]
        assert entity.priority == NotificationPriority.HIGH
        assert entity.retry_policy == {"max_attempts": 3}

    def test_notification_entity_to_model(self, notification_repository, sample_notification_entity):
        """Test converting Notification entity to NotificationModel"""
        model = notification_repository._entity_to_model(sample_notification_entity)

        assert model.id == "notif-123"
        assert model.recipient_id == "user-123"
        assert model.message_template == "Hello {name}"
        assert model.message_variables == {"name": "John"}
        assert model.priority == "HIGH"
        assert model.channels == ["email", "sms"]

    async def test_save_new_notification(self, notification_repository, sample_notification_entity, mock_session):
        """Test saving new notification"""
        # Mock no existing notification
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await notification_repository.save(sample_notification_entity)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_save_existing_notification(self, notification_repository, sample_notification_entity, sample_notification_model, mock_session):
        """Test updating existing notification"""
        # Mock existing notification found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_notification_model
        mock_session.execute.return_value = mock_result

        await notification_repository.save(sample_notification_entity)

        # Verify fields were updated
        assert sample_notification_model.message_template == "Hello {name}"
        assert sample_notification_model.priority == "HIGH"
        mock_session.commit.assert_called_once()

    async def test_get_by_id_found(self, notification_repository, sample_notification_model, mock_session):
        """Test getting notification by ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_notification_model
        mock_session.execute.return_value = mock_result

        notification = await notification_repository.get_by_id(NotificationId("notif-123"))

        assert notification is not None
        assert notification.id.value == "notif-123"

    async def test_get_by_id_not_found(self, notification_repository, mock_session):
        """Test getting notification by ID when not found"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        notification = await notification_repository.get_by_id(NotificationId("nonexistent"))

        assert notification is None

    async def test_get_pending_notifications(self, notification_repository, mock_session):
        """Test getting pending notifications"""
        mock_notifications = [
            NotificationModel(id="n1", recipient_id="u1", message_template="Test",
                            channels=["email"], priority="MEDIUM",
                            scheduled_at=datetime.now(), created_at=datetime.now()),
            NotificationModel(id="n2", recipient_id="u2", message_template="Test2",
                            channels=["sms"], priority="LOW",
                            scheduled_at=datetime.now(), created_at=datetime.now())
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute.return_value = mock_result

        notifications = await notification_repository.get_pending(limit=10)

        assert len(notifications) == 2
        mock_session.execute.assert_called_once()

    async def test_get_by_recipient(self, notification_repository, mock_session):
        """Test getting notifications by recipient ID"""
        mock_notifications = [
            NotificationModel(id="n1", recipient_id="user-123", message_template="Test",
                            channels=["email"], priority="HIGH",
                            scheduled_at=datetime.now(), created_at=datetime.now())
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute.return_value = mock_result

        notifications = await notification_repository.get_by_recipient(UserId("user-123"))

        assert len(notifications) == 1
        assert notifications[0].recipient_id.value == "user-123"

    async def test_delete_notification(self, notification_repository, mock_session):
        """Test deleting notification"""
        await notification_repository.delete(NotificationId("notif-123"))

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestSQLAlchemyDeliveryRepository:
    """Test SQLAlchemy Delivery Repository - targeting ~47 lines coverage"""

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
            metadata={"test": "data"},
            created_at=datetime(2025, 1, 1)
        )

        # Create delivery model
        delivery_model = DeliveryModel(
            id="delivery-123",
            notification_id="notif-123",
            channel="email",
            provider="smtp",
            status="PENDING",
            created_at=datetime(2025, 1, 1),
            completed_at=None
        )

        # Set relationships
        delivery_model.notification = notification_model
        delivery_model.attempts = []

        return delivery_model

    def test_delivery_model_to_entity(self, delivery_repository, sample_delivery_model_with_notification):
        """Test converting DeliveryModel to Delivery entity"""
        entity = delivery_repository._model_to_entity(sample_delivery_model_with_notification)

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

        # Create sample delivery entity
        notification = Notification(
            id=NotificationId("notif-123"),
            recipient_id=UserId("user-123"),
            message=MessageTemplate("Test", {}),
            channels=["email"],
            priority=NotificationPriority.MEDIUM,
            scheduled_at=datetime(2025, 1, 1),
            retry_policy={},
            metadata={},
            created_at=datetime(2025, 1, 1)
        )

        delivery = Delivery(
            id=DeliveryId("delivery-123"),
            notification=notification,
            channel="email",
            provider="smtp",
            status=DeliveryStatus.PENDING,
            created_at=datetime(2025, 1, 1)
        )

        await delivery_repository.save(delivery)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_save_existing_delivery(self, delivery_repository, sample_delivery_model_with_notification, mock_session):
        """Test updating existing delivery"""
        # Mock existing delivery found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_delivery_model_with_notification
        mock_session.execute.return_value = mock_result

        # Create delivery entity for update
        notification = Notification(
            id=NotificationId("notif-123"),
            recipient_id=UserId("user-123"),
            message=MessageTemplate("Test", {}),
            channels=["email"],
            priority=NotificationPriority.MEDIUM,
            scheduled_at=datetime(2025, 1, 1),
            retry_policy={},
            metadata={},
            created_at=datetime(2025, 1, 1)
        )

        delivery = Delivery(
            id=DeliveryId("delivery-123"),
            notification=notification,
            channel="email",
            provider="smtp",
            status=DeliveryStatus.DELIVERED,
            created_at=datetime(2025, 1, 1)
        )
        delivery._completed_at = datetime(2025, 1, 1, 12, 0)

        await delivery_repository.save(delivery)

        # Verify status was updated
        assert sample_delivery_model_with_notification.status == "DELIVERED"
        mock_session.commit.assert_called_once()

    async def test_get_by_id_found(self, delivery_repository, sample_delivery_model_with_notification, mock_session):
        """Test getting delivery by ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_delivery_model_with_notification
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

    async def test_get_by_notification(self, delivery_repository, sample_delivery_model_with_notification, mock_session):
        """Test getting deliveries by notification ID"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_delivery_model_with_notification]
        mock_session.execute.return_value = mock_result

        deliveries = await delivery_repository.get_by_notification(NotificationId("notif-123"))

        assert len(deliveries) == 1
        assert deliveries[0].notification.id.value == "notif-123"

    async def test_get_pending_retries(self, delivery_repository, mock_session):
        """Test getting deliveries that need retry"""
        retry_delivery = DeliveryModel(
            id="retry-delivery",
            notification_id="notif-123",
            channel="sms",
            provider="twilio",
            status="RETRYING",
            created_at=datetime(2025, 1, 1)
        )
        retry_delivery.notification = NotificationModel(
            id="notif-123", recipient_id="user-123", message_template="Test",
            channels=["sms"], priority="HIGH", scheduled_at=datetime.now(), created_at=datetime.now()
        )
        retry_delivery.attempts = []

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [retry_delivery]
        mock_session.execute.return_value = mock_result

        deliveries = await delivery_repository.get_pending_retries()

        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.RETRYING

    async def test_get_statistics(self, delivery_repository, mock_session):
        """Test getting delivery statistics"""
        # Mock delivery models with various statuses
        mock_deliveries = [
            DeliveryModel(id="d1", notification_id="n1", channel="email", provider="smtp",
                         status="DELIVERED", created_at=datetime.now()),
            DeliveryModel(id="d2", notification_id="n2", channel="sms", provider="twilio",
                         status="FAILED", created_at=datetime.now()),
            DeliveryModel(id="d3", notification_id="n3", channel="email", provider="smtp",
                         status="PENDING", created_at=datetime.now()),
            DeliveryModel(id="d4", notification_id="n4", channel="email", provider="smtp",
                         status="DELIVERED", created_at=datetime.now())
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_deliveries
        mock_session.execute.return_value = mock_result

        stats = await delivery_repository.get_statistics(days=7)

        assert stats["period_days"] == 7
        assert stats["total_deliveries"] == 4
        assert stats["successful_deliveries"] == 2
        assert stats["failed_deliveries"] == 1
        assert stats["pending_deliveries"] == 1
        assert stats["success_rate"] == 50.0
        assert "provider_statistics" in stats
        assert stats["provider_statistics"]["smtp"]["total"] == 3
        assert stats["provider_statistics"]["smtp"]["successful"] == 2
        assert stats["provider_statistics"]["twilio"]["total"] == 1
        assert stats["provider_statistics"]["twilio"]["successful"] == 0


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

    async def test_repository_session_sharing(self, mock_session):
        """Test that repositories can share the same session for transactions"""
        user_repo = SQLAlchemyUserRepository(mock_session)
        notification_repo = SQLAlchemyNotificationRepository(mock_session)

        # Mock operations that would occur in same transaction
        user_entity = User(
            id=UserId("user-123"),
            email=Email("test@example.com"),
            is_active=True,
            preferences={},
            created_at=datetime.now()
        )

        notification_entity = Notification(
            id=NotificationId("notif-123"),
            recipient_id=UserId("user-123"),
            message=MessageTemplate("Hello", {}),
            channels=["email"],
            priority=NotificationPriority.MEDIUM,
            scheduled_at=datetime.now(),
            retry_policy={},
            metadata={},
            created_at=datetime.now()
        )

        # Mock no existing entities
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Simulate transaction operations
        await user_repo.save(user_entity)
        await notification_repo.save(notification_entity)

        # Verify session was used for both operations
        assert mock_session.add.call_count == 2
        assert mock_session.commit.call_count == 2


if __name__ == "__main__":
    # Run this test file directly for development
    pytest.main([__file__, "-v"])
