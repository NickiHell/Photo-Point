"""
Dependency injection container and dependency providers for Tortoise ORM.
"""

from typing import Any

try:
    from dependency_injector import containers, providers

    from ..application.use_cases.celery_notification_sending import (
        GetTaskStatusUseCase,
        RetryFailedNotificationUseCase,
        SendBulkNotificationAsyncUseCase,
        SendNotificationAsyncUseCase,
    )
    from ..application.use_cases.notification_sending import (
        SendBulkNotificationUseCase,
        SendNotificationUseCase,
    )
    from ..application.use_cases.user_management import (
        CreateUserUseCase,
        GetUserUseCase,
        UpdateUserUseCase,
    )
    from ..infrastructure.adapters.email_adapter import EmailNotificationAdapter
    from ..infrastructure.adapters.sms_adapter import SMSNotificationAdapter
    from ..infrastructure.adapters.telegram_adapter import TelegramNotificationAdapter
    from ..infrastructure.config import get_config
    from ..infrastructure.repositories.tortoise_delivery_repository import (
        TortoiseDeliveryRepository,
    )
    from ..infrastructure.repositories.tortoise_notification_repository import (
        TortoiseNotificationRepository,
    )
    from ..infrastructure.repositories.tortoise_user_repository import (
        TortoiseUserRepository,
    )

    class Container(containers.DeclarativeContainer):
        """Dependency injection container."""

        # Configuration
        config = providers.Singleton(get_config)

        # Repositories - Tortoise ORM implementation
        user_repository = providers.Singleton(TortoiseUserRepository)
        notification_repository = providers.Singleton(TortoiseNotificationRepository)
        delivery_repository = providers.Singleton(TortoiseDeliveryRepository)

        # Notification providers
        email_provider = providers.Singleton(
            EmailNotificationAdapter, config=config.provided.email
        )
        sms_provider = providers.Singleton(
            SMSNotificationAdapter, config=config.provided.sms
        )
        telegram_provider = providers.Singleton(
            TelegramNotificationAdapter, config=config.provided.telegram
        )

        # Provider registry
        notification_providers = providers.Dict(
            email=email_provider, sms=sms_provider, telegram=telegram_provider
        )

        # Use cases - User Management
        create_user_use_case = providers.Factory(
            CreateUserUseCase, user_repository=user_repository
        )
        get_user_use_case = providers.Factory(
            GetUserUseCase, user_repository=user_repository
        )
        update_user_use_case = providers.Factory(
            UpdateUserUseCase, user_repository=user_repository
        )

        # Use cases - Notification Sending
        send_notification_use_case = providers.Factory(
            SendNotificationUseCase,
            user_repository=user_repository,
            notification_repository=notification_repository,
            delivery_repository=delivery_repository,
            notification_providers=notification_providers,
        )
        send_bulk_notification_use_case = providers.Factory(
            SendBulkNotificationUseCase,
            user_repository=user_repository,
            notification_repository=notification_repository,
            delivery_repository=delivery_repository,
            notification_providers=notification_providers,
        )
        # Use cases - Celery-based Async Notification Sending
        send_notification_async_use_case = providers.Factory(
            SendNotificationAsyncUseCase, user_repository=user_repository
        )
        send_bulk_notification_async_use_case = providers.Factory(
            SendBulkNotificationAsyncUseCase, user_repository=user_repository
        )
        get_task_status_use_case = providers.Factory(GetTaskStatusUseCase)
        retry_failed_notification_use_case = providers.Factory(
            RetryFailedNotificationUseCase
        )

        get_notification_status_use_case: providers.Factory = providers.Factory(
            # TODO: Implement GetNotificationStatusUseCase
            # GetNotificationStatusUseCase,
            # notification_repository=notification_repository,
            # delivery_repository=delivery_repository
        )

    # Global container instance
    container = Container()

    def get_container() -> Any:
        """Get the global container instance."""
        return container

    # Dependency providers for FastAPI
    def get_create_user_use_case():
        """Get create user use case."""
        return container.create_user_use_case()

    def get_get_user_use_case():
        """Get get user use case."""
        return container.get_user_use_case()

    def get_update_user_use_case():
        """Get update user use case."""
        return container.update_user_use_case()

    def get_user_use_cases():
        """Get user management use cases."""
        return {
            "create": container.create_user_use_case(),
            "get": container.get_user_use_case(),
            "update": container.update_user_use_case(),
        }

    def get_notification_use_cases():
        """Get notification use cases."""
        return {
            "send": container.send_notification_use_case(),
            "send_bulk": container.send_bulk_notification_use_case(),
            "get_status": container.get_notification_status_use_case(),
        }

    def get_notification_async_use_cases():
        """Get async notification use cases (Celery-based)."""
        return {
            "send_async": container.send_notification_async_use_case(),
            "send_bulk_async": container.send_bulk_notification_async_use_case(),
            "get_task_status": container.get_task_status_use_case(),
            "retry_failed": container.retry_failed_notification_use_case(),
        }

    def get_delivery_use_cases():
        """Get delivery use cases."""
        return {
            "get_status": container.get_notification_status_use_case(),
            "get_statistics": None,  # TODO: Implement
        }

    def get_user_repository():
        """Get user repository."""
        return container.user_repository()

    def get_notification_repository():
        """Get notification repository."""
        return container.notification_repository()

    def get_delivery_repository():
        """Get delivery repository."""
        return container.delivery_repository()

except ImportError:
    # Fallback when dependency-injector is not available
    class MockContainer:
        def init_resources(self):
            pass

        def shutdown_resources(self):
            pass

    def get_container() -> Any:
        return MockContainer()

    def get_user_use_cases():
        return {}

    def get_notification_use_cases():
        return {}

    def get_notification_async_use_cases():
        return {}

    def get_delivery_use_cases():
        return {}

    def get_user_repository():
        return None

    def get_notification_repository():
        return None

    def get_delivery_repository():
        return None
