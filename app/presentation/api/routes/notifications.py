"""
Notification management API endpoints.
"""

from datetime import datetime

try:
    from fastapi import APIRouter, Depends, HTTPException, status
    from pydantic import BaseModel, Field

    from ....application.dto import (
        BulkNotificationRequest,
        SendBulkNotificationDTO,
        SendNotificationDTO,
    )
    from ....application.use_cases.celery_notification_sending import (
        GetTaskStatusUseCase,
    )
    from ....application.use_cases.notification_sending import (
        SendBulkNotificationUseCase,
        SendNotificationUseCase,
    )
    from ....domain.value_objects.notification import (
        NotificationId,
    )
    from ...dependencies import get_notification_use_cases

    router = APIRouter()

    class SendNotificationRequest(BaseModel):
        """Send notification request model."""

        recipient_id: str = Field(description="Recipient user ID")
        message_template: str = Field(description="Message template")
        message_variables: dict = Field(
            default_factory=dict, description="Template variables"
        )
        channels: list[str] = Field(description="Notification channels")
        priority: str = Field(default="MEDIUM", description="Notification priority")
        scheduled_at: str | None = Field(
            None, description="Scheduled delivery time (ISO format)"
        )
        retry_policy: dict = Field(
            default_factory=dict, description="Retry policy configuration"
        )
        metadata: dict = Field(default_factory=dict, description="Additional metadata")

    class SendBulkNotificationRequest(BaseModel):
        """Send bulk notification request model."""

        recipient_ids: list[str] = Field(description="List of recipient user IDs")
        message_template: str = Field(description="Message template")
        message_variables: dict = Field(
            default_factory=dict, description="Template variables"
        )
        channels: list[str] = Field(description="Notification channels")
        priority: str = Field(default="MEDIUM", description="Notification priority")
        scheduled_at: str | None = Field(
            None, description="Scheduled delivery time (ISO format)"
        )
        retry_policy: dict = Field(
            default_factory=dict, description="Retry policy configuration"
        )
        metadata: dict = Field(default_factory=dict, description="Additional metadata")

    class NotificationResponse(BaseModel):
        """Notification response model."""

        id: str = Field(description="Notification ID")
        recipient_id: str = Field(description="Recipient user ID")
        message_template: str = Field(description="Message template")
        channels: list[str] = Field(description="Notification channels")
        priority: str = Field(description="Notification priority")
        scheduled_at: str = Field(description="Scheduled delivery time")
        created_at: str = Field(description="Creation timestamp")
        status: str = Field(description="Notification status")

    class BulkNotificationResponse(BaseModel):
        """Bulk notification response model."""

        notifications: list[NotificationResponse] = Field(
            description="Created notifications"
        )
        total_count: int = Field(description="Total number of notifications created")

    @router.post(
        "/send",
        response_model=NotificationResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def send_notification(
        request: SendNotificationRequest,
        use_case: SendNotificationUseCase = Depends(get_notification_use_cases),
    ):
        """Send a single notification."""
        try:
            scheduled_at = None
            if request.scheduled_at:
                scheduled_at = datetime.fromisoformat(
                    request.scheduled_at.replace("Z", "+00:00")
                )

            dto = SendNotificationDTO(
                recipient_id=request.recipient_id,
                message_template=request.message_template,
                message_variables=request.message_variables,
                channels=request.channels,
                priority=request.priority,
                scheduled_at=scheduled_at,
                retry_policy=request.retry_policy,
                metadata=request.metadata,
            )

            notification_response = await use_case.execute(dto)

            return NotificationResponse(
                id=notification_response.data.get("id", "unknown")
                if notification_response.data
                else "unknown",
                recipient_id=notification_response.data.get("recipient_id")
                if notification_response.data
                else request.recipient_id,
                message_template=notification_response.data.get("message_template")
                if notification_response.data
                else request.message_template,
                channels=notification_response.data.get("channels")
                if notification_response.data
                else request.channels,
                priority=notification_response.data.get("priority")
                if notification_response.data
                else request.priority,
                scheduled_at=notification_response.data.get("scheduled_at")
                if notification_response.data
                else (request.scheduled_at or datetime.now().isoformat()),
                created_at=notification_response.data.get("created_at")
                if notification_response.data
                else datetime.now().isoformat(),
                status=notification_response.data.get("status")
                if notification_response.data
                else "queued",
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @router.post(
        "/send-bulk",
        response_model=BulkNotificationResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def send_bulk_notification(
        request: SendBulkNotificationRequest,
        use_case: SendBulkNotificationUseCase = Depends(get_notification_use_cases),
    ):
        """Send bulk notifications to multiple recipients."""
        try:
            scheduled_at = None
            if request.scheduled_at:
                scheduled_at = datetime.fromisoformat(
                    request.scheduled_at.replace("Z", "+00:00")
                )

            request_obj = SendBulkNotificationDTO(
                recipient_ids=request.recipient_ids,
                message_template=request.message_template,
                message_variables=request.message_variables,
                channels=request.channels,
                priority=request.priority,
                scheduled_at=scheduled_at,
                retry_policy=request.retry_policy,
                metadata=request.metadata,
            )

            bulk_response = await use_case.execute(request_obj)

            notifications = []
            if (
                bulk_response.data
                and isinstance(bulk_response.data, dict)
                and "notifications" in bulk_response.data
            ):
                for n in bulk_response.data["notifications"]:
                    notifications.append(
                        NotificationResponse(
                            id=n.get("id", "unknown"),
                            recipient_id=n.get("recipient_id", "unknown"),
                            message_template=n.get("message_template", ""),
                            channels=n.get("channels", []),
                            priority=n.get("priority", "MEDIUM"),
                            scheduled_at=n.get(
                                "scheduled_at", datetime.now().isoformat()
                            ),
                            created_at=n.get("created_at", datetime.now().isoformat()),
                            status=n.get("status", "queued"),
                        )
                    )

            return BulkNotificationResponse(
                notifications=notifications,
                total_count=bulk_response.data.get("total_count", len(notifications))
                if bulk_response.data
                else len(notifications),
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @router.get("/{notification_id}/status", response_model=dict)
    async def get_notification_status(
        notification_id: str,
        use_case: GetTaskStatusUseCase = Depends(get_notification_use_cases),
    ):
        """Get notification status and delivery information."""
        try:
            status_response = await use_case.execute(notification_id)

            if not status_response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found",
                )

            return {
                "notification_id": getattr(
                    status_response, "notification_id", notification_id
                ),
                "status": getattr(status_response, "status", "unknown"),
                "created_at": getattr(
                    status_response, "created_at", datetime.now()
                ).isoformat()
                if hasattr(status_response, "created_at") and status_response.created_at
                else datetime.now().isoformat(),
                "deliveries": [
                    {
                        "delivery_id": getattr(d, "delivery_id", ""),
                        "channel": getattr(d, "channel", ""),
                        "provider": getattr(d, "provider", ""),
                        "status": getattr(d, "status", ""),
                        "attempts": getattr(d, "attempts", 0),
                        "created_at": getattr(
                            d, "created_at", datetime.now()
                        ).isoformat()
                        if hasattr(d, "created_at") and d.created_at
                        else datetime.now().isoformat(),
                        "completed_at": (
                            d.completed_at.isoformat()
                            if hasattr(d, "completed_at") and d.completed_at is not None
                            else None
                        ),
                    }
                    for d in getattr(status_response, "deliveries", [])
                ],
            }

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

except ImportError:
    # Fallback for when dependencies are not available - create real APIRouter
    from fastapi import APIRouter

    router = APIRouter()
