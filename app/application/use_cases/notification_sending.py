"""
Notification sending use cases.
"""
from typing import List, Optional
import uuid
import asyncio
from datetime import datetime, timezone

from ..dto import (
    SendNotificationRequest, BulkNotificationRequest, 
    DeliveryResponse, OperationResponse, DeliveryAttemptResponse
)
from ...domain.entities.user import User
from ...domain.entities.notification import Notification
from ...domain.entities.delivery import Delivery
from ...domain.value_objects.user import UserId
from ...domain.value_objects.notification import (
    NotificationId, MessageTemplate, NotificationPriority
)
from ...domain.value_objects.delivery import DeliveryId, DeliveryStrategy, RetryPolicy
from ...domain.repositories import UserRepository, NotificationRepository, DeliveryRepository
from ...domain.services import NotificationDeliveryService


class SendNotificationUseCase:
    """Use case for sending a notification to a single user."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        notification_repository: NotificationRepository,
        delivery_repository: DeliveryRepository,
        delivery_service: NotificationDeliveryService
    ) -> None:
        self._user_repository = user_repository
        self._notification_repository = notification_repository
        self._delivery_repository = delivery_repository
        self._delivery_service = delivery_service
    
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
                    errors=["User with given ID does not exist"]
                )
            
            if not user.can_receive_notifications():
                return OperationResponse(
                    success=False,
                    message="User cannot receive notifications",
                    errors=["User is inactive or has no available channels"]
                )
            
            # Create notification
            notification_id = NotificationId(str(uuid.uuid4()))
            message_template = MessageTemplate(
                subject=request.subject,
                content=request.content,
                template_data=request.template_data
            )
            
            notification = Notification(
                notification_id=notification_id,
                recipient_id=user_id,
                message_template=message_template,
                priority=request.priority,
                scheduled_at=request.scheduled_at,
                expires_at=request.expires_at
            )
            
            # Save notification
            await self._notification_repository.save(notification)
            
            # Create delivery
            delivery_id = DeliveryId(str(uuid.uuid4()))
            delivery = Delivery(
                delivery_id=delivery_id,
                notification=notification,
                user=user,
                strategy=request.strategy
            )
            
            # Execute delivery
            delivery_result = await self._execute_delivery(delivery)
            
            # Save delivery
            await self._delivery_repository.save(delivery)
            
            return OperationResponse(
                success=delivery_result.success,
                message="Notification processed successfully",
                data=delivery_result
            )
            
        except ValueError as e:
            return OperationResponse(
                success=False,
                message="Invalid input data",
                errors=[str(e)]
            )
        except Exception as e:
            return OperationResponse(
                success=False,
                message="Failed to send notification",
                errors=[str(e)]
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
    
    async def _execute_first_success_strategy(self, delivery: Delivery, providers: List) -> None:
        """Execute first success delivery strategy."""
        rendered_message = delivery.notification.render_message()
        
        for provider in providers:
            try:
                result = await provider.send(delivery.user, rendered_message)
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result
                )
                
                if result.success:
                    break  # Stop on first success
                    
            except Exception as e:
                from ...domain.value_objects.delivery import DeliveryResult, DeliveryError
                error = DeliveryError(code="PROVIDER_ERROR", message=str(e))
                result = DeliveryResult(
                    success=False,
                    provider=provider.name,
                    message="Provider failed with exception",
                    error=error
                )
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result
                )
    
    async def _execute_try_all_strategy(self, delivery: Delivery, providers: List) -> None:
        """Execute try all delivery strategy."""
        rendered_message = delivery.notification.render_message()
        
        # Try all providers regardless of success
        for provider in providers:
            try:
                result = await provider.send(delivery.user, rendered_message)
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result
                )
                    
            except Exception as e:
                from ...domain.value_objects.delivery import DeliveryResult, DeliveryError
                error = DeliveryError(code="PROVIDER_ERROR", message=str(e))
                result = DeliveryResult(
                    success=False,
                    provider=provider.name,
                    message="Provider failed with exception",
                    error=error
                )
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result
                )
    
    async def _execute_fail_fast_strategy(self, delivery: Delivery, providers: List) -> None:
        """Execute fail fast delivery strategy."""
        rendered_message = delivery.notification.render_message()
        
        for provider in providers:
            try:
                result = await provider.send(delivery.user, rendered_message)
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result
                )
                
                if not result.success:
                    break  # Stop on first failure
                    
            except Exception as e:
                from ...domain.value_objects.delivery import DeliveryResult, DeliveryError
                error = DeliveryError(code="PROVIDER_ERROR", message=str(e))
                result = DeliveryResult(
                    success=False,
                    provider=provider.name,
                    message="Provider failed with exception",
                    error=error
                )
                delivery.add_attempt(
                    provider=provider.name,
                    channel=provider.get_channel_type(),
                    result=result
                )
                break
    
    def _create_delivery_response(self, delivery: Delivery) -> DeliveryResponse:
        """Create delivery response from delivery entity."""
        attempts = []
        for attempt in delivery.attempts:
            attempts.append(DeliveryAttemptResponse(
                provider=attempt.provider,
                channel=attempt.channel.value,
                attempted_at=attempt.attempted_at,
                success=attempt.result.success,
                message=attempt.result.message,
                error=attempt.result.error.message if attempt.result.error else None,
                delivery_time=attempt.result.delivery_time
            ))
        
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
            started_at=delivery.started_at,
            completed_at=delivery.completed_at,
            total_delivery_time=delivery.get_total_delivery_time(),
            created_at=delivery.created_at,
            updated_at=delivery.updated_at
        )


class SendBulkNotificationUseCase:
    """Use case for sending notifications to multiple users."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        send_notification_use_case: SendNotificationUseCase
    ) -> None:
        self._user_repository = user_repository
        self._send_notification_use_case = send_notification_use_case
    
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
                    errors=["None of the provided recipient IDs exist"]
                )
            
            # Create individual send requests
            send_requests = []
            for user in users:
                send_request = SendNotificationRequest(
                    recipient_id=str(user.id.value),
                    subject=request.subject,
                    content=request.content,
                    template_data={
                        **request.template_data,
                        "user_name": user.name.value,  # Add user name to template data
                        "user_id": str(user.id.value)
                    },
                    priority=request.priority,
                    strategy=request.strategy
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
                return_exceptions=True
            )
            
            # Process results
            successful_deliveries = []
            failed_deliveries = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_deliveries.append({
                        "user_id": send_requests[i].recipient_id,
                        "error": str(result)
                    })
                elif result.success:
                    successful_deliveries.append(result.data)
                else:
                    failed_deliveries.append({
                        "user_id": send_requests[i].recipient_id,
                        "error": result.message
                    })
            
            return OperationResponse(
                success=len(successful_deliveries) > 0,
                message=f"Bulk notification completed. {len(successful_deliveries)} successful, {len(failed_deliveries)} failed",
                data={
                    "total_users": len(users),
                    "successful_deliveries": successful_deliveries,
                    "failed_deliveries": failed_deliveries,
                    "success_rate": len(successful_deliveries) / len(users) * 100
                }
            )
            
        except ValueError as e:
            return OperationResponse(
                success=False,
                message="Invalid input data",
                errors=[str(e)]
            )
        except Exception as e:
            return OperationResponse(
                success=False,
                message="Failed to send bulk notifications",
                errors=[str(e)]
            )