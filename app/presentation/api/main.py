"""
FastAPI application main module.
"""

from fastapi import APIRouter, FastAPI

# Create FastAPI app
app = FastAPI(
    title="Notification Service API",
    description="Clean Architecture notification service",
    version="1.0.0",
)

# Import and include routers
try:
    from .routes.health import router as health_router

    app.include_router(health_router, prefix="/health", tags=["health"])
    print("Health router loaded")
except ImportError as e:
    print(f"Health router failed: {e}")

# Add admin panel
try:
    from ..admin.routes import router as admin_router

    app.include_router(admin_router, tags=["admin"])
    print("Admin panel loaded")
except ImportError as e:
    print(f"Admin panel failed: {e}")

# Add Celery-based notification endpoints
try:
    from ...infrastructure.celery.tasks import simple_notification_task
    from ...infrastructure.simple_tasks import simple_bulk_notification_task

    celery_router = APIRouter(prefix="/notifications", tags=["notifications"])

    @celery_router.post("/send")
    async def send_notification_celery(
        recipient_id: str,
        message_template: str,
        message_variables: dict | None = None,
        channels: list[str] | None = None,
        priority: str = "MEDIUM",
    ):
        """Send notification via Celery."""
        if channels is None:
            channels = ["email"]
        if message_variables is None:
            message_variables = {}
        try:
            # Submit task to Celery
            result = simple_notification_task.delay(
                recipient_id=recipient_id,
                subject=f"Notification: {message_template}",
                content=str(message_variables),
            )

            return {
                "success": True,
                "message": "Notification queued successfully",
                "task_id": result.id,
                "status": result.status,
                "recipient_id": recipient_id,
                "channels": channels,
                "priority": priority,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @celery_router.post("/send-bulk")
    async def send_bulk_notification_celery(
        recipient_ids: list[str],
        message_template: str,
        message_variables: dict | None = None,
        channels: list[str] | None = None,
        priority: str = "MEDIUM",
    ):
        """Send bulk notification via Celery."""
        if channels is None:
            channels = ["email"]
        if message_variables is None:
            message_variables = {}
        try:
            # Submit bulk task to Celery
            result = simple_bulk_notification_task.delay(
                recipient_ids=recipient_ids,
                subject=f"Bulk Notification: {message_template}",
                content=str(message_variables),
            )

            return {
                "success": True,
                "message": "Bulk notification queued successfully",
                "task_id": result.id,
                "recipients": len(recipient_ids),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to queue bulk notification: {e}",
            }

    app.include_router(celery_router)

except ImportError as e:
    print(f"Celery router failed: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Notification Service API",
        "service": "Notification Service with Celery",
        "version": "1.0.0",
        "celery_enabled": True,
    }
