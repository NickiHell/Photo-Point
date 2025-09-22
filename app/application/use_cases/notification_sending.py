"""
Notification sending use cases.
"""

import asyncio
import uuid
from datetime import UTC, datetime

import backoff

from ...domain.entities.delivery import Delivery
from ...domain.entities.notification import Notification
from ...domain.repositories import (
    DeliveryRepository,
    NotificationRepository,
    UserRepository,
)
from ...domain.services import NotificationDeliveryService
from ...domain.value_objects.delivery import DeliveryId, DeliveryStrategy
from ...domain.value_objects.notification import (
    MessageTemplate,
    NotificationId,
    NotificationPriority,
)
from ...domain.value_objects.user import UserId
from ..dto import (
    BulkNotificationRequest,
    DeliveryAttemptResponse,
    DeliveryResponse,
    OperationResponse,
    SendNotificationRequest,
)


class SendNotificationUseCase:
    """Use case for sending a notification to a single user."""

    def __init__(
        self,
        user_repository: UserRepository,
        notification_repository: NotificationRepository,
        delivery_repository: DeliveryRepository,
        delivery_service: NotificationDeliveryService,
    ) -> None:
        self._user_repository = user_repository
        self._notification_repository = notification_repository
        self._delivery_repository = delivery_repository
        self._delivery_service = delivery_service

    @backoff.on_exception(
        backoff.expo,
        (ConnectionError, TimeoutError, Exception),
        max_tries=3,
        max_time=30,
    )
    async def execute(self, request: SendNotificationRequest) -> OperationResponse:
        """Execute the send notification use case."""
        try:
            # Validate and get user
            user_id = UserId(request.recipient_id)
            user = await self._user_repository.get_by_id(user_id)

            if not user:
                return OperationResponse(
                    success=False,
                    message="Recipient not found",
                    errors=["User with given ID does not exist"],
                )

            if not user.can_receive_notifications():
                return OperationResponse(
                    success=False,
                    message="User cannot receive notifications",
                    errors=["User is inactive or has no available channels"],
                )

            # Create notification
            notification_id = NotificationId(str(uuid.uuid4()))
            message_template = MessageTemplate(
                subject=request.subject,
                content=request.content,
                template_data=request.template_data,
            )

            # Convert priority string to enum
            priority = NotificationPriority.NORMAL  # Default
            if request.priority:
                try:
                    priority = NotificationPriority(request.priority.lower())
                except ValueError:
                    # Use default if invalid priority
                    pass

            # Create notification entity
            notification = Notification(
                notification_id=notification_id,
                recipient_id=user_id,
                message_template=message_template,
                priority=priority,
            )

            # Save notification
            await self._notification_repository.save(notification)

            # Create delivery
            delivery_id = DeliveryId(str(uuid.uuid4()))

            # Convert string strategy to enum
            strategy = DeliveryStrategy.FIRST_SUCCESS  # Default
            if request.strategy:
                try:
                    strategy = DeliveryStrategy(request.strategy.upper())
                except ValueError:
                    # Use default if invalid strategy
                    pass

            delivery = Delivery(
                delivery_id=delivery_id,
                notification=notification,
                user=user,
                strategy=strategy,
            )

            # Execute delivery
            delivery_result = await self._execute_delivery(delivery)

            # Save delivery
            await self._delivery_repository.save(delivery)

            return OperationResponse(
                success=delivery_result.success,
                message="Notification processed successfully",
                data=delivery_result,
            )

        except ValueError as e:
            return OperationResponse(
                success=False, message="Invalid input data", errors=[str(e)]
            )
        except Exception as e:
            return OperationResponse(
                success=False, message="Failed to send notification", errors=[str(e)]
            )

    @backoff.on_exception(
        backoff.expo, (ConnectionError, TimeoutError), max_tries=3, max_time=15
    )
    async def _execute_delivery(self, delivery: Delivery) -> DeliveryResponse:
        """Execute the delivery process."""
        delivery.start()

        if delivery.status.value == "failed":
            return self._create_delivery_response(delivery)

        # Get available providers
        providers = self._delivery_service.get_ordered_providers_for_user(delivery.user)

        if not providers:
            return self._create_delivery_response(delivery)

        # Execute delivery based on strategy
        if delivery.strategy == DeliveryStrategy.FIRST_SUCCESS:
            await self._execute_first_success_strategy(delivery, providers)
        elif delivery.strategy == DeliveryStrategy.TRY_ALL:
            await self._execute_try_all_strategy(delivery, providers)
        elif delivery.strategy == DeliveryStrategy.FAIL_FAST:
            await self._execute_fail_fast_strategy(delivery, providers)

        return self._create_delivery_response(delivery)

    @backoff.on_exception(
        backoff.expo, (ConnectionError, TimeoutError), max_tries=2, max_time=10
    )
    async def _execute_first_success_strategy(
        self, delivery: Delivery, providers: list
    ) -> None:
        """Execute first success delivery strategy."""
        rendered_message = delivery.notification.render_message()

        for provider in providers:
            try:
                result = await provider.send(delivery.user, rendered_message)
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result,
                )

                if result.success:
                    break  # Stop on first success

            except Exception as e:
                from ...domain.value_objects.delivery import (
                    DeliveryError,
                    DeliveryResult,
                )

                error = DeliveryError(code="PROVIDER_ERROR", message=str(e))
                result = DeliveryResult(
                    success=False,
                    provider=provider.name,
                    message="Provider failed with exception",
                    error=error,
                )
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result,
                )

    @backoff.on_exception(
        backoff.expo, (ConnectionError, TimeoutError), max_tries=2, max_time=15
    )
    async def _execute_try_all_strategy(
        self, delivery: Delivery, providers: list
    ) -> None:
        """Execute try all delivery strategy."""
        rendered_message = delivery.notification.render_message()

        # Try all providers regardless of success
        for provider in providers:
            try:
                result = await provider.send(delivery.user, rendered_message)
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result,
                )

            except Exception as e:
                from ...domain.value_objects.delivery import (
                    DeliveryError,
                    DeliveryResult,
                )

                error = DeliveryError(code="PROVIDER_ERROR", message=str(e))
                result = DeliveryResult(
                    success=False,
                    provider=provider.name,
                    message="Provider failed with exception",
                    error=error,
                )
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result,
                )

    @backoff.on_exception(
        backoff.expo, (ConnectionError, TimeoutError), max_tries=2, max_time=10
    )
    async def _execute_fail_fast_strategy(
        self, delivery: Delivery, providers: list
    ) -> None:
        """Execute fail fast delivery strategy."""
        rendered_message = delivery.notification.render_message()

        for provider in providers:
            try:
                result = await provider.send(delivery.user, rendered_message)
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result,
                )

                if not result.success:
                    break  # Stop on first failure

            except Exception as e:
                from ...domain.value_objects.delivery import (
                    DeliveryError,
                    DeliveryResult,
                )

                error = DeliveryError(code="PROVIDER_ERROR", message=str(e))
                result = DeliveryResult(
                    success=False,
                    provider=provider.name,
                    message="Provider failed with exception",
                    error=error,
                )
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result,
                )
                break

    def _create_delivery_response(self, delivery: Delivery) -> DeliveryResponse:
        """Create delivery response from delivery entity."""
        attempts = []
        for attempt in delivery.attempts:
            attempts.append(
                DeliveryAttemptResponse(
                    id=str(attempt.id) if hasattr(attempt, "id") else str(uuid.uuid4()),
                    delivery_id=str(delivery.id.value),
                    provider=attempt.provider,
                    channel=attempt.channel.value,
                    status="SUCCESS" if attempt.result.success else "FAILED",
                    error_message=attempt.result.error.message
                    if attempt.result.error
                    else None,
                    attempted_at=attempt.attempted_at,
                    completed_at=attempt.attempted_at,  # Assuming completed at same time for now
                    duration=getattr(attempt.result, "delivery_time", 0.0) or 0.0,
                )
            )

        successful_attempts = delivery.get_successful_attempts()
        failed_attempts = delivery.get_failed_attempts()

        return DeliveryResponse(
            id=str(delivery.id.value),
            notification_id=str(delivery.notification.id.value),
            user_id=str(delivery.user.id.value),
            status=delivery.status.value,
            strategy=delivery.strategy.value,
            attempts=attempts,
            total_attempts=len(delivery.attempts),
            successful_providers=[attempt.provider for attempt in successful_attempts],
            failed_providers=[attempt.provider for attempt in failed_attempts],
            started_at=delivery.started_at or datetime.now(UTC),
            completed_at=delivery.completed_at,
            total_delivery_time=delivery.get_total_delivery_time() or 0.0,
            created_at=delivery.created_at,
            updated_at=delivery.updated_at,
            success=len(successful_attempts) > 0,
        )


class SendBulkNotificationUseCase:
    """Use case for sending notifications to multiple users."""

    def __init__(
        self,
        user_repository: UserRepository,
        send_notification_use_case: SendNotificationUseCase,
    ) -> None:
        self._user_repository = user_repository
        self._send_notification_use_case = send_notification_use_case

    @backoff.on_exception(
        backoff.expo,
        (ConnectionError, TimeoutError, Exception),
        max_tries=2,
        max_time=60,
    )
    async def execute(self, request: BulkNotificationRequest) -> OperationResponse:
        """Execute the bulk notification use case."""
        try:
            # Validate all recipient IDs exist
            users = []
            for recipient_id in request.recipient_ids:
                user_id = UserId(recipient_id)
                user = await self._user_repository.get_by_id(user_id)
                if user:
                    users.append(user)

            if not users:
                return OperationResponse(
                    success=False,
                    message="No valid recipients found",
                    errors=["None of the provided recipient IDs exist"],
                )

            # Create individual send requests
            send_requests = []
            for user in users:
                send_request = SendNotificationRequest(
                    recipient_id=str(user.id.value),
                    subject=request.subject,
                    content=request.content,
                    template_data={
                        **(request.template_data or {}),
                        "user_name": user.name.value,  # Add user name to template data
                        "user_id": str(user.id.value),
                    },
                    priority=request.priority,
                    strategy=request.strategy,
                )
                send_requests.append(send_request)

            # Execute notifications with concurrency control
            semaphore = asyncio.Semaphore(request.max_concurrent)

            async def send_with_semaphore(send_request: SendNotificationRequest):
                async with semaphore:
                    return await self._send_notification_use_case.execute(send_request)

            # Execute all notifications
            results = await asyncio.gather(
                *[send_with_semaphore(req) for req in send_requests],
                return_exceptions=True,
            )

            # Process results
            successful_deliveries = []
            failed_deliveries = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_deliveries.append(
                        {"user_id": send_requests[i].recipient_id, "error": str(result)}
                    )
                elif hasattr(result, "success") and result.success:
                    successful_deliveries.append(getattr(result, "data", None))
                else:
                    failed_deliveries.append(
                        {
                            "user_id": send_requests[i].recipient_id,
                            "error": getattr(result, "message", "Unknown error"),
                        }
                    )

            return OperationResponse(
                success=len(successful_deliveries) > 0,
                message=f"Bulk notification completed. {len(successful_deliveries)} successful, {len(failed_deliveries)} failed",
                data={
                    "total_users": len(users),
                    "successful_deliveries": successful_deliveries,
                    "failed_deliveries": failed_deliveries,
                    "success_rate": len(successful_deliveries) / len(users) * 100,
                },
            )

        except ValueError as e:
            return OperationResponse(
                success=False, message="Invalid input data", errors=[str(e)]
            )
        except Exception as e:
            return OperationResponse(
                success=False,
                message="Failed to send bulk notifications",
                errors=[str(e)],
            )
