"""
Comprehensive tests for all Domain Entities to maximize coverage.
"""
from datetime import UTC, datetime, timedelta


class TestUserEntity:
    """Test User Entity comprehensively."""

    def test_user_creation_minimal(self):
        """Test User creation with minimal required data."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")

        user = User(user_id=user_id, name=name, email=email)

        assert user.id == user_id
        assert user.name == name
        assert user.email == email
        assert user.phone is None
        assert user.telegram_chat_id is None
        assert user.is_active is True
        assert user.preferences == set()

    def test_user_creation_full(self):
        """Test User creation with all data."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import (
            Email,
            PhoneNumber,
            TelegramChatId,
            UserId,
            UserName,
        )

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")
        phone = PhoneNumber("+1234567890")
        telegram_id = TelegramChatId(123456789)

        user = User(
            user_id=user_id,
            name=name,
            email=email,
            phone=phone,
            telegram_chat_id=telegram_id,
            is_active=False
        )

        assert user.id == user_id
        assert user.name == name
        assert user.email == email
        assert user.phone == phone
        assert user.telegram_chat_id == telegram_id
        assert user.is_active is False

    def test_user_update_name(self):
        """Test updating user name."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        user_id = UserId("user-1")
        original_name = UserName("John Doe")
        new_name = UserName("Jane Doe")
        email = Email("john@gmail.com")

        user = User(user_id=user_id, name=original_name, email=email)
        user.update_name(new_name)

        assert user.name == new_name

    def test_user_update_email(self):
        """Test updating user email."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        user_id = UserId("user-1")
        name = UserName("John Doe")
        original_email = Email("john@gmail.com")
        new_email = Email("jane@gmail.com")

        user = User(user_id=user_id, name=name, email=original_email)
        user.update_email(new_email)

        assert user.email == new_email

    def test_user_update_phone(self):
        """Test updating user phone."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, PhoneNumber, UserId, UserName

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")
        phone = PhoneNumber("+1234567890")

        user = User(user_id=user_id, name=name, email=email)
        user.update_phone(phone)

        assert user.phone == phone

    def test_user_update_telegram(self):
        """Test updating user telegram chat ID."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import (
            Email,
            TelegramChatId,
            UserId,
            UserName,
        )

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")
        telegram_id = TelegramChatId(123456789)

        user = User(user_id=user_id, name=name, email=email)
        user.update_telegram_chat_id(telegram_id)

        assert user.telegram_chat_id == telegram_id

    def test_user_activate_deactivate(self):
        """Test user activation and deactivation."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")

        user = User(user_id=user_id, name=name, email=email, is_active=False)
        assert user.is_active is False

        user.activate()
        assert user.is_active is True

        user.deactivate()
        assert user.is_active is False

    def test_user_preferences_management(self):
        """Test user preferences management."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")

        user = User(user_id=user_id, name=name, email=email)

        # Add preferences
        user.add_preference("email")
        user.add_preference("sms")
        assert "email" in user.preferences
        assert "sms" in user.preferences
        assert len(user.preferences) == 2

        # Remove preference
        user.remove_preference("email")
        assert "email" not in user.preferences
        assert "sms" in user.preferences
        assert len(user.preferences) == 1

        # Add duplicate (should not increase count)
        user.add_preference("sms")
        assert len(user.preferences) == 1

    def test_user_available_channels(self):
        """Test getting available notification channels."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import (
            Email,
            PhoneNumber,
            TelegramChatId,
            UserId,
            UserName,
        )

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")
        phone = PhoneNumber("+1234567890")
        telegram_id = TelegramChatId(123456789)

        user = User(
            user_id=user_id,
            name=name,
            email=email,
            phone=phone,
            telegram_chat_id=telegram_id
        )

        channels = user.get_available_channels()
        assert "email" in channels
        assert "sms" in channels
        assert "telegram" in channels
        assert len(channels) == 3

    def test_user_available_channels_partial(self):
        """Test getting available channels with partial contact info."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")

        user = User(user_id=user_id, name=name, email=email)

        channels = user.get_available_channels()
        assert "email" in channels
        assert "sms" not in channels
        assert "telegram" not in channels
        assert len(channels) == 1

    def test_user_can_receive_notifications(self):
        """Test checking if user can receive notifications."""
        from app.domain.entities.user import User
        from app.domain.value_objects.user import Email, UserId, UserName

        user_id = UserId("user-1")
        name = UserName("John Doe")
        email = Email("john@gmail.com")

        # Active user with contact info can receive
        user = User(user_id=user_id, name=name, email=email, is_active=True)
        assert user.can_receive_notifications() is True

        # Inactive user cannot receive
        user.deactivate()
        assert user.can_receive_notifications() is False

        # Active user without contact info cannot receive
        user_no_contact = User(user_id=user_id, name=name, is_active=True)
        assert user_no_contact.can_receive_notifications() is False


class TestNotificationEntity:
    """Test Notification Entity comprehensively."""

    def test_notification_creation_minimal(self):
        """Test Notification creation with minimal data."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
            NotificationPriority,
        )
        from app.domain.value_objects.user import UserId

        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")
        template = MessageTemplate("subject", "Hello {name}!")

        notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template
        )

        assert notification.id == notification_id
        assert notification.recipient_id == recipient_id
        assert notification.message_template == template
        assert notification.priority == NotificationPriority.NORMAL
        assert notification.scheduled_at is not None
        assert notification.expires_at is None
        assert notification.metadata == {}
        assert notification.is_cancelled is False

    def test_notification_creation_full(self):
        """Test Notification creation with all data."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
            NotificationPriority,
        )
        from app.domain.value_objects.user import UserId

        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")
        template = MessageTemplate("subject", "Hello {name}!")
        priority = NotificationPriority.HIGH
        scheduled_at = datetime.now(UTC) + timedelta(hours=1)
        expires_at = datetime.now(UTC) + timedelta(days=1)
        metadata = {"source": "api", "campaign": "welcome"}

        notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template,
            priority=priority,
            scheduled_at=scheduled_at,
            expires_at=expires_at,
            metadata=metadata
        )

        assert notification.id == notification_id
        assert notification.recipient_id == recipient_id
        assert notification.message_template == template
        assert notification.priority == priority
        assert notification.scheduled_at == scheduled_at
        assert notification.expires_at == expires_at
        assert notification.metadata == metadata

    def test_notification_render_message(self):
        """Test notification message rendering."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
        )
        from app.domain.value_objects.user import UserId

        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")
        template = MessageTemplate("Welcome", "Hello {name}! Welcome to {platform}!")

        notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template
        )

        rendered = notification.render_message(name="John", platform="MyApp")
        assert rendered.subject == "Welcome"
        assert rendered.content == "Hello John! Welcome to MyApp!"

    def test_notification_is_ready_to_send(self):
        """Test checking if notification is ready to send."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
        )
        from app.domain.value_objects.user import UserId

        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")
        template = MessageTemplate("subject", "content")

        # Future scheduled notification is not ready
        future_time = datetime.now(UTC) + timedelta(hours=1)
        future_notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template,
            scheduled_at=future_time
        )
        assert future_notification.is_ready_to_send() is False

        # Past scheduled notification is ready
        past_time = datetime.now(UTC) - timedelta(hours=1)
        past_notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template,
            scheduled_at=past_time
        )
        assert past_notification.is_ready_to_send() is True

        # Cancelled notification is not ready
        past_notification.cancel()
        assert past_notification.is_ready_to_send() is False

    def test_notification_is_expired(self):
        """Test checking if notification is expired."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
        )
        from app.domain.value_objects.user import UserId

        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")
        template = MessageTemplate("subject", "content")

        # No expiry - not expired
        no_expiry = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template
        )
        assert no_expiry.is_expired() is False

        # Future expiry - not expired
        future_expiry = datetime.now(UTC) + timedelta(hours=1)
        future_notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template,
            expires_at=future_expiry
        )
        assert future_notification.is_expired() is False

        # Past expiry - expired
        past_expiry = datetime.now(UTC) - timedelta(hours=1)
        past_notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template,
            expires_at=past_expiry
        )
        assert past_notification.is_expired() is True

    def test_notification_cancel(self):
        """Test cancelling notification."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
        )
        from app.domain.value_objects.user import UserId

        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")
        template = MessageTemplate("subject", "content")

        notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template
        )

        assert notification.is_cancelled is False
        notification.cancel()
        assert notification.is_cancelled is True

    def test_notification_update_metadata(self):
        """Test updating notification metadata."""
        from app.domain.entities.notification import Notification
        from app.domain.value_objects.notification import (
            MessageTemplate,
            NotificationId,
        )
        from app.domain.value_objects.user import UserId

        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")
        template = MessageTemplate("subject", "content")

        notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            message_template=template,
            metadata={"key1": "value1"}
        )

        # Update existing key
        notification.update_metadata("key1", "new_value")
        assert notification.metadata["key1"] == "new_value"

        # Add new key
        notification.update_metadata("key2", "value2")
        assert notification.metadata["key2"] == "value2"
        assert len(notification.metadata) == 2


class TestDeliveryEntity:
    """Test Delivery Entity comprehensively."""

    def test_delivery_creation(self):
        """Test Delivery creation."""
        from app.domain.entities.delivery import Delivery
        from app.domain.value_objects.delivery import DeliveryId, DeliveryStatus
        from app.domain.value_objects.notification import NotificationId
        from app.domain.value_objects.user import UserId

        delivery_id = DeliveryId("delivery-1")
        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")

        delivery = Delivery(
            delivery_id=delivery_id,
            notification_id=notification_id,
            recipient_id=recipient_id,
            channel="email",
            provider="smtp"
        )

        assert delivery.id == delivery_id
        assert delivery.notification_id == notification_id
        assert delivery.recipient_id == recipient_id
        assert delivery.channel == "email"
        assert delivery.provider == "smtp"
        assert delivery.status == DeliveryStatus.PENDING
        assert delivery.attempts == []
        assert delivery.created_at is not None
        assert delivery.sent_at is None
        assert delivery.delivered_at is None

    def test_delivery_attempt_success(self):
        """Test successful delivery attempt."""
        from app.domain.entities.delivery import Delivery
        from app.domain.value_objects.delivery import DeliveryId, DeliveryStatus
        from app.domain.value_objects.notification import NotificationId
        from app.domain.value_objects.user import UserId

        delivery_id = DeliveryId("delivery-1")
        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")

        delivery = Delivery(
            delivery_id=delivery_id,
            notification_id=notification_id,
            recipient_id=recipient_id,
            channel="email",
            provider="smtp"
        )

        # Successful attempt
        delivery.add_attempt(
            success=True,
            response="Email sent successfully",
            provider_message_id="msg-123"
        )

        assert delivery.status == DeliveryStatus.SENT
        assert len(delivery.attempts) == 1
        assert delivery.attempts[0].success is True
        assert delivery.attempts[0].response == "Email sent successfully"
        assert delivery.attempts[0].provider_message_id == "msg-123"
        assert delivery.sent_at is not None

    def test_delivery_attempt_failure(self):
        """Test failed delivery attempt."""
        from app.domain.entities.delivery import Delivery
        from app.domain.value_objects.delivery import (
            DeliveryError,
            DeliveryId,
            DeliveryStatus,
        )
        from app.domain.value_objects.notification import NotificationId
        from app.domain.value_objects.user import UserId

        delivery_id = DeliveryId("delivery-1")
        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")

        delivery = Delivery(
            delivery_id=delivery_id,
            notification_id=notification_id,
            recipient_id=recipient_id,
            channel="email",
            provider="smtp"
        )

        # Failed attempt
        error = DeliveryError("TIMEOUT", "Connection timeout")
        delivery.add_attempt(
            success=False,
            response="Failed to send",
            error=error
        )

        assert delivery.status == DeliveryStatus.FAILED
        assert len(delivery.attempts) == 1
        assert delivery.attempts[0].success is False
        assert delivery.attempts[0].error == error
        assert delivery.sent_at is None

    def test_delivery_multiple_attempts(self):
        """Test multiple delivery attempts."""
        from app.domain.entities.delivery import Delivery
        from app.domain.value_objects.delivery import (
            DeliveryError,
            DeliveryId,
            DeliveryStatus,
        )
        from app.domain.value_objects.notification import NotificationId
        from app.domain.value_objects.user import UserId

        delivery_id = DeliveryId("delivery-1")
        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")

        delivery = Delivery(
            delivery_id=delivery_id,
            notification_id=notification_id,
            recipient_id=recipient_id,
            channel="email",
            provider="smtp"
        )

        # First attempt fails
        error1 = DeliveryError("TIMEOUT", "Connection timeout")
        delivery.add_attempt(success=False, response="Failed", error=error1)
        assert delivery.status == DeliveryStatus.FAILED
        assert len(delivery.attempts) == 1

        # Retry
        delivery.retry()
        assert delivery.status == DeliveryStatus.RETRYING

        # Second attempt succeeds
        delivery.add_attempt(success=True, response="Success", provider_message_id="msg-456")
        assert delivery.status == DeliveryStatus.SENT
        assert len(delivery.attempts) == 2
        assert delivery.attempts[1].success is True

    def test_delivery_mark_delivered(self):
        """Test marking delivery as delivered."""
        from app.domain.entities.delivery import Delivery
        from app.domain.value_objects.delivery import DeliveryId, DeliveryStatus
        from app.domain.value_objects.notification import NotificationId
        from app.domain.value_objects.user import UserId

        delivery_id = DeliveryId("delivery-1")
        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")

        delivery = Delivery(
            delivery_id=delivery_id,
            notification_id=notification_id,
            recipient_id=recipient_id,
            channel="email",
            provider="smtp"
        )

        # First mark as sent
        delivery.add_attempt(success=True, response="Sent")
        assert delivery.status == DeliveryStatus.SENT

        # Then mark as delivered
        delivery.mark_delivered("Delivered successfully")
        assert delivery.status == DeliveryStatus.DELIVERED
        assert delivery.delivered_at is not None

    def test_delivery_get_last_attempt(self):
        """Test getting last delivery attempt."""
        from app.domain.entities.delivery import Delivery
        from app.domain.value_objects.delivery import DeliveryId
        from app.domain.value_objects.notification import NotificationId
        from app.domain.value_objects.user import UserId

        delivery_id = DeliveryId("delivery-1")
        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")

        delivery = Delivery(
            delivery_id=delivery_id,
            notification_id=notification_id,
            recipient_id=recipient_id,
            channel="email",
            provider="smtp"
        )

        # No attempts yet
        assert delivery.get_last_attempt() is None

        # Add attempts
        delivery.add_attempt(success=False, response="First attempt failed")
        delivery.add_attempt(success=True, response="Second attempt success")

        last_attempt = delivery.get_last_attempt()
        assert last_attempt is not None
        assert last_attempt.success is True
        assert last_attempt.response == "Second attempt success"

    def test_delivery_is_final_state(self):
        """Test checking if delivery is in final state."""
        from app.domain.entities.delivery import Delivery
        from app.domain.value_objects.delivery import DeliveryId
        from app.domain.value_objects.notification import NotificationId
        from app.domain.value_objects.user import UserId

        delivery_id = DeliveryId("delivery-1")
        notification_id = NotificationId("notif-1")
        recipient_id = UserId("user-1")

        delivery = Delivery(
            delivery_id=delivery_id,
            notification_id=notification_id,
            recipient_id=recipient_id,
            channel="email",
            provider="smtp"
        )

        # PENDING is not final
        assert delivery.is_final_state() is False

        # SENT is not final
        delivery.add_attempt(success=True, response="Sent")
        assert delivery.is_final_state() is False

        # DELIVERED is final
        delivery.mark_delivered("Delivered")
        assert delivery.is_final_state() is True


def test_all_entities_import():
    """Test that all entities can be imported successfully."""
    from app.domain.entities.delivery import Delivery
    from app.domain.entities.notification import Notification
    from app.domain.entities.user import User
    from app.domain.value_objects.delivery import DeliveryId
    from app.domain.value_objects.notification import MessageTemplate, NotificationId
    from app.domain.value_objects.user import Email, UserId, UserName

    # Basic instantiation test
    user_id = UserId("test")
    user = User(user_id, UserName("Test"), Email("test@gmail.com"))

    notif_id = NotificationId("test")
    notification = Notification(notif_id, user_id, MessageTemplate("subject", "content"))

    delivery_id = DeliveryId("test")
    delivery = Delivery(delivery_id, notif_id, user_id, "email", "smtp")

    assert all([user, notification, delivery])
