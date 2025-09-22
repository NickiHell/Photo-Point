"""
Tests for Tortoise ORM repositories.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tortoise import Tortoise
from tortoise.contrib.test import finalizer, initializer

from app.domain.entities.delivery import Delivery
from app.domain.entities.notification import Notification
from app.domain.entities.user import User
from app.domain.value_objects.delivery import DeliveryId
from app.domain.value_objects.notification import NotificationId, NotificationPriority
from app.domain.value_objects.user import Email, PhoneNumber, TelegramChatId, UserId
from app.infrastructure.repositories.tortoise_delivery_repository import (
    TortoiseDeliveryRepository,
)
from app.infrastructure.repositories.tortoise_notification_repository import (
    TortoiseNotificationRepository,
)
from app.infrastructure.repositories.tortoise_user_repository import (
    TortoiseUserRepository,
)


@pytest.fixture(scope="module")
def event_loop() -> Generator:
    """Create an event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def initialize_tests() -> None:
    """Initialize the test database for Tortoise ORM."""
    initializer(
        ["app.infrastructure.repositories.tortoise_models"], db_url="sqlite://:memory:"
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()
    finalizer()


class TestTortoiseRepositories:
    """Test Tortoise ORM repositories."""

    @pytest.fixture
    def user_repo(self) -> TortoiseUserRepository:
        """Create TortoiseUserRepository for testing."""
        return TortoiseUserRepository()

    @pytest.fixture
    def notification_repo(self) -> TortoiseNotificationRepository:
        """Create TortoiseNotificationRepository for testing."""
        return TortoiseNotificationRepository()

    @pytest.fixture
    def delivery_repo(self) -> TortoiseDeliveryRepository:
        """Create TortoiseDeliveryRepository for testing."""
        return TortoiseDeliveryRepository()

    @pytest.fixture
    def sample_user(self) -> User:
        """Create a sample user for testing."""
        return User(
            id=UserId("user-123"),
            email=Email("test@example.com"),
            phone_number=PhoneNumber("+12345678901"),
            telegram_id=TelegramChatId("123456789"),
            is_active=True,
            preferences={"theme": "dark"},
        )

    @pytest.fixture
    def sample_notification(self, sample_user: User) -> Notification:
        """Create a sample notification for testing."""
        from app.domain.entities.notification import NotificationType
        from app.domain.value_objects.delivery import RetryPolicy
        from app.domain.value_objects.notification import MessageTemplate

        return Notification(
            id=NotificationId("notif-123"),
            recipient_id=sample_user.id,
            message=MessageTemplate(
                content="Hello {name}!",
                template_data={"name": "John"},
            ),
            channels=[NotificationType.EMAIL, NotificationType.SMS],
            priority=NotificationPriority.HIGH,
            scheduled_at=datetime.utcnow(),
            sent_at=None,
            retry_policy=RetryPolicy(max_retries=3, delay=60),
            metadata={"campaign_id": "welcome-123"},
        )

    @pytest.mark.asyncio
    async def test_user_save(
        self, user_repo: TortoiseUserRepository, sample_user: User
    ) -> None:
        """Test saving a user using the Tortoise repository."""
        saved_user = await user_repo.save(sample_user)

        assert saved_user is not None
        assert saved_user.id == sample_user.id
        assert saved_user.email == sample_user.email
        assert saved_user.phone_number == sample_user.phone_number
        assert saved_user.telegram_id == sample_user.telegram_id
        assert saved_user.is_active == sample_user.is_active
        assert saved_user.preferences == sample_user.preferences

    @pytest.mark.asyncio
    async def test_user_get_by_id(
        self, user_repo: TortoiseUserRepository, sample_user: User
    ) -> None:
        """Test getting a user by ID using the Tortoise repository."""
        await user_repo.save(sample_user)

        retrieved_user = await user_repo.get_by_id(sample_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == sample_user.id
        assert retrieved_user.email == sample_user.email

    @pytest.mark.asyncio
    async def test_user_get_by_email(
        self, user_repo: TortoiseUserRepository, sample_user: User
    ) -> None:
        """Test getting a user by email using the Tortoise repository."""
        await user_repo.save(sample_user)

        retrieved_user = await user_repo.get_by_email(sample_user.email)

        assert retrieved_user is not None
        assert retrieved_user.id == sample_user.id
        assert retrieved_user.email == sample_user.email

    @pytest.mark.asyncio
    async def test_notification_save(
        self,
        notification_repo: TortoiseNotificationRepository,
        sample_notification: Notification,
    ) -> None:
        """Test saving a notification using the Tortoise repository."""
        saved_notification = await notification_repo.save(sample_notification)

        assert saved_notification is not None
        assert saved_notification.id == sample_notification.id
        assert saved_notification.recipient_id == sample_notification.recipient_id
        assert saved_notification.priority == sample_notification.priority

    @pytest.mark.asyncio
    async def test_notification_get_by_id(
        self,
        notification_repo: TortoiseNotificationRepository,
        sample_notification: Notification,
    ) -> None:
        """Test getting a notification by ID using the Tortoise repository."""
        await notification_repo.save(sample_notification)

        retrieved_notification = await notification_repo.get_by_id(
            sample_notification.id
        )

        assert retrieved_notification is not None
        assert retrieved_notification.id == sample_notification.id
        assert retrieved_notification.recipient_id == sample_notification.recipient_id
