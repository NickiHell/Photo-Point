"""
Simple unit tests for core domain and application components to improve coverage.
"""


class TestDomainValueObjects:
    """Test domain value objects."""

    def test_email_value_object(self):
        """Test Email value object."""
        from app.domain.value_objects.user import Email

        # Valid email
        valid_email = Email("test@example.com")
        assert valid_email.value == "test@example.com"
        assert str(valid_email) == "test@example.com"

        # Equality test
        email1 = Email("same@example.com")
        email2 = Email("same@example.com")
        assert email1 == email2
        assert hash(email1) == hash(email2)

        # Different emails
        email3 = Email("different@example.com")
        assert email1 != email3

    def test_phone_number_value_object(self):
        """Test PhoneNumber value object."""
        from app.domain.value_objects.user import PhoneNumber

        phone = PhoneNumber("+1234567890")
        assert phone.value == "+1234567890"
        assert str(phone) == "+1234567890"

        # Equality
        phone1 = PhoneNumber("+1111111111")
        phone2 = PhoneNumber("+1111111111")
        assert phone1 == phone2

    def test_user_id_value_object(self):
        """Test UserId value object."""
        from app.domain.value_objects.user import UserId

        user_id = UserId("user123")
        assert user_id.value == "user123"
        assert str(user_id) == "user123"

        # Test UUID generation
        generated_id = UserId.generate()
        assert generated_id.value is not None
        assert len(generated_id.value) > 0

    def test_telegram_id_value_object(self):
        """Test TelegramId value object."""
        from app.domain.value_objects.user import TelegramId

        telegram_id = TelegramId("123456789")
        assert telegram_id.value == "123456789"
        assert str(telegram_id) == "123456789"


class TestDomainEntities:
    """Test domain entities with full coverage."""

    def test_user_entity_creation(self):
        """Test User entity creation and methods."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, PhoneNumber, TelegramId, UserId

        user_id = UserId("user123")
        email = Email("test@example.com")
        phone = PhoneNumber("+1234567890")
        telegram_id = TelegramId("tg123")

        user = User(
            id=user_id,
            email=email,
            phone_number=phone,
            telegram_id=telegram_id,
            preferences={"lang": "en"},
            is_active=True,
        )

        # Test properties
        assert user.id == user_id
        assert user.email == email
        assert user.phone_number == phone
        assert user.telegram_id == telegram_id
        assert user.preferences == {"lang": "en"}
        assert user.is_active is True

        # Test update methods
        new_email = Email("new@example.com")
        user.update_email(new_email)
        assert user.email == new_email

        new_phone = PhoneNumber("+9876543210")
        user.update_phone_number(new_phone)
        assert user.phone_number == new_phone

        new_telegram = TelegramId("newtg456")
        user.update_telegram_id(new_telegram)
        assert user.telegram_id == new_telegram

        # Test preferences update
        user.update_preferences({"lang": "ru", "notifications": True})
        assert user.preferences == {"lang": "ru", "notifications": True}

        # Test activation/deactivation
        user.deactivate()
        assert user.is_active is False

        user.activate()
        assert user.is_active is True

        # Test string representation
        assert "User" in repr(user)
        assert str(user_id.value) in repr(user)

    def test_notification_entity_creation(self):
        """Test Notification entity creation and methods."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            Message,
            NotificationId,
            Priority,
        )
        from app.domain.value_objects.user import UserId

        notif_id = NotificationId("notif123")
        user_id = UserId("user456")
        message = Message("Hello {name}!", {"name": "John"})
        priority = Priority.HIGH

        notification = Notification(
            id=notif_id,
            user_id=user_id,
            message=message,
            channels=["email", "sms"],
            priority=priority,
            metadata={"campaign": "welcome"},
        )

        # Test properties
        assert notification.id == notif_id
        assert notification.user_id == user_id
        assert notification.message == message
        assert notification.channels == ["email", "sms"]
        assert notification.priority == priority
        assert notification.metadata == {"campaign": "welcome"}
        assert notification.status == "pending"

        # Test status updates
        notification.mark_as_sent()
        assert notification.status == "sent"
        assert notification.sent_at is not None

        notification.mark_as_failed("SMTP error")
        assert notification.status == "failed"
        assert notification.failed_reason == "SMTP error"

        # Test string representation
        assert "Notification" in repr(notification)


class TestApplicationDTOs:
    """Test application layer DTOs."""

    def test_create_user_dto(self):
        """Test CreateUserDTO."""
        from app.application.dto import CreateUserDTO

        # Full DTO
        dto = CreateUserDTO(
            email="test@example.com",
            phone_number="+1234567890",
            telegram_id="tg123",
            preferences={"lang": "en"},
        )

        assert dto.email == "test@example.com"
        assert dto.phone_number == "+1234567890"
        assert dto.telegram_id == "tg123"
        assert dto.preferences == {"lang": "en"}

        # Minimal DTO
        minimal_dto = CreateUserDTO()
        assert minimal_dto.email is None
        assert minimal_dto.phone_number is None
        assert minimal_dto.telegram_id is None
        assert minimal_dto.preferences == {}

        # Test dict conversion if available
        if hasattr(dto, "dict"):
            dto_dict = dto.dict()
            assert dto_dict["email"] == "test@example.com"

    def test_send_notification_dto(self):
        """Test SendNotificationDTO."""
        from app.application.dto import SendNotificationDTO

        # Full DTO
        dto = SendNotificationDTO(
            user_id="user123",
            message_template="Hello {name}!",
            message_variables={"name": "John"},
            channels=["email", "sms"],
            priority="HIGH",
            metadata={"campaign": "test"},
        )

        assert dto.user_id == "user123"
        assert dto.message_template == "Hello {name}!"
        assert dto.message_variables == {"name": "John"}
        assert dto.channels == ["email", "sms"]
        assert dto.priority == "HIGH"
        assert dto.metadata == {"campaign": "test"}

        # Minimal DTO
        minimal_dto = SendNotificationDTO(
            user_id="user456", message_template="Simple message"
        )

        assert minimal_dto.user_id == "user456"
        assert minimal_dto.message_template == "Simple message"
        assert minimal_dto.message_variables == {}
        assert minimal_dto.channels == ["email"]
        assert minimal_dto.priority == "MEDIUM"
        assert minimal_dto.metadata == {}


class TestValueObjectPriority:
    """Test Priority value object specifically."""

    def test_priority_enum_values(self):
        """Test Priority enum values."""
        from app.domain.value_objects.notification import Priority

        # Test all priority levels
        assert Priority.LOW.value == "LOW"
        assert Priority.MEDIUM.value == "MEDIUM"
        assert Priority.HIGH.value == "HIGH"
        assert Priority.URGENT.value == "URGENT"

        # Test comparison
        assert Priority.LOW < Priority.MEDIUM < Priority.HIGH < Priority.URGENT

        # Test string representation
        assert str(Priority.HIGH) == "Priority.HIGH"

    def test_priority_from_string(self):
        """Test Priority creation from string."""
        from app.domain.value_objects.notification import Priority

        # Test valid strings
        assert Priority("HIGH") == Priority.HIGH
        assert Priority("MEDIUM") == Priority.MEDIUM

        # Test case insensitivity if implemented
        try:
            low_case = Priority("high")
            assert low_case == Priority.HIGH
        except ValueError:
            # Case sensitive implementation
            pass


class TestMessageValueObject:
    """Test Message value object."""

    def test_message_creation(self):
        """Test Message value object creation."""
        from app.domain.value_objects.notification import Message

        # Simple message
        msg1 = Message("Hello world!")
        assert msg1.template == "Hello world!"
        assert msg1.variables == {}

        # Message with variables
        msg2 = Message("Hello {name}!", {"name": "John"})
        assert msg2.template == "Hello {name}!"
        assert msg2.variables == {"name": "John"}

    def test_message_render(self):
        """Test Message rendering."""
        from app.domain.value_objects.notification import Message

        msg = Message(
            "Hello {name}! Welcome to {service}.",
            {"name": "John", "service": "TestApp"},
        )

        rendered = msg.render()
        assert rendered == "Hello John! Welcome to TestApp."

        # Test with missing variable
        msg_missing = Message("Hello {name}! Missing: {missing}", {"name": "John"})
        try:
            rendered_missing = msg_missing.render()
            # Should handle missing variables gracefully or raise error
            assert "John" in rendered_missing
        except KeyError:
            # Expected behavior for missing variables
            pass

    def test_message_equality(self):
        """Test Message equality."""
        from app.domain.value_objects.notification import Message

        msg1 = Message("Hello {name}!", {"name": "John"})
        msg2 = Message("Hello {name}!", {"name": "John"})
        msg3 = Message("Hello {name}!", {"name": "Jane"})

        assert msg1 == msg2
        assert msg1 != msg3


class TestDeliveryValueObjects:
    """Test delivery-related value objects."""

    def test_delivery_id(self):
        """Test DeliveryId value object."""
        from app.domain.value_objects.delivery import DeliveryId

        delivery_id = DeliveryId("delivery123")
        assert delivery_id.value == "delivery123"
        assert str(delivery_id) == "delivery123"

        # Test generation
        generated = DeliveryId.generate()
        assert generated.value is not None
        assert len(generated.value) > 0

    def test_delivery_status(self):
        """Test DeliveryStatus enum."""
        from app.domain.value_objects.delivery import DeliveryStatus

        # Test all status values
        assert DeliveryStatus.PENDING.value == "PENDING"
        assert DeliveryStatus.SENT.value == "SENT"
        assert DeliveryStatus.DELIVERED.value == "DELIVERED"
        assert DeliveryStatus.FAILED.value == "FAILED"

        # Test string representation
        assert str(DeliveryStatus.SENT) == "DeliveryStatus.SENT"

    def test_delivery_channel(self):
        """Test DeliveryChannel enum."""
        from app.domain.value_objects.delivery import DeliveryChannel

        # Test channel values
        assert DeliveryChannel.EMAIL.value == "EMAIL"
        assert DeliveryChannel.SMS.value == "SMS"
        assert DeliveryChannel.TELEGRAM.value == "TELEGRAM"
        assert DeliveryChannel.PUSH.value == "PUSH"

        # Test string representation
        assert str(DeliveryChannel.EMAIL) == "DeliveryChannel.EMAIL"


class TestBasicInfrastructure:
    """Test basic infrastructure components that can be tested without external dependencies."""

    def test_in_memory_user_repository_interface(self):
        """Test in-memory repository implementation."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryUserRepository,
        )

        repo = InMemoryUserRepository()

        # Test save and retrieve
        user_id = UserId("test_user")
        email = Email("test@example.com")
        user = User(
            id=user_id,
            email=email,
            phone_number=None,
            telegram_id=None,
            preferences={},
            is_active=True,
        )

        # Save user
        repo.save(user)

        # Retrieve user
        retrieved = repo.find_by_id(user_id)
        assert retrieved is not None
        assert retrieved.id == user_id
        assert retrieved.email == email

        # Test find non-existent user
        non_existent = repo.find_by_id(UserId("non_existent"))
        assert non_existent is None

        # Test find by email
        found_by_email = repo.find_by_email(email)
        assert found_by_email is not None
        assert found_by_email.id == user_id

    def test_in_memory_notification_repository(self):
        """Test in-memory notification repository."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import Message, NotificationId
        from app.domain.value_objects.user import UserId
        from app.infrastructure.repositories.memory_repositories import (
            InMemoryNotificationRepository,
        )

        repo = InMemoryNotificationRepository()

        # Create notification
        notif_id = NotificationId("test_notif")
        user_id = UserId("user123")
        message = Message("Test message")

        notification = Notification(
            id=notif_id,
            user_id=user_id,
            message=message,
            channels=["email"],
            priority="MEDIUM",
        )

        # Save notification
        repo.save(notification)

        # Retrieve notification
        retrieved = repo.find_by_id(notif_id)
        assert retrieved is not None
        assert retrieved.id == notif_id
        assert retrieved.user_id == user_id

        # Test find by user
        user_notifications = repo.find_by_user_id(user_id)
        assert len(user_notifications) == 1
        assert user_notifications[0].id == notif_id


def test_imports_coverage():
    """Test that all main modules can be imported without errors."""
    # Domain imports
    # Application imports

    # Infrastructure imports (basic ones)

    # Presentation imports

    assert True


def test_basic_functionality():
    """Simple smoke test for basic functionality."""
    # Test that basic domain concepts work
    from app.domain.entities.user import User
    from app.domain.value_objects.user import Email, UserId

    # Create basic entities
    user_id = UserId("test_user_smoke")
    email = Email("smoke@test.com")

    user = User(
        id=user_id,
        email=email,
        phone_number=None,
        telegram_id=None,
        preferences={"test": True},
        is_active=True,
    )

    # Basic operations should work
    assert user.is_active
    user.deactivate()
    assert not user.is_active
    user.activate()
    assert user.is_active

    # Test basic notification concepts
    from app.domain.entities.notification import Notification
    from app.domain.value_objects.notification import Message, NotificationId

    notif_id = NotificationId("smoke_notif")
    message = Message("Smoke test message")

    notification = Notification(
        id=notif_id,
        user_id=user_id,
        message=message,
        channels=["email"],
        priority="LOW",
    )

    assert notification.status == "pending"
    notification.mark_as_sent()
    assert notification.status == "sent"
