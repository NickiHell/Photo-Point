"""
Delivery repository implementation based on Tortoise ORM.
"""

from typing import List, Optional

from app.domain.entities.delivery import Delivery, DeliveryAttempt
from app.domain.repositories.delivery_repository import DeliveryRepository
from app.domain.value_objects.delivery import (
    DeliveryId,
    DeliveryStatus,
    DeliveryStrategy,
    RetryPolicy,
)
from app.domain.value_objects.notification import NotificationId
from app.infrastructure.repositories.tortoise_models import (
    DeliveryAttemptModel,
    DeliveryModel,
)


class TortoiseDeliveryRepository(DeliveryRepository):
    """Tortoise ORM implementation of the DeliveryRepository."""

    async def get_by_id(self, delivery_id: DeliveryId) -> Optional[Delivery]:
        """Get a delivery by ID."""
        delivery_model = await DeliveryModel.get_or_none(
            id=delivery_id.value
        ).prefetch_related("attempts")
        if not delivery_model:
            return None

        return self._model_to_entity(delivery_model)

    async def save(self, delivery: Delivery) -> Delivery:
        """Save a delivery."""
        delivery_data = {
            "id": delivery.id.value,
            "notification_id": delivery.notification_id.value,
            "channel": delivery.channel,
            "provider": delivery.provider,
            "status": delivery.status.value,
            "completed_at": delivery.completed_at,
        }

        delivery_model, created = await DeliveryModel.update_or_create(
            id=delivery.id.value, defaults=delivery_data
        )

        # Save attempts if any
        for attempt in delivery.attempts:
            attempt_data = {
                "delivery_id": delivery.id.value,
                "attempt_number": attempt.attempt_number,
                "provider": attempt.provider,
                "attempted_at": attempt.attempted_at,
                "success": attempt.success,
                "error_message": attempt.error_message,
                "response_data": attempt.response_data,
            }

            await DeliveryAttemptModel.update_or_create(
                delivery_id=delivery.id.value,
                attempt_number=attempt.attempt_number,
                defaults=attempt_data,
            )

        # Reload to get the updated model with attempts
        delivery_model = await DeliveryModel.get(id=delivery.id.value).prefetch_related(
            "attempts"
        )

        return self._model_to_entity(delivery_model)

    async def list_by_notification(
        self, notification_id: NotificationId
    ) -> List[Delivery]:
        """List deliveries for a notification."""
        delivery_models = await DeliveryModel.filter(
            notification_id=notification_id.value
        ).prefetch_related("attempts")

        return [
            self._model_to_entity(delivery_model) for delivery_model in delivery_models
        ]

    async def list_pending(self, limit: int = 100, offset: int = 0) -> List[Delivery]:
        """List pending deliveries."""
        delivery_models = (
            await DeliveryModel.filter(status="pending")
            .limit(limit)
            .offset(offset)
            .prefetch_related("attempts")
        )

        return [
            self._model_to_entity(delivery_model) for delivery_model in delivery_models
        ]

    def _model_to_entity(self, delivery_model: DeliveryModel) -> Delivery:
        """Convert a DeliveryModel to a Delivery entity."""
        attempts = []

        for attempt_model in delivery_model.attempts:
            attempt = DeliveryAttempt(
                attempt_number=attempt_model.attempt_number,
                provider=attempt_model.provider,
                attempted_at=attempt_model.attempted_at,
                success=attempt_model.success,
                error_message=attempt_model.error_message,
                response_data=attempt_model.response_data or {},
            )
            attempts.append(attempt)

        # Sort attempts by attempt number
        attempts.sort(key=lambda a: a.attempt_number)

        # Use retry policy from configuration
        retry_policy = RetryPolicy()

        return Delivery(
            id=DeliveryId(delivery_model.id),
            notification_id=NotificationId(delivery_model.notification_id),
            channel=delivery_model.channel,
            provider=delivery_model.provider,
            status=DeliveryStatus(delivery_model.status),
            attempts=attempts,
            completed_at=delivery_model.completed_at,
            strategy=DeliveryStrategy.TRY_ALL,  # Default strategy
            retry_policy=retry_policy,
        )
