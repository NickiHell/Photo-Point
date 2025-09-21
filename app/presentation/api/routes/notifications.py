"""
Notification management API endpoints.
"""
from datetime import datetime

try:
    from fastapi import APIRouter, Depends, HTTPException, Query, status
    from pydantic import BaseModel, Field

    from ....application.dto import (
        NotificationStatusResponseDTO,
        SendBulkNotificationDTO,
        SendNotificationDTO,
    )
    from ....application.use_cases.notification_sending import (
        GetNotificationStatusUseCase,
        SendBulkNotificationUseCase,
        SendNotificationUseCase,
    )
    from ....domain.value_objects.notification import (
        NotificationId,
        NotificationPriority,
    )
    from ...dependencies import get_notification_use_cases

    router = APIRouter()


    class SendNotificationRequest(BaseModel):
        """Send notification request model."""
        recipient_id: str = Field(description="Recipient user ID")
        message_template: str = Field(description="Message template")
        message_variables: dict = Field(default_factory=dict, description="Template variables")
        channels: list[str] = Field(description="Notification channels")
        priority: str = Field(default="MEDIUM", description="Notification priority")
        scheduled_at: str | None = Field(None, description="Scheduled delivery time (ISO format)")
        retry_policy: dict = Field(default_factory=dict, description="Retry policy configuration")
        metadata: dict = Field(default_factory=dict, description="Additional metadata")


    class SendBulkNotificationRequest(BaseModel):
        """Send bulk notification request model."""
        recipient_ids: list[str] = Field(description="List of recipient user IDs")
        message_template: str = Field(description="Message template")
        message_variables: dict = Field(default_factory=dict, description="Template variables")
        channels: list[str] = Field(description="Notification channels")
        priority: str = Field(default="MEDIUM", description="Notification priority")
        scheduled_at: str | None = Field(None, description="Scheduled delivery time (ISO format)")
        retry_policy: dict = Field(default_factory=dict, description="Retry policy configuration")
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
        notifications: list[NotificationResponse] = Field(description="Created notifications")
        total_count: int = Field(description="Total number of notifications created")


    @router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
    async def send_notification(
        request: SendNotificationRequest,
        use_case: SendNotificationUseCase = Depends(get_notification_use_cases)
    ):
        """Send a single notification."""
        try:
            scheduled_at = None
            if request.scheduled_at:
                scheduled_at = datetime.fromisoformat(request.scheduled_at.replace('Z', '+00:00'))

            dto = SendNotificationDTO(
                recipient_id=request.recipient_id,
                message_template=request.message_template,
                message_variables=request.message_variables,
                channels=request.channels,
                priority=request.priority,
                scheduled_at=scheduled_at,
                retry_policy=request.retry_policy,
                metadata=request.metadata
            )

            notification_response = await use_case.execute(dto)

            return NotificationResponse(
                id=notification_response.id,
                recipient_id=notification_response.recipient_id,
                message_template=notification_response.message_template,
                channels=notification_response.channels,
                priority=notification_response.priority,
                scheduled_at=notification_response.scheduled_at.isoformat(),
                created_at=notification_response.created_at.isoformat(),
                status=notification_response.status
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


    @router.post("/send-bulk", response_model=BulkNotificationResponse, status_code=status.HTTP_201_CREATED)
    async def send_bulk_notification(
        request: SendBulkNotificationRequest,
        use_case: SendBulkNotificationUseCase = Depends(get_notification_use_cases)
    ):
        """Send bulk notifications to multiple recipients."""
        try:
            scheduled_at = None
            if request.scheduled_at:
                scheduled_at = datetime.fromisoformat(request.scheduled_at.replace('Z', '+00:00'))

            dto = SendBulkNotificationDTO(
                recipient_ids=request.recipient_ids,
                message_template=request.message_template,
                message_variables=request.message_variables,
                channels=request.channels,
                priority=request.priority,
                scheduled_at=scheduled_at,
                retry_policy=request.retry_policy,
                metadata=request.metadata
            )

            bulk_response = await use_case.execute(dto)

            notifications = [
                NotificationResponse(
                    id=n.id,
                    recipient_id=n.recipient_id,
                    message_template=n.message_template,
                    channels=n.channels,
                    priority=n.priority,
                    scheduled_at=n.scheduled_at.isoformat(),
                    created_at=n.created_at.isoformat(),
                    status=n.status
                )
                for n in bulk_response.notifications
            ]

            return BulkNotificationResponse(
                notifications=notifications,
                total_count=bulk_response.total_count
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


    @router.get("/{notification_id}/status", response_model=dict)
    async def get_notification_status(
        notification_id: str,
        use_case: GetNotificationStatusUseCase = Depends(get_notification_use_cases)
    ):
        """Get notification status and delivery information."""
        try:
            status_response = await use_case.execute(NotificationId(notification_id))

            if not status_response:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

            return {
                "notification_id": status_response.notification_id,
                "status": status_response.status,
                "created_at": status_response.created_at.isoformat(),
                "deliveries": [
                    {
                        "delivery_id": d.delivery_id,
                        "channel": d.channel,
                        "provider": d.provider,
                        "status": d.status,
                        "attempts": d.attempts,
                        "created_at": d.created_at.isoformat(),
                        "completed_at": d.completed_at.isoformat() if d.completed_at else None
                    }
                    for d in status_response.deliveries
                ]
            }

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

except ImportError:
    # Mock router for when FastAPI is not available
    class MockRouter:
        def post(self, path: str, **kwargs):
            def decorator(func):
                return func
            return decorator

        def get(self, path: str, **kwargs):
            def decorator(func):
                return func
            return decorator

    router = MockRouter()
