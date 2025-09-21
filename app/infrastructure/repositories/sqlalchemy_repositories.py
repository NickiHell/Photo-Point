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
        name_value = model.email or f"user_{model.id}"

        return User(
            user_id=UserId(model.id),
            name=UserName(name_value),
            email=Email(model.email) if model.email else None,
            phone=PhoneNumber(model.phone_number) if model.phone_number else None,
            telegram_chat_id=TelegramChatId(model.telegram_id) if model.telegram_id else None,
            is_active=model.is_active
        )

    def _entity_to_model(self, entity: User) -> UserModel:
        """Convert User entity to UserModel."""
        return UserModel(
            id=entity.id.value,
            email=entity.email.value if entity.email else None,
            phone_number=entity.phone.value if entity.phone else None,
            telegram_id=entity.telegram_chat_id.value if entity.telegram_chat_id else None,
            is_active=entity.is_active
        )

    async def save(self, user: User) -> None:
        """Save user entity."""
        stmt = select(UserModel).where(UserModel.id == user.id.value)
        result = await self.session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Update existing user
            existing_user.email = user.email.value if user.email else None
            existing_user.phone_number = user.phone.value if user.phone else None
            existing_user.telegram_id = user.telegram_chat_id.value if user.telegram_chat_id else None
            existing_user.is_active = user.is_active
            existing_user.preferences = user.preferences
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
        return Notification(
            id=NotificationId(model.id),
            recipient_id=UserId(model.recipient_id),
            message=MessageTemplate(
                template=model.message_template,
                variables=model.message_variables or {}
            ),
            channels=model.channels,
            priority=NotificationPriority(model.priority),
            scheduled_at=model.scheduled_at,
            retry_policy=model.retry_policy,
            metadata=model.notification_metadata or {},
            created_at=model.created_at
        )

    def _entity_to_model(self, entity: Notification) -> NotificationModel:
        """Convert Notification entity to NotificationModel."""
        return NotificationModel(
            id=entity.id.value,
            recipient_id=entity.recipient_id.value,
            message_template=entity.message.template,
            message_variables=entity.message.variables,
            channels=entity.channels,
            priority=entity.priority.value,
            scheduled_at=entity.scheduled_at,
            retry_policy=entity.retry_policy,
            notification_metadata=entity.metadata,
            created_at=entity.created_at
        )

    async def save(self, notification: Notification) -> None:
        """Save notification entity."""
        stmt = select(NotificationModel).where(NotificationModel.id == notification.id.value)
        result = await self.session.execute(stmt)
        existing_notification = result.scalar_one_or_none()

        if existing_notification:
            # Update existing notification
            existing_notification.message_template = notification.message.template
            existing_notification.message_variables = notification.message.variables
            existing_notification.channels = notification.channels
            existing_notification.priority = notification.priority.value
            existing_notification.scheduled_at = notification.scheduled_at
            existing_notification.retry_policy = notification.retry_policy
            existing_notification.notification_metadata = notification.metadata
        else:
            # Create new notification
            new_notification = self._entity_to_model(notification)
            self.session.add(new_notification)

        await self.session.commit()

    async def get_by_id(self, notification_id: NotificationId) -> Notification | None:
        """Get notification by ID."""
        stmt = select(NotificationModel).where(NotificationModel.id == notification_id.value)
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
                    NotificationModel.sent_at.is_(None)
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
        stmt = delete(NotificationModel).where(NotificationModel.id == notification_id.value)
        await self.session.execute(stmt)
        await self.session.commit()


class SQLAlchemyDeliveryRepository(DeliveryRepository):
    """SQLAlchemy implementation of DeliveryRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _model_to_entity(self, model: DeliveryModel) -> Delivery:
        """Convert DeliveryModel to Delivery entity."""
        # First get the notification
        notification = Notification(
            id=NotificationId(model.notification.id),
            recipient_id=UserId(model.notification.recipient_id),
            message=MessageTemplate(
                template=model.notification.message_template,
                variables=model.notification.message_variables or {}
            ),
            channels=model.notification.channels,
            priority=NotificationPriority(model.notification.priority),
            scheduled_at=model.notification.scheduled_at,
            retry_policy=model.notification.retry_policy,
            metadata=model.notification.notification_metadata or {},
            created_at=model.notification.created_at
        )

        # Create delivery entity
        delivery = Delivery(
            id=DeliveryId(model.id),
            notification=notification,
            channel=model.channel,
            provider=model.provider,
            status=DeliveryStatus(model.status),
            created_at=model.created_at
        )

        # Add delivery attempts
        for attempt_model in model.attempts:
            delivery.attempts.append(attempt_model)

        return delivery

    async def save(self, delivery: Delivery) -> None:
        """Save delivery entity."""
        stmt = select(DeliveryModel).where(DeliveryModel.id == delivery.id.value)
        result = await self.session.execute(stmt)
        existing_delivery = result.scalar_one_or_none()

        if existing_delivery:
            # Update existing delivery
            existing_delivery.status = delivery.status.value
            existing_delivery.completed_at = delivery.completed_at
        else:
            # Create new delivery
            new_delivery = DeliveryModel(
                id=delivery.id.value,
                notification_id=delivery.notification.id.value,
                channel=delivery.channel,
                provider=delivery.provider,
                status=delivery.status.value,
                created_at=delivery.created_at,
                completed_at=delivery.completed_at
            )
            self.session.add(new_delivery)

        # Handle delivery attempts (simplified - in real implementation would be more complex)
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

    async def get_by_notification(self, notification_id: NotificationId) -> list[Delivery]:
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
        successful_deliveries = len([
            d for d in recent_deliveries
            if d.status == DeliveryStatus.DELIVERED.value
        ])
        failed_deliveries = len([
            d for d in recent_deliveries
            if d.status == DeliveryStatus.FAILED.value
        ])
        pending_deliveries = len([
            d for d in recent_deliveries
            if d.status in [
                DeliveryStatus.PENDING.value,
                DeliveryStatus.SENT.value,
                DeliveryStatus.RETRYING.value
            ]
        ])

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
            "success_rate": (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0,
            "provider_statistics": provider_stats
        }
