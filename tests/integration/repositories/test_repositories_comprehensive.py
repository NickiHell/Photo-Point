"""
Comprehensive tests for all Repository implementations to maximize coverage.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest


class TestInMemoryUserRepository:
    """Test InMemoryUserRepository comprehensively."""

    @pytest.fixture
    def user_repo(self):
        """Create InMemoryUserRepository instance."""
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryUserRepository,
        )

        return InMemoryUserRepository()

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        return User(
            user_id=UserId("user-123"),
            name=UserName("Test User"),
            email=Email("test@gmail.com"),
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_save_user_success(self, user_repo, sample_user):
        """Test successful user saving."""
        await user_repo.save(sample_user)

        # Verify user is saved
        retrieved = await user_repo.get_by_id(sample_user.id)
        assert retrieved is not None
        assert retrieved.id == sample_user.id
        assert retrieved.name.value == sample_user.name.value
        assert retrieved.email.value == sample_user.email.value

    @pytest.mark.asyncio
    async def test_get_by_id_existing_user(self, user_repo, sample_user):
        """Test getting existing user by ID."""
        await user_repo.save(sample_user)

        retrieved = await user_repo.get_by_id(sample_user.id)
        assert retrieved is not None
        assert retrieved.id.value == "user-123"
        assert retrieved.name.value == "Test User"

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_user(self, user_repo):
        """Test getting nonexistent user by ID."""
        from app.domain.value_objects.user import UserId

        result = await user_repo.get_by_id(UserId("nonexistent"))
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_active_users(self, user_repo):
        """Test getting all active users."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        # Create active and inactive users
        active_user1 = User(
            user_id=UserId("active-1"),
            name=UserName("Active User 1"),
            email=Email("active1@gmail.com"),
            is_active=True,
        )
        active_user2 = User(
            user_id=UserId("active-2"),
            name=UserName("Active User 2"),
            email=Email("active2@gmail.com"),
            is_active=True,
        )
        inactive_user = User(
            user_id=UserId("inactive-1"),
            name=UserName("Inactive User"),
            email=Email("inactive@gmail.com"),
            is_active=False,
        )

        # Save all users
        await user_repo.save(active_user1)
        await user_repo.save(active_user2)
        await user_repo.save(inactive_user)

        # Get all active users
        active_users = await user_repo.get_all_active()

        assert len(active_users) == 2
        assert all(user.is_active for user in active_users)
        active_ids = [user.id.value for user in active_users]
        assert "active-1" in active_ids
        assert "active-2" in active_ids
        assert "inactive-1" not in active_ids

    @pytest.mark.asyncio
    async def test_delete_existing_user(self, user_repo, sample_user):
        """Test deleting existing user."""
        await user_repo.save(sample_user)

        # Verify user exists
        retrieved = await user_repo.get_by_id(sample_user.id)
        assert retrieved is not None

        # Delete user
        await user_repo.delete(sample_user.id)

        # Verify user is deleted
        retrieved = await user_repo.get_by_id(sample_user.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, user_repo):
        """Test deleting nonexistent user (should not raise error)."""
        from app.domain.value_objects.user import UserId

        # Should not raise error
        await user_repo.delete(UserId("nonexistent"))

    @pytest.mark.asyncio
    async def test_update_user(self, user_repo, sample_user):
        """Test updating existing user."""
        await user_repo.save(sample_user)

        # Update user
        sample_user.update_name(sample_user.name.__class__("Updated Name"))
        await user_repo.save(sample_user)  # Save updates the same ID

        # Verify update
        retrieved = await user_repo.get_by_id(sample_user.id)
        assert retrieved is not None
        assert retrieved.name.value == "Updated Name"


class TestInMemoryNotificationRepository:
    """Test InMemoryNotificationRepository comprehensively."""

    @pytest.fixture
    def notification_repo(self):
        """Create InMemoryNotificationRepository instance."""
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryNotificationRepository,
        )

        return InMemoryNotificationRepository()

    @pytest.fixture
    def sample_notification(self):
        """Create sample notification for testing."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
        )
        from app.domain.value_objects.user import UserId

        return Notification(
            notification_id=NotificationId("notif-123"),
            recipient_id=UserId("user-123"),
            message_template=MessageTemplate("Test Subject", "Test message content"),
        )

    @pytest.mark.asyncio
    async def test_save_notification_success(
        self, notification_repo, sample_notification
    ):
        """Test successful notification saving."""
        await notification_repo.save(sample_notification)

        # Verify notification is saved
        retrieved = await notification_repo.get_by_id(sample_notification.id)
        assert retrieved is not None
        assert retrieved.id == sample_notification.id
        assert retrieved.recipient_id == sample_notification.recipient_id

    @pytest.mark.asyncio
    async def test_get_by_id_existing_notification(
        self, notification_repo, sample_notification
    ):
        """Test getting existing notification by ID."""
        await notification_repo.save(sample_notification)

        retrieved = await notification_repo.get_by_id(sample_notification.id)
        assert retrieved is not None
        assert retrieved.id.value == "notif-123"

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_notification(self, notification_repo):
        """Test getting nonexistent notification by ID."""
        from app.domain.value_objects.notification import NotificationId

        result = await notification_repo.get_by_id(NotificationId("nonexistent"))
        assert result is None

    @pytest.mark.asyncio
    async def test_get_pending_notifications(self, notification_repo):
        """Test getting pending notifications."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
        )
        from app.domain.value_objects.user import UserId

        # Create notifications with different scheduled times
        now = datetime.now(UTC)
        past_notification = Notification(
            notification_id=NotificationId("past-notif"),
            recipient_id=UserId("user-1"),
            message_template=MessageTemplate("Past", "Past notification"),
            scheduled_at=now - timedelta(hours=1),
        )
        future_notification = Notification(
            notification_id=NotificationId("future-notif"),
            recipient_id=UserId("user-2"),
            message_template=MessageTemplate("Future", "Future notification"),
            scheduled_at=now + timedelta(hours=1),
        )

        await notification_repo.save(past_notification)
        await notification_repo.save(future_notification)

        # Get pending notifications (should return past notification)
        pending = await notification_repo.get_pending_notifications()

        assert len(pending) >= 1  # At least the past notification
        pending_ids = [notif.id.value for notif in pending]
        assert "past-notif" in pending_ids

    @pytest.mark.asyncio
    async def test_get_notifications_for_user(self, notification_repo):
        """Test getting notifications for specific user."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
        )
        from app.domain.value_objects.user import UserId

        user1_id = UserId("user-1")
        user2_id = UserId("user-2")

        # Create notifications for different users
        notif1 = Notification(
            notification_id=NotificationId("notif-1"),
            recipient_id=user1_id,
            message_template=MessageTemplate("Subject 1", "Message 1"),
        )
        notif2 = Notification(
            notification_id=NotificationId("notif-2"),
            recipient_id=user1_id,
            message_template=MessageTemplate("Subject 2", "Message 2"),
        )
        notif3 = Notification(
            notification_id=NotificationId("notif-3"),
            recipient_id=user2_id,
            message_template=MessageTemplate("Subject 3", "Message 3"),
        )

        await notification_repo.save(notif1)
        await notification_repo.save(notif2)
        await notification_repo.save(notif3)

        # Get notifications for user1
        user1_notifications = await notification_repo.get_notifications_for_user(
            user1_id
        )

        assert len(user1_notifications) == 2
        notification_ids = [notif.id.value for notif in user1_notifications]
        assert "notif-1" in notification_ids
        assert "notif-2" in notification_ids
        assert "notif-3" not in notification_ids


class TestInMemoryDeliveryRepository:
    """Test InMemoryDeliveryRepository comprehensively."""

    @pytest.fixture
    def delivery_repo(self):
        """Create InMemoryDeliveryRepository instance."""
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryDeliveryRepository,
        )

        return InMemoryDeliveryRepository()

    @pytest.fixture
    def sample_delivery(self):
        """Create sample delivery for testing."""
        from app.domain.entities.delivery import Delivery
        from app.domain.entities.notification import Notification
        from app.domain.entities.user import User
        from app.domain.value_objects.delivery import DeliveryId
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
            NotificationPriority,
        )
        from app.domain.value_objects.user import Email, UserId, UserName

        # Create user
        user = User(
            user_id=UserId("user-123"),
            name=UserName("Test User"),
            email=Email("test@example.com"),
        )

        # Create notification
        notification = Notification(
            notification_id=NotificationId("notif-123"),
            recipient_id=UserId("user-123"),
            message_template=MessageTemplate("Hello!", {}),
            priority=NotificationPriority.NORMAL,
        )

        # Create delivery
        return Delivery(
            delivery_id=DeliveryId("delivery-123"),
            notification=notification,
            user=user,
        )

    @pytest.mark.asyncio
    async def test_save_delivery_success(self, delivery_repo, sample_delivery):
        """Test successful delivery saving."""
        await delivery_repo.save(sample_delivery)

        # Verify delivery is saved
        retrieved = await delivery_repo.get_by_id(sample_delivery.id)
        assert retrieved is not None
        assert retrieved.id == sample_delivery.id
        assert retrieved.channel == sample_delivery.channel

    @pytest.mark.asyncio
    async def test_get_by_id_existing_delivery(self, delivery_repo, sample_delivery):
        """Test getting existing delivery by ID."""
        await delivery_repo.save(sample_delivery)

        retrieved = await delivery_repo.get_by_id(sample_delivery.id)
        assert retrieved is not None
        assert retrieved.id.value == "delivery-123"
        assert retrieved.channel == "email"

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_delivery(self, delivery_repo):
        """Test getting nonexistent delivery by ID."""
        from app.domain.value_objects.delivery import DeliveryId

        result = await delivery_repo.get_by_id(DeliveryId("nonexistent"))
        assert result is None

    @pytest.mark.asyncio
    async def test_get_deliveries_for_user(self, delivery_repo):
        """Test getting deliveries for specific user."""
        from app.domain.entities.delivery import Delivery
        from app.domain.entities.notification import Notification
        from app.domain.entities.user import User
        from app.domain.value_objects.delivery import DeliveryId
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
            NotificationPriority,
        )
        from app.domain.value_objects.user import Email, UserId, UserName

        user1_id = UserId("user-1")
        user2_id = UserId("user-2")

        # Create users
        user1 = User(user1_id, UserName("User 1"), email=Email("user1@example.com"))
        user2 = User(user2_id, UserName("User 2"), email=Email("user2@example.com"))

        # Create notifications
        notif1 = Notification(
            NotificationId("notif-1"), user1_id, MessageTemplate("Hello!", {})
        )
        notif2 = Notification(
            NotificationId("notif-2"), user1_id, MessageTemplate("Hi!", {})
        )
        notif3 = Notification(
            NotificationId("notif-3"), user2_id, MessageTemplate("Hey!", {})
        )

        # Create deliveries for different users
        delivery1 = Delivery(DeliveryId("delivery-1"), notif1, user1)
        delivery2 = Delivery(DeliveryId("delivery-2"), notif2, user1)
        delivery3 = Delivery(DeliveryId("delivery-3"), notif3, user2)

        await delivery_repo.save(delivery1)
        await delivery_repo.save(delivery2)
        await delivery_repo.save(delivery3)

        # Get deliveries for user1
        user1_deliveries = await delivery_repo.get_deliveries_for_user(user1_id)

        assert len(user1_deliveries) == 2
        delivery_ids = [delivery.id.value for delivery in user1_deliveries]
        assert "delivery-1" in delivery_ids
        assert "delivery-2" in delivery_ids
        assert "delivery-3" not in delivery_ids

    @pytest.mark.asyncio
    async def test_get_deliveries_by_status(self, delivery_repo, sample_delivery):
        """Test getting deliveries by status."""
        from app.domain.value_objects.delivery import DeliveryStatus

        await delivery_repo.save(sample_delivery)

        # Get deliveries by PENDING status (default)
        pending_deliveries = await delivery_repo.get_deliveries_by_status(
            DeliveryStatus.PENDING
        )

        assert len(pending_deliveries) >= 1
        delivery_ids = [delivery.id.value for delivery in pending_deliveries]
        assert "delivery-123" in delivery_ids


class TestTortoiseRepositories:
    """Test Tortoise ORM repositories."""

    @pytest.fixture
    def user_repo(self):
        """Create TortoiseUserRepository instance."""
        from app.infrastructure.repositories.tortoise_user_repository import (
            TortoiseUserRepository,
        )

        return TortoiseUserRepository()

    @pytest.fixture
    def notification_repo(self):
        """Create TortoiseNotificationRepository instance."""
        from app.infrastructure.repositories.tortoise_notification_repository import (
            TortoiseNotificationRepository,
        )

        return TortoiseNotificationRepository()

    @pytest.fixture
    def delivery_repo(self):
        """Create TortoiseDeliveryRepository instance."""
        from app.infrastructure.repositories.tortoise_delivery_repository import (
            TortoiseDeliveryRepository,
        )

        return TortoiseDeliveryRepository()


class TestRepositoryErrorHandling:
    """Test repository error handling scenarios."""

    @pytest.mark.asyncio
    async def test_memory_repo_concurrent_access(self):
        """Test concurrent access to memory repositories."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryUserRepository,
        )

        repo = InMemoryUserRepository()

        # Create multiple users concurrently
        users = [
            User(
                user_id=UserId(f"user-{i}"),
                name=UserName(f"User {i}"),
                email=Email(f"user{i}@gmail.com"),
            )
            for i in range(10)
        ]

        # Save all users concurrently
        await asyncio.gather(*[repo.save(user) for user in users])

        # Verify all users were saved
        all_active = await repo.get_all_active()
        assert len(all_active) == 10

    @pytest.mark.asyncio
    async def test_tortoise_connection_error(self):
        """Test Tortoise ORM connection error handling."""
        from app.domain.value_objects.user import UserId
        from app.infrastructure.repositories.tortoise_user_repository import (
            TortoiseUserRepository,
        )
        from unittest.mock import patch

        # Mock connection error using patch
        with patch(
            "tortoise.models.Model.get_or_none",
            side_effect=Exception("Database connection failed"),
        ):
            repo = TortoiseUserRepository()

            # Should raise exception on database error
            with pytest.raises(Exception, match="Database connection failed"):
                await repo.get_by_id(UserId("user-123"))


def test_all_repositories_import():
    """Test that all repository implementations can be imported successfully."""
    from app.infrastructure.repositories.memory_repositories import (
        InMemoryDeliveryRepository,
        InMemoryNotificationRepository,
        InMemoryUserRepository,
    )
    from app.infrastructure.repositories.tortoise_user_repository import (
        TortoiseUserRepository,
    )
    from app.infrastructure.repositories.tortoise_notification_repository import (
        TortoiseNotificationRepository,
    )
    from app.infrastructure.repositories.tortoise_delivery_repository import (
        TortoiseDeliveryRepository,
    )

    # Basic instantiation test for memory repos
    user_repo = InMemoryUserRepository()
    notif_repo = InMemoryNotificationRepository()
    delivery_repo = InMemoryDeliveryRepository()

    assert all([user_repo, notif_repo, delivery_repo])

    # Tortoise repos can be imported
    assert all(
        [
            TortoiseUserRepository,
            TortoiseNotificationRepository,
            TortoiseDeliveryRepository,
        ]
    )


@pytest.mark.parametrize(
    "repo_type,expected_methods",
    [
        ("InMemoryUserRepository", ["save", "get_by_id", "get_all_active", "delete"]),
        (
            "InMemoryNotificationRepository",
            ["save", "get_by_id", "get_pending_notifications"],
        ),
        (
            "InMemoryDeliveryRepository",
            ["save", "get_by_id", "get_deliveries_for_user"],
        ),
    ],
)
def test_repository_interface_compliance(repo_type, expected_methods):
    """Test that repositories implement expected interface methods."""
    if repo_type == "InMemoryUserRepository":
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryUserRepository,
        )

        repo = InMemoryUserRepository()
    elif repo_type == "InMemoryNotificationRepository":
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryNotificationRepository,
        )

        repo = InMemoryNotificationRepository()
    elif repo_type == "InMemoryDeliveryRepository":
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryDeliveryRepository,
        )

        repo = InMemoryDeliveryRepository()

    for method_name in expected_methods:
        assert hasattr(repo, method_name)
        assert callable(getattr(repo, method_name))
