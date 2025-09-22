"""
Celery-based notification use cases for better reliability and scaling.
"""

from datetime import datetime
from typing import Any

from structlog import get_logger

from ...domain.repositories import UserRepository
from ...domain.value_objects.user import UserId
from ...infrastructure.tasks import (
    retry_failed_notification_task,
    send_bulk_notification_task,
    send_notification_task,
)
from ..dto import (
    BulkNotificationRequest,
    BulkNotificationTaskResponse,
    NotificationTaskResponse,
    OperationResponse,
    SendNotificationRequest,
)

logger = get_logger()


class SendNotificationAsyncUseCase:
    """
    Use case for asynchronously sending a notification using Celery.

    This replaces the direct async SendNotificationUseCase with a more reliable
    Celery-based approach that provides better error handling, retries, and monitoring.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, request: SendNotificationRequest) -> OperationResponse:
        """
        Execute the async send notification use case.

        Instead of processing immediately, this queues a Celery task
        for background processing with proper retry mechanisms.
        """
        try:
            # Validate user exists
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

            # Queue Celery task
            task_result = send_notification_task.delay(
                recipient_id=request.recipient_id,
                subject=request.subject,
                content=request.content,
                template_data=request.template_data or {},
                priority=request.priority if request.priority else "normal",
                strategy=request.strategy if request.strategy else "first_success",
                scheduled_at=request.scheduled_at.isoformat()
                if request.scheduled_at
                else None,
                expires_at=request.expires_at.isoformat()
                if request.expires_at
                else None,
            )

            logger.info(
                "Notification task queued",
                task_id=task_result.id,
                recipient_id=request.recipient_id,
                subject=request.subject,
                priority=request.priority if request.priority else "normal",
            )

            return OperationResponse(
                success=True,
                message="Notification queued successfully",
                data=NotificationTaskResponse(
                    task_id=task_result.id,
                    recipient_id=request.recipient_id,
                    subject=request.subject,
                    status="queued",
                    queued_at=datetime.utcnow(),
                ),
            )

        except ValueError as e:
            logger.error("Invalid input for notification task", error=str(e))
            return OperationResponse(
                success=False, message="Invalid input data", errors=[str(e)]
            )
        except Exception as e:
            logger.error("Failed to queue notification task", error=str(e))
            return OperationResponse(
                success=False, message="Failed to queue notification", errors=[str(e)]
            )


class SendBulkNotificationAsyncUseCase:
    """
    Use case for asynchronously sending bulk notifications using Celery.

    Provides better concurrency control and error isolation compared to
    the direct async approach.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, request: BulkNotificationRequest) -> OperationResponse:
        """
        Execute the async bulk notification use case.

        Validates recipients and queues a bulk Celery task that will
        spawn individual notification tasks for better parallelism.
        """
        try:
            # Validate recipients exist
            valid_recipients = []
            invalid_recipients = []

            for recipient_id in request.recipient_ids:
                try:
                    user_id = UserId(recipient_id)
                    user = await self._user_repository.get_by_id(user_id)

                    if user and user.can_receive_notifications():
                        valid_recipients.append(recipient_id)
                    else:
                        invalid_recipients.append(recipient_id)

                except Exception:
                    invalid_recipients.append(recipient_id)

            if not valid_recipients:
                return OperationResponse(
                    success=False,
                    message="No valid recipients found",
                    errors=[f"Invalid recipient IDs: {invalid_recipients}"],
                )

            # Queue bulk Celery task
            task_result = send_bulk_notification_task.delay(
                recipient_ids=valid_recipients,
                subject=request.subject,
                content=request.content,
                template_data=request.template_data or {},
                priority=request.priority if request.priority else "normal",
                strategy=request.strategy if request.strategy else "first_success",
                max_concurrent=request.max_concurrent,
            )

            logger.info(
                "Bulk notification task queued",
                task_id=task_result.id,
                valid_recipients_count=len(valid_recipients),
                invalid_recipients_count=len(invalid_recipients),
                subject=request.subject,
            )

            return OperationResponse(
                success=True,
                message=f"Bulk notification queued for {len(valid_recipients)} recipients",
                data=BulkNotificationTaskResponse(
                    task_id=task_result.id,
                    valid_recipients_count=len(valid_recipients),
                    invalid_recipients_count=len(invalid_recipients),
                    invalid_recipients=invalid_recipients,
                    subject=request.subject,
                    status="queued",
                    queued_at=datetime.utcnow(),
                    max_concurrent=request.max_concurrent,
                ),
            )

        except ValueError as e:
            logger.error("Invalid input for bulk notification task", error=str(e))
            return OperationResponse(
                success=False, message="Invalid input data", errors=[str(e)]
            )
        except Exception as e:
            logger.error("Failed to queue bulk notification task", error=str(e))
            return OperationResponse(
                success=False,
                message="Failed to queue bulk notification",
                errors=[str(e)],
            )


class GetTaskStatusUseCase:
    """
    Use case for checking the status of a Celery task.

    Provides visibility into task execution progress and results.
    """

    def __init__(self) -> None:
        pass

    async def execute(self, task_id: str) -> OperationResponse:
        """
        Get the status of a Celery task.

        Args:
            task_id: The Celery task ID

        Returns:
            OperationResponse with task status information
        """
        try:
            from ...infrastructure.celery_config import celery_app

            # Get task result
            task_result = celery_app.AsyncResult(task_id)

            # Build response based on task state
            if task_result.state == "PENDING":
                task_info = {
                    "task_id": task_id,
                    "status": "pending",
                    "message": "Task is waiting to be processed",
                }
            elif task_result.state == "STARTED":
                task_info = {
                    "task_id": task_id,
                    "status": "started",
                    "message": "Task is being processed",
                    "info": task_result.info or {},  # type: ignore[dict-item]
                }
            elif task_result.state == "SUCCESS":
                task_info = {
                    "task_id": task_id,
                    "status": "success",
                    "message": "Task completed successfully",
                    "result": task_result.result,
                }
            elif task_result.state == "FAILURE":
                task_info = {
                    "task_id": task_id,
                    "status": "failure",
                    "message": f"Task failed: {str(task_result.info)}",
                    "error": str(task_result.info),
                    "traceback": task_result.traceback,
                }
            elif task_result.state == "RETRY":
                task_info = {
                    "task_id": task_id,
                    "status": "retry",
                    "message": f"Task is being retried: {str(task_result.info)}",
                    "retry_info": task_result.info or {},  # type: ignore[dict-item]
                }
            else:
                task_info = {
                    "task_id": task_id,
                    "status": task_result.state.lower(),
                    "message": f"Task in state: {task_result.state}",
                    "info": task_result.info or {},  # type: ignore[dict-item]
                }

            return OperationResponse(
                success=True,
                message="Task status retrieved successfully",
                data=task_info,
            )

        except Exception as e:
            logger.error("Failed to get task status", task_id=task_id, error=str(e))
            return OperationResponse(
                success=False, message="Failed to retrieve task status", errors=[str(e)]
            )


class RetryFailedNotificationUseCase:
    """
    Use case for retrying a failed notification.

    Allows manual retry of failed notifications with the original parameters.
    """

    def __init__(self) -> None:
        pass

    async def execute(self, original_task_data: dict[str, Any]) -> OperationResponse:
        """
        Retry a failed notification with the original parameters.

        Args:
            original_task_data: Original notification parameters

        Returns:
            OperationResponse with retry task information
        """
        try:
            # Validate required fields
            required_fields = ["recipient_id", "subject", "content"]
            for field in required_fields:
                if field not in original_task_data:
                    return OperationResponse(
                        success=False,
                        message=f"Missing required field: {field}",
                        errors=[f"Field '{field}' is required for retry"],
                    )

            # Queue retry task
            task_result = retry_failed_notification_task.delay(original_task_data)

            logger.info(
                "Retry task queued",
                retry_task_id=task_result.id,
                original_recipient=original_task_data.get("recipient_id"),
                original_subject=original_task_data.get("subject"),
            )

            return OperationResponse(
                success=True,
                message="Notification retry queued successfully",
                data={
                    "retry_task_id": task_result.id,
                    "original_recipient_id": original_task_data.get("recipient_id"),
                    "original_subject": original_task_data.get("subject"),
                    "status": "queued",
                    "queued_at": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error("Failed to queue retry task", error=str(e))
            return OperationResponse(
                success=False,
                message="Failed to queue notification retry",
                errors=[str(e)],
            )
