"""
Simple Celery tasks for testing without complex dependencies.
"""

from datetime import datetime
from typing import Any

from celery import Task
from structlog import get_logger

from .celery_config import celery_app

logger = get_logger()


class SimpleTask(Task):
    """Simple base task class."""

    def on_success(self, retval, task_id, args, kwargs):
        logger.info("Task succeeded", task_id=task_id)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("Task failed", task_id=task_id, error=str(exc))


@celery_app.task(
    bind=True,
    base=SimpleTask,
    name="app.infrastructure.simple_tasks.simple_notification_task",
)
def simple_notification_task(
    self, recipient_id: str, subject: str, content: str, **kwargs
) -> dict[str, Any]:
    """
    Simple notification task for testing.

    This is a basic version that just simulates notification processing
    without complex dependencies.
    """
    logger.info(
        "Processing simple notification task",
        task_id=self.request.id,
        recipient_id=recipient_id,
        subject=subject,
    )

    try:
        # Simulate processing time
        import time

        time.sleep(1)

        # Simulate success/failure based on recipient_id
        if "fail" in recipient_id.lower():
            raise Exception(f"Simulated failure for recipient {recipient_id}")

        # Return success result
        result = {
            "success": True,
            "message": "Notification processed successfully",
            "task_id": self.request.id,
            "recipient_id": recipient_id,
            "subject": subject,
            "processed_at": datetime.utcnow().isoformat(),
            "delivery_attempts": [
                {
                    "provider": "email",
                    "status": "success",
                    "attempted_at": datetime.utcnow().isoformat(),
                }
            ],
        }

        logger.info(
            "Simple notification task completed successfully",
            task_id=self.request.id,
            recipient_id=recipient_id,
        )

        return result

    except Exception as exc:
        logger.error(
            "Simple notification task failed",
            task_id=self.request.id,
            recipient_id=recipient_id,
            error=str(exc),
        )

        # Return failure result
        return {
            "success": False,
            "message": f"Task failed: {str(exc)}",
            "task_id": self.request.id,
            "recipient_id": recipient_id,
            "error": str(exc),
            "processed_at": datetime.utcnow().isoformat(),
        }


@celery_app.task(
    bind=True,
    base=SimpleTask,
    name="app.infrastructure.simple_tasks.simple_bulk_notification_task",
)
def simple_bulk_notification_task(
    self, recipient_ids: list[str], subject: str, content: str, max_concurrent: int = 10
) -> dict[str, Any]:
    """
    Simple bulk notification task.

    Spawns individual notification tasks for better parallelism.
    """
    logger.info(
        "Processing simple bulk notification task",
        task_id=self.request.id,
        recipient_count=len(recipient_ids),
        subject=subject,
    )

    try:
        # Create individual tasks for each recipient
        spawned_tasks = []

        for recipient_id in recipient_ids[:max_concurrent]:  # Limit concurrency
            task_result = simple_notification_task.delay(
                recipient_id=recipient_id, subject=subject, content=content
            )
            spawned_tasks.append(
                {"task_id": task_result.id, "recipient_id": recipient_id}
            )

        result = {
            "success": True,
            "message": f"Bulk notification spawned {len(spawned_tasks)} tasks",
            "task_id": self.request.id,
            "recipient_count": len(recipient_ids),
            "spawned_tasks": spawned_tasks,
            "processed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Simple bulk notification task completed",
            task_id=self.request.id,
            spawned_tasks=len(spawned_tasks),
        )

        return result

    except Exception as exc:
        logger.error(
            "Simple bulk notification task failed",
            task_id=self.request.id,
            error=str(exc),
        )

        return {
            "success": False,
            "message": f"Bulk task failed: {str(exc)}",
            "task_id": self.request.id,
            "recipient_count": len(recipient_ids),
            "error": str(exc),
            "processed_at": datetime.utcnow().isoformat(),
        }


@celery_app.task(
    bind=True, base=SimpleTask, name="app.infrastructure.simple_tasks.health_check_task"
)
def health_check_task(self) -> dict[str, Any]:
    """Health check task to verify Celery is working."""
    logger.info("Processing health check task", task_id=self.request.id)

    return {
        "success": True,
        "message": "Celery is working correctly",
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": self.request.hostname,
    }
