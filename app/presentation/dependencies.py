"""
Dependency injection container and dependency providers.
"""
from typing import AsyncGenerator

try:
    from dependency_injector import containers, providers
    from dependency_injector.wiring import Provide, inject
    
    from ..application.use_cases.user_management import CreateUserUseCase, GetUserUseCase, UpdateUserUseCase, DeleteUserUseCase
    from ..application.use_cases.notification_sending import SendNotificationUseCase, SendBulkNotificationUseCase, GetNotificationStatusUseCase
    from ..domain.services import NotificationProviderInterface
    from ..infrastructure.config import get_config
    from ..infrastructure.repositories.memory_repositories import InMemoryUserRepository, InMemoryNotificationRepository, InMemoryDeliveryRepository
    from ..infrastructure.adapters.email_adapter import EmailNotificationAdapter
    from ..infrastructure.adapters.sms_adapter import SMSNotificationAdapter
    from ..infrastructure.adapters.telegram_adapter import TelegramNotificationAdapter
    
    
    class Container(containers.DeclarativeContainer):
        """Dependency injection container."""
        
        # Configuration
        config = providers.Singleton(get_config)
        
        # Repositories
        user_repository = providers.Singleton(InMemoryUserRepository)
        notification_repository = providers.Singleton(InMemoryNotificationRepository)
        delivery_repository = providers.Singleton(InMemoryDeliveryRepository)
        
        # Notification providers
        email_provider = providers.Singleton(
            EmailNotificationAdapter,
            config=config.provided.email
        )
        sms_provider = providers.Singleton(
            SMSNotificationAdapter,
            config=config.provided.sms
        )
        telegram_provider = providers.Singleton(
            TelegramNotificationAdapter,
            config=config.provided.telegram
        )
        
        # Provider registry
        notification_providers = providers.Dict(
            email=email_provider,
            sms=sms_provider,
            telegram=telegram_provider
        )
        
        # Use cases - User Management
        create_user_use_case = providers.Factory(
            CreateUserUseCase,
            user_repository=user_repository
        )
        get_user_use_case = providers.Factory(
            GetUserUseCase,
            user_repository=user_repository
        )
        update_user_use_case = providers.Factory(
            UpdateUserUseCase,
            user_repository=user_repository
        )
        delete_user_use_case = providers.Factory(
            DeleteUserUseCase,
            user_repository=user_repository
        )
        
        # Use cases - Notification Sending
        send_notification_use_case = providers.Factory(
            SendNotificationUseCase,
            user_repository=user_repository,
            notification_repository=notification_repository,
            delivery_repository=delivery_repository,
            notification_providers=notification_providers
        )
        send_bulk_notification_use_case = providers.Factory(
            SendBulkNotificationUseCase,
            user_repository=user_repository,
            notification_repository=notification_repository,
            delivery_repository=delivery_repository,
            notification_providers=notification_providers
        )
        get_notification_status_use_case = providers.Factory(
            GetNotificationStatusUseCase,
            notification_repository=notification_repository,
            delivery_repository=delivery_repository
        )
    
    
    # Global container instance
    container = Container()
    
    
    def get_container() -> Container:
        """Get the global container instance."""
        return container
    
    
    # Dependency providers for FastAPI
    def get_user_use_cases():
        """Get user management use cases."""
        return {
            'create': container.create_user_use_case(),
            'get': container.get_user_use_case(),
            'update': container.update_user_use_case(),
            'delete': container.delete_user_use_case()
        }
    
    
    def get_notification_use_cases():
        """Get notification use cases."""
        return {
            'send': container.send_notification_use_case(),
            'send_bulk': container.send_bulk_notification_use_case(),
            'get_status': container.get_notification_status_use_case()
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
    
    def get_container():
        return MockContainer()
    
    def get_user_use_cases():
        return {}
    
    def get_notification_use_cases():
        return {}
    
    def get_user_repository():
        return None
    
    def get_notification_repository():
        return None
    
    def get_delivery_repository():
        return None