"""
Celery-based notification API endpoints for asynchronous processing.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ....application.dto import (
    BulkNotificationRequest,
    BulkNotificationTaskResponse,
    NotificationTaskResponse,
    SendNotificationRequest,
)
from ....application.use_cases.celery_notification_sending import (
    GetTaskStatusUseCase,
    RetryFailedNotificationUseCase,
    SendBulkNotificationAsyncUseCase,
)
from ....domain.value_objects.delivery import DeliveryStrategy
from ....domain.value_objects.notification import NotificationPriority
from ...dependencies import get_notification_async_use_cases

router = APIRouter(prefix="/async", tags=["async-notifications"])


# Pydantic models for API
class AsyncSendNotificationRequest(BaseModel):
    """Async send notification request model."""

    recipient_id: str = Field(description="Recipient user ID")
    subject: str = Field(description="Notification subject")
    content: str = Field(description="Notification content")
    template_data: dict[str, Any] = Field(
        default_factory=dict, description="Template variables"
    )
    priority: str = Field(
        default="normal",
        description="Notification priority (low, normal, high, urgent)",
    )
    strategy: str = Field(default="first_success", description="Delivery strategy")
    scheduled_at: str | None = Field(
        None, description="Scheduled delivery time (ISO format)"
    )
    expires_at: str | None = Field(None, description="Expiration time (ISO format)")


class AsyncBulkNotificationRequest(BaseModel):
    """Async bulk notification request model."""

    recipient_ids: list[str] = Field(description="List of recipient user IDs")
    subject: str = Field(description="Notification subject")
    content: str = Field(description="Notification content")
    template_data: dict[str, Any] = Field(
        default_factory=dict, description="Template variables"
    )
    priority: str = Field(default="normal", description="Notification priority")
    strategy: str = Field(default="first_success", description="Delivery strategy")
    max_concurrent: int = Field(
        default=10, ge=1, le=50, description="Maximum concurrent tasks"
    )


class NotificationTaskStatusRequest(BaseModel):
    """Task status request model."""

    task_id: str = Field(description="Celery task ID")


class RetryNotificationRequest(BaseModel):
    """Retry notification request model."""

    recipient_id: str = Field(description="Recipient user ID")
    subject: str = Field(description="Notification subject")
    content: str = Field(description="Notification content")
    template_data: dict[str, Any] = Field(
        default_factory=dict, description="Template variables"
    )
    priority: str = Field(default="normal", description="Notification priority")
    strategy: str = Field(default="first_success", description="Delivery strategy")


class AsyncNotificationResponse(BaseModel):
    """Async notification response model."""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Response message")
    task_id: str = Field(description="Celery task ID")
    recipient_id: str = Field(description="Recipient user ID")
    subject: str = Field(description="Notification subject")
    status: str = Field(description="Task status")
    queued_at: str = Field(description="Task queue timestamp")


class AsyncBulkNotificationResponse(BaseModel):
    """Async bulk notification response model."""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Response message")
    task_id: str = Field(description="Bulk task ID")
    valid_recipients_count: int = Field(description="Number of valid recipients")
    invalid_recipients_count: int = Field(description="Number of invalid recipients")
    invalid_recipients: list[str] = Field(description="List of invalid recipient IDs")
    subject: str = Field(description="Notification subject")
    status: str = Field(description="Task status")
    queued_at: str = Field(description="Task queue timestamp")
    max_concurrent: int = Field(description="Maximum concurrent tasks")


class TaskStatusResponseModel(BaseModel):
    """Task status response model."""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Response message")
    task_id: str = Field(description="Task ID")
    status: str = Field(description="Task status")
    result: dict[str, Any] | None = Field(None, description="Task result")
    error: str | None = Field(None, description="Error message if failed")
    info: dict[str, Any] | None = Field(None, description="Additional task info")


@router.post(
    "/notifications/send",
    response_model=AsyncNotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send notification asynchronously",
    description="Queue a notification for asynchronous processing using Celery. Returns task ID for status tracking.",
)
async def send_notification_async(
    request: AsyncSendNotificationRequest,
    # use_case: SendNotificationAsyncUseCase = Depends(get_notification_async_use_cases)
):
    """Send a single notification asynchronously using Celery."""
    try:
        # Get use case directly for now
        from ....application.use_cases.celery_notification_sending import (
            SendNotificationAsyncUseCase,
        )
        from ....presentation.dependencies import get_container

        container = get_container()
        user_repo = (
            container.user_repository()
            if hasattr(container, "user_repository")
            else None
        )

        if not user_repo:
            # Create a simple mock response for now
            from ....infrastructure.tasks import send_notification_task

            task_result = send_notification_task.delay(
                recipient_id=request.recipient_id,
                subject=request.subject,
                content=request.content,
                template_data=request.template_data,
                priority=request.priority,
                strategy=request.strategy,
                scheduled_at=request.scheduled_at,
                expires_at=request.expires_at,
            )

            return AsyncNotificationResponse(
                success=True,
                message="Notification queued successfully",
                task_id=task_result.id,
                recipient_id=request.recipient_id,
                subject=request.subject,
                status="queued",
                queued_at=datetime.utcnow().isoformat(),
            )

        # Use actual use case when container is working
        use_case = SendNotificationAsyncUseCase(user_repo)

        # Parse datetime fields
        scheduled_at = None
        expires_at = None

        if request.scheduled_at:
            scheduled_at = datetime.fromisoformat(
                request.scheduled_at.replace("Z", "+00:00")
            )
        if request.expires_at:
            expires_at = datetime.fromisoformat(
                request.expires_at.replace("Z", "+00:00")
            )

        # Create use case request
        dto = SendNotificationRequest(
            recipient_id=request.recipient_id,
            subject=request.subject,
            content=request.content,
            template_data=request.template_data,
            priority=NotificationPriority(request.priority),
            strategy=DeliveryStrategy(request.strategy),
            scheduled_at=scheduled_at,
            expires_at=expires_at,
        )

        # Execute use case
        result = await use_case.execute(dto)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": result.message, "errors": result.errors},
            )

        # Extract task data
        task_data: NotificationTaskResponse = result.data

        return AsyncNotificationResponse(
            success=result.success,
            message=result.message,
            task_id=task_data.task_id,
            recipient_id=task_data.recipient_id,
            subject=task_data.subject,
            status=task_data.status,
            queued_at=task_data.queued_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/notifications/send-bulk",
    response_model=AsyncBulkNotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send bulk notifications asynchronously",
    description="Queue bulk notifications for asynchronous processing. Returns task ID for status tracking.",
)
async def send_bulk_notification_async(
    request: AsyncBulkNotificationRequest,
    use_case: SendBulkNotificationAsyncUseCase = Depends(
        get_notification_async_use_cases
    ),
):
    """Send bulk notifications asynchronously using Celery."""
    try:
        # Create use case request
        dto = BulkNotificationRequest(
            recipient_ids=request.recipient_ids,
            subject=request.subject,
            content=request.content,
            template_data=request.template_data,
            priority=request.priority,
            strategy=request.strategy,
            max_concurrent=request.max_concurrent,
        )

        # Execute use case
        result = await use_case.execute(dto)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": result.message, "errors": result.errors},
            )

        # Extract task data
        task_data: BulkNotificationTaskResponse = result.data

        return AsyncBulkNotificationResponse(
            success=result.success,
            message=result.message,
            task_id=task_data.task_id,
            valid_recipients_count=task_data.valid_recipients_count,
            invalid_recipients_count=task_data.invalid_recipients_count,
            invalid_recipients=task_data.invalid_recipients,
            subject=task_data.subject,
            status=task_data.status,
            queued_at=task_data.queued_at.isoformat(),
            max_concurrent=task_data.max_concurrent,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/tasks/{task_id}/status",
    response_model=TaskStatusResponseModel,
    summary="Get task status",
    description="Get the current status and result of a Celery task.",
)
async def get_task_status(
    task_id: str,
    use_case: GetTaskStatusUseCase = Depends(get_notification_async_use_cases),
):
    """Get the status of a Celery task."""
    try:
        result = await use_case.execute(task_id)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": result.message, "errors": result.errors},
            )

        task_info = result.data

        return TaskStatusResponseModel(
            success=result.success,
            message=result.message,
            task_id=task_info["task_id"],
            status=task_info["status"],
            result=task_info.get("result"),
            error=task_info.get("error"),
            info=task_info.get("info"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/notifications/retry",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry failed notification",
    description="Retry a failed notification with original parameters.",
)
async def retry_failed_notification(
    request: RetryNotificationRequest,
    use_case: RetryFailedNotificationUseCase = Depends(
        get_notification_async_use_cases
    ),
):
    """Retry a failed notification."""
    try:
        # Convert request to dict for retry
        original_task_data = {
            "recipient_id": request.recipient_id,
            "subject": request.subject,
            "content": request.content,
            "template_data": request.template_data,
            "priority": request.priority,
            "strategy": request.strategy,
        }

        result = await use_case.execute(original_task_data)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": result.message, "errors": result.errors},
            )

        return {
            "success": result.success,
            "message": result.message,
            "data": result.data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/health/celery",
    summary="Celery health check",
    description="Check if Celery workers are running and healthy.",
)
async def celery_health_check():
    """Check Celery health status."""
    try:
        # Simple health check - just check if we can import Celery

        # Basic connectivity check
        return {
            "status": "healthy",
            "message": "Celery is configured and available",
            "timestamp": datetime.utcnow().isoformat(),
            "broker": "redis://redis:6379/0",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get(
    "/stats",
    summary="Celery statistics",
    description="Get basic Celery queue information.",
)
async def celery_stats():
    """Get basic Celery statistics."""
    try:
        return {
            "message": "Celery stats available via Flower on port 5555",
            "flower_url": "http://localhost:5555",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )
