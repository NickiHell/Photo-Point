"""
SQLAlchemy repository implementations for PostgreSQL persistence.
"""

from datetime import datetime, timedelta

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.delivery import Delivery
from ...domain.entities.notification import Notification
from ...domain.entities.user import User
from ...domain.repositories import (
    DeliveryRepository,
    NotificationRepository,
    UserRepository,
)
from ...domain.value_objects.delivery import DeliveryId, DeliveryStatus
from ...domain.value_objects.notification import (
    MessageTemplate,
    NotificationId,
    NotificationPriority,
)
from ...domain.value_objects.user import (
    Email,
    PhoneNumber,
    TelegramChatId,
    UserId,
    UserName,
)
from .models import DeliveryModel, NotificationModel, UserModel


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _model_to_entity(self, model: UserModel) -> User:
        """Convert UserModel to User entity."""
        # Create a fake name from email or ID since name is required but not in the model
        name_value = str(model.email) if model.email else f"user_{model.id}"
        return User(
            user_id=UserId(str(model.id)),  # type: ignore[arg-type]
            name=UserName(name_value),  # type: ignore[arg-type]
            email=Email(str(model.email)) if model.email else None,  # type: ignore[arg-type]
            phone=PhoneNumber(str(model.phone_number)) if model.phone_number else None,  # type: ignore[arg-type]
            telegram_chat_id=TelegramChatId(str(model.telegram_id)) if model.telegram_id else None,  # type: ignore[arg-type]
            is_active=bool(model.is_active),  # type: ignore[arg-type]
        )

    def _entity_to_model(self, entity: User) -> UserModel:
        """Convert User entity to UserModel."""
        return UserModel(
            id=entity.id.value,
            email=str(entity.email.value) if entity.email else None,
            phone_number=str(entity.phone.value) if entity.phone else None,
            telegram_id=str(entity.telegram_chat_id.value) if entity.telegram_chat_id else None,
            is_active=entity.is_active,
        )

    async def save(self, user: User) -> None:
        """Save user entity."""
        stmt = select(UserModel).where(UserModel.id == user.id.value)
        result = await self.session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Update existing user
            existing_user.email = str(user.email.value) if user.email else None  # type: ignore[assignment]
            existing_user.phone_number = str(user.phone.value) if user.phone else None  # type: ignore[assignment]
            existing_user.telegram_id = str(user.telegram_chat_id.value) if user.telegram_chat_id else None  # type: ignore[assignment]
            existing_user.is_active = user.is_active  # type: ignore[assignment]
            existing_user.preferences = user.preferences  # type: ignore[assignment]
        else:
            # Create new user
            new_user = self._entity_to_model(user)
            self.session.add(new_user)

        await self.session.commit()

    async def get_by_id(self, user_id: UserId) -> User | None:
        """Get user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def get_all_active(self) -> list[User]:
        """Get all active users."""
        stmt = select(UserModel).where(UserModel.is_active)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def delete(self, user_id: UserId) -> None:
        """Delete user by ID."""
        stmt = delete(UserModel).where(UserModel.id == user_id.value)
        await self.session.execute(stmt)
        await self.session.commit()


class SQLAlchemyNotificationRepository(NotificationRepository):
    """SQLAlchemy implementation of NotificationRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _model_to_entity(self, model: NotificationModel) -> Notification:
        """Convert NotificationModel to Notification entity."""
        # Ensure scheduled_at is a datetime or None
        scheduled_at = model.scheduled_at if isinstance(model.scheduled_at, datetime) else None
        return Notification(
            notification_id=NotificationId(str(model.id)),
            recipient_id=UserId(str(model.recipient_id)),
            message_template=MessageTemplate(template=str(model.message_template)),
            priority=NotificationPriority(str(model.priority)),
            scheduled_at=scheduled_at,
            metadata=dict(model.notification_metadata) if model.notification_metadata else {},
        )

    def _entity_to_model(self, entity: Notification) -> NotificationModel:
        """Convert Notification entity to NotificationModel."""
        return NotificationModel(  # type: ignore[call-arg]
            id=entity.id.value,
            recipient_id=entity.recipient_id.value,
            message_template=entity.message_template.template,
            message_variables={},  # MessageTemplate doesn't have variables anymore
            channels=[],  # Channels are handled separately
            priority=entity.priority.value,
            scheduled_at=entity.scheduled_at,
            retry_policy={},  # Default empty retry policy
            notification_metadata=entity.metadata or {},
        )

    async def save(self, notification: Notification) -> None:
        """Save notification entity."""
        stmt = select(NotificationModel).where(
            NotificationModel.id == notification.id.value
        )
        result = await self.session.execute(stmt)
        existing_notification = result.scalar_one_or_none()

        if existing_notification:
            # Update existing notification
            existing_notification.message_template = notification.message_template.template  # type: ignore[assignment]
            existing_notification.message_variables = {}  # type: ignore[assignment]
            existing_notification.channels = []  # type: ignore[assignment]
            existing_notification.priority = notification.priority.value  # type: ignore[assignment]
            existing_notification.scheduled_at = notification.scheduled_at  # type: ignore[assignment]
            existing_notification.retry_policy = {}  # type: ignore[assignment]
            existing_notification.notification_metadata = notification.metadata or {}  # type: ignore[assignment]
        else:
            # Create new notification
            new_notification = self._entity_to_model(notification)
            self.session.add(new_notification)

        await self.session.commit()

    async def get_by_id(self, notification_id: NotificationId) -> Notification | None:
        """Get notification by ID."""
        stmt = select(NotificationModel).where(
            NotificationModel.id == notification_id.value
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def get_pending(self, limit: int | None = None) -> list[Notification]:
        """Get pending notifications ready to be sent."""
        now = datetime.utcnow()
        stmt = (
            select(NotificationModel)
            .where(
                and_(
                    NotificationModel.scheduled_at <= now,
                    NotificationModel.sent_at.is_(None),
                )
            )
            .order_by(NotificationModel.priority, NotificationModel.scheduled_at)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def get_by_recipient(self, recipient_id: UserId) -> list[Notification]:
        """Get notifications for specific recipient."""
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.recipient_id == recipient_id.value)
            .order_by(NotificationModel.created_at.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def delete(self, notification_id: NotificationId) -> None:
        """Delete notification by ID."""
        stmt = delete(NotificationModel).where(
            NotificationModel.id == notification_id.value
        )
        await self.session.execute(stmt)
        await self.session.commit()


class SQLAlchemyDeliveryRepository(DeliveryRepository):
    """SQLAlchemy implementation of DeliveryRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _model_to_entity(self, model: DeliveryModel) -> Delivery:
        """Convert DeliveryModel to Delivery entity."""
        # Convert related notification
        notification = SQLAlchemyNotificationRepository(self.session)._model_to_entity(model.notification)
        # Create a dummy user (since we don't have user info in DeliveryModel)
        dummy_user = User(
            user_id=UserId("dummy"),
            name=UserName("Dummy User"),
            email=None,
            phone=None,
            telegram_chat_id=None,
            is_active=True,
        )
        delivery = Delivery(
            delivery_id=DeliveryId(str(model.id)),
            notification=notification,
            user=dummy_user,
        )
        return delivery

    async def save(self, delivery: Delivery) -> None:
        """Save delivery entity."""
        stmt = select(DeliveryModel).where(DeliveryModel.id == delivery.id.value)
        result = await self.session.execute(stmt)
        existing_delivery = result.scalar_one_or_none()

        # Extract channel and provider from attempts if available, else use defaults
        channel = None
        provider = None
        if delivery.attempts:
            channel = str(delivery.attempts[-1].channel)
            provider = delivery.attempts[-1].provider
        else:
            channel = "unknown"
            provider = "unknown"

        if existing_delivery:
            # Update existing delivery
            existing_delivery.status = delivery.status.value  # type: ignore[assignment]
            existing_delivery.completed_at = delivery.completed_at  # type: ignore[assignment]
            existing_delivery.channel = channel  # type: ignore[assignment]
            existing_delivery.provider = provider  # type: ignore[assignment]
        else:
            # Create new delivery
            new_delivery = DeliveryModel(  # type: ignore[call-arg]
                id=delivery.id.value,
                notification_id=delivery.notification.id.value,
                channel=channel,
                provider=provider,
                status=delivery.status.value,
                created_at=delivery.started_at or delivery.completed_at or datetime.utcnow(),
                completed_at=delivery.completed_at,
            )
            self.session.add(new_delivery)

        # Handle delivery attempts (not implemented)
        await self.session.commit()

    async def get_by_id(self, delivery_id: DeliveryId) -> Delivery | None:
        """Get delivery by ID."""
        stmt = (
            select(DeliveryModel)
            .options(selectinload(DeliveryModel.notification))
            .options(selectinload(DeliveryModel.attempts))
            .where(DeliveryModel.id == delivery_id.value)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def get_by_notification(
        self, notification_id: NotificationId
    ) -> list[Delivery]:
        """Get deliveries for specific notification."""
        stmt = (
            select(DeliveryModel)
            .options(selectinload(DeliveryModel.notification))
            .options(selectinload(DeliveryModel.attempts))
            .where(DeliveryModel.notification_id == notification_id.value)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def get_pending_retries(self) -> list[Delivery]:
        """Get deliveries that need to be retried."""
        stmt = (
            select(DeliveryModel)
            .options(selectinload(DeliveryModel.notification))
            .options(selectinload(DeliveryModel.attempts))
            .where(DeliveryModel.status == DeliveryStatus.RETRYING.value)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def get_statistics(self, days: int = 7) -> dict:
        """Get delivery statistics for the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Basic statistics query
        stmt = select(DeliveryModel).where(DeliveryModel.created_at >= cutoff_date)
        result = await self.session.execute(stmt)
        recent_deliveries = result.scalars().all()

        total_deliveries = len(recent_deliveries)
        successful_deliveries = len(
            [d for d in recent_deliveries if d.status == DeliveryStatus.DELIVERED.value]
        )
        failed_deliveries = len(
            [d for d in recent_deliveries if d.status == DeliveryStatus.FAILED.value]
        )
        pending_deliveries = len(
            [
                d
                for d in recent_deliveries
                if d.status
                in [
                    DeliveryStatus.PENDING.value,
                    DeliveryStatus.SENT.value,
                    DeliveryStatus.RETRYING.value,
                ]
            ]
        )

        # Provider statistics
        provider_stats = {}
        for delivery in recent_deliveries:
            provider = delivery.provider
            if provider not in provider_stats:
                provider_stats[provider] = {"total": 0, "successful": 0}
            provider_stats[provider]["total"] += 1
            if delivery.status == DeliveryStatus.DELIVERED.value:
                provider_stats[provider]["successful"] += 1

        return {
            "period_days": days,
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": failed_deliveries,
            "pending_deliveries": pending_deliveries,
            "success_rate": (successful_deliveries / total_deliveries * 100)
            if total_deliveries > 0
            else 0,
            "provider_statistics": provider_stats,
        }
