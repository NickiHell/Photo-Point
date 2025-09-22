"""
Celery configuration for the notification service.
"""

import os

from celery import Celery
from kombu import Queue
from structlog import get_logger

logger = get_logger()

# Redis connection configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery instance
celery_app = Celery(
    "notification_service",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.infrastructure.simple_tasks"],  # Updated to simple_tasks
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.infrastructure.simple_tasks.simple_notification_task": {
            "queue": "notifications"
        },
        "app.infrastructure.simple_tasks.simple_bulk_notification_task": {
            "queue": "bulk_notifications"
        },
        "app.infrastructure.simple_tasks.health_check_task": {"queue": "celery"},
    },
    # Queue definitions
    task_queues=(
        Queue("notifications", routing_key="notifications"),
        Queue("bulk_notifications", routing_key="bulk_notifications"),
        Queue("retries", routing_key="retries"),
        Queue("celery", routing_key="celery"),  # Default queue
    ),
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task result settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_policy": {"timeout": 5.0},
    },
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Rate limiting
    task_annotations={
        "app.infrastructure.simple_tasks.simple_notification_task": {
            "rate_limit": "100/s"
        },
        "app.infrastructure.simple_tasks.simple_bulk_notification_task": {
            "rate_limit": "10/s"
        },
        "app.infrastructure.simple_tasks.health_check_task": {"rate_limit": "1000/s"},
    },
    # Monitoring
    task_send_sent_event=True,
    task_track_started=True,
    worker_send_task_events=True,
    # Error handling
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    # Beat schedule for periodic tasks (if needed)
    beat_schedule={
        "health-check": {
            "task": "app.infrastructure.simple_tasks.health_check_task",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)


# Health check function
def check_celery_health() -> bool:
    """Check if Celery is healthy by inspecting active workers."""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats is None:
            return False
        return len(stats) > 0
    except Exception as e:
        logger.error("Celery health check failed", error=str(e))
        return False


# Task discovery
celery_app.autodiscover_tasks(
    [
        "app.infrastructure.simple_tasks"  # Use simple tasks instead
    ]
)

logger.info(
    "Celery configured",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    queues=["notifications", "bulk_notifications", "retries", "celery"],
)
