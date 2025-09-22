"""
Simple Celery test endpoints for basic functionality testing.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/celery", tags=["celery-test"])


class SimpleSendNotificationRequest(BaseModel):
    """Simple notification request."""

    recipient_id: str = Field(description="Recipient ID")
    subject: str = Field(description="Subject")
    content: str = Field(description="Content")
    priority: str = Field(default="normal", description="Priority")


class SimpleNotificationResponse(BaseModel):
    """Simple notification response."""

    success: bool
    message: str
    task_id: str | None = None
    timestamp: str


@router.post("/send", response_model=SimpleNotificationResponse)
async def send_notification_simple(request: SimpleSendNotificationRequest):
    """Send notification using Celery (simplified version)."""
    try:
        # Import simple Celery task
        import os
        import sys

        # Add the app directory to Python path
        app_root = os.path.join(os.path.dirname(__file__), "../../../..")
        if app_root not in sys.path:
            sys.path.insert(0, app_root)

        from app.infrastructure.simple_tasks import simple_notification_task

        # Submit task
        task_result = simple_notification_task.delay(
            recipient_id=request.recipient_id,
            subject=request.subject,
            content=request.content,
        )

        return SimpleNotificationResponse(
            success=True,
            message="Notification queued successfully",
            task_id=task_result.id,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        return SimpleNotificationResponse(
            success=False,
            message=f"Failed to queue notification: {str(e)}",
            timestamp=datetime.utcnow().isoformat(),
        )


@router.get("/health")
async def celery_health():
    """Simple Celery health check."""
    try:
        import os
        import sys

        # Add the app directory to Python path
        app_root = os.path.join(os.path.dirname(__file__), "../../../..")
        if app_root not in sys.path:
            sys.path.insert(0, app_root)

        from app.infrastructure.celery_config import celery_app

        return {
            "status": "healthy",
            "message": "Celery configuration loaded",
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": celery_app.main,
            "broker": "redis://redis:6379/0",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/task/{task_id}")
async def get_task_status_simple(task_id: str):
    """Get task status (simplified)."""
    try:
        import os
        import sys

        # Add the app directory to Python path
        app_root = os.path.join(os.path.dirname(__file__), "../../../..")
        if app_root not in sys.path:
            sys.path.insert(0, app_root)

        from app.infrastructure.celery_config import celery_app

        result = celery_app.AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": result.state,
            "result": result.result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
