"""
Основной сервис уведомлений с поддержкой надежной доставки.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.base import NotificationProvider
from src.models import User, NotificationMessage, NotificationResult, NotificationType
from src.exceptions import NotificationError


logger = logging.getLogger(__name__)


class DeliveryStrategy(str, Enum):
    """Стратегии доставки уведомлений."""
    FAIL_FAST = "fail_fast"  # Остановиться при первой ошибке
    TRY_ALL = "try_all"      # Попробовать все доступные провайдеры
    FIRST_SUCCESS = "first_success"  # Остановиться при первом успехе


@dataclass
class NotificationAttempt:
    """Информация о попытке отправки уведомления."""
    provider: NotificationProvider
    result: NotificationResult
    attempt_number: int
    timestamp: float


@dataclass 
class DeliveryReport:
    """Отчет о доставке уведомления."""
    user: User
    message: NotificationMessage
    success: bool
    attempts: List[NotificationAttempt]
    final_result: Optional[NotificationResult] = None
    total_attempts: int = 0
    delivery_time: float = 0.0
    
    @property
    def successful_providers(self) -> List[str]:
        """Список провайдеров, успешно доставивших уведомление."""
        return [
            attempt.provider.provider_name 
            for attempt in self.attempts 
            if attempt.result.success
        ]
    
    @property
    def failed_providers(self) -> List[str]:
        """Список провайдеров, которые не смогли доставить уведомление."""
        return [
            attempt.provider.provider_name 
            for attempt in self.attempts 
            if not attempt.result.success
        ]


class NotificationService:
    """Основной сервис для отправки уведомлений с поддержкой fallback."""
    
    def __init__(self, providers: List[NotificationProvider]):
        """
        Инициализация сервиса уведомлений.
        
        Args:
            providers: Список провайдеров уведомлений в порядке приоритета
        """
        self.providers = providers
        self._validated_providers: Optional[List[NotificationProvider]] = None
    
    async def validate_providers(self) -> List[NotificationProvider]:
        """Проверить все провайдеры и вернуть список рабочих."""
        if self._validated_providers is not None:
            return self._validated_providers
        
        validated = []
        for provider in self.providers:
            try:
                await provider.validate_config()
                validated.append(provider)
                logger.info(f"Provider {provider.provider_name} validated successfully")
            except Exception as e:
                logger.warning(f"Provider {provider.provider_name} validation failed: {e}")
        
        self._validated_providers = validated
        return validated
    
    def get_available_providers(self, user: User) -> List[NotificationProvider]:
        """Получить список провайдеров, доступных для данного пользователя."""
        return [
            provider for provider in self.providers
            if provider.is_user_reachable(user)
        ]
    
    async def send_notification(
        self,
        user: User,
        message: NotificationMessage,
        strategy: DeliveryStrategy = DeliveryStrategy.FIRST_SUCCESS,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> DeliveryReport:
        """
        Отправить уведомление пользователю.
        
        Args:
            user: Пользователь
            message: Сообщение для отправки
            strategy: Стратегия доставки
            max_retries: Максимальное количество повторных попыток для каждого провайдера
            retry_delay: Задержка между повторными попытками в секундах
            
        Returns:
            Отчет о доставке
        """
        start_time = asyncio.get_event_loop().time()
        attempts = []
        
        # Получаем доступных провайдеров для пользователя
        available_providers = self.get_available_providers(user)
        
        if not available_providers:
            logger.warning(f"No available providers for user {user.id}")
            return DeliveryReport(
                user=user,
                message=message,
                success=False,
                attempts=[],
                total_attempts=0,
                delivery_time=0.0
            )
        
        logger.info(f"Sending notification to user {user.id} using {len(available_providers)} providers")
        
        success = False
        final_result = None
        
        for provider in available_providers:
            # Попытки отправки через текущий провайдер
            for attempt_num in range(1, max_retries + 1):
                try:
                    result = await provider.send(user, message)
                    attempt = NotificationAttempt(
                        provider=provider,
                        result=result,
                        attempt_number=attempt_num,
                        timestamp=asyncio.get_event_loop().time()
                    )
                    attempts.append(attempt)
                    
                    if result.success:
                        success = True
                        final_result = result
                        logger.info(f"Notification sent successfully via {provider.provider_name} (attempt {attempt_num})")
                        
                        # В зависимости от стратегии, продолжаем или останавливаемся
                        if strategy == DeliveryStrategy.FIRST_SUCCESS:
                            break
                    else:
                        logger.warning(f"Failed to send via {provider.provider_name} (attempt {attempt_num}): {result.error}")
                        
                        if strategy == DeliveryStrategy.FAIL_FAST:
                            break
                        
                        # Задержка перед повторной попыткой
                        if attempt_num < max_retries:
                            await asyncio.sleep(retry_delay)
                    
                except Exception as e:
                    logger.error(f"Unexpected error with provider {provider.provider_name}: {e}")
                    error_result = NotificationResult(
                        success=False,
                        provider=NotificationType.EMAIL,  # Placeholder, будет переопределено
                        message="Unexpected error",
                        error=str(e)
                    )
                    
                    attempt = NotificationAttempt(
                        provider=provider,
                        result=error_result,
                        attempt_number=attempt_num,
                        timestamp=asyncio.get_event_loop().time()
                    )
                    attempts.append(attempt)
                    
                    if strategy == DeliveryStrategy.FAIL_FAST:
                        break
            
            # Если уведомление было успешно доставлено и стратегия FIRST_SUCCESS
            if success and strategy == DeliveryStrategy.FIRST_SUCCESS:
                break
                
            # Если стратегия FAIL_FAST и была ошибка
            if strategy == DeliveryStrategy.FAIL_FAST and attempts and not attempts[-1].result.success:
                break
        
        end_time = asyncio.get_event_loop().time()
        delivery_time = end_time - start_time
        
        report = DeliveryReport(
            user=user,
            message=message,
            success=success,
            attempts=attempts,
            final_result=final_result,
            total_attempts=len(attempts),
            delivery_time=delivery_time
        )
        
        # Логирование результата
        if success:
            logger.info(f"Notification delivered successfully to user {user.id} in {delivery_time:.2f}s")
        else:
            logger.error(f"Failed to deliver notification to user {user.id} after {len(attempts)} attempts")
        
        return report
    
    async def send_bulk_notifications(
        self,
        users: List[User],
        message: NotificationMessage,
        strategy: DeliveryStrategy = DeliveryStrategy.FIRST_SUCCESS,
        max_concurrent: int = 10
    ) -> List[DeliveryReport]:
        """
        Отправить уведомления множеству пользователей параллельно.
        
        Args:
            users: Список пользователей
            message: Сообщение для отправки
            strategy: Стратегия доставки
            max_concurrent: Максимальное количество параллельных отправок
            
        Returns:
            Список отчетов о доставке
        """
        logger.info(f"Sending bulk notifications to {len(users)} users")
        
        # Создаем семафор для ограничения параллельности
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def send_with_semaphore(user: User) -> DeliveryReport:
            async with semaphore:
                return await self.send_notification(user, message, strategy)
        
        # Отправляем уведомления параллельно
        tasks = [send_with_semaphore(user) for user in users]
        reports = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем исключения
        valid_reports = []
        for i, report in enumerate(reports):
            if isinstance(report, Exception):
                logger.error(f"Error sending notification to user {users[i].id}: {report}")
                # Создаем фиктивный отчет об ошибке
                error_report = DeliveryReport(
                    user=users[i],
                    message=message,
                    success=False,
                    attempts=[],
                    total_attempts=0,
                    delivery_time=0.0
                )
                valid_reports.append(error_report)
            else:
                valid_reports.append(report)
        
        # Статистика
        successful = sum(1 for report in valid_reports if report.success)
        failed = len(valid_reports) - successful
        
        logger.info(f"Bulk notification complete: {successful} successful, {failed} failed")
        
        return valid_reports
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Получить статус сервиса и всех провайдеров."""
        validated_providers = await self.validate_providers()
        
        provider_status = []
        for provider in self.providers:
            is_validated = provider in validated_providers
            provider_info = {
                "name": provider.provider_name,
                "available": is_validated,
                "error": None if is_validated else "Configuration validation failed"
            }
            provider_status.append(provider_info)
        
        return {
            "service_status": "healthy" if validated_providers else "degraded",
            "total_providers": len(self.providers),
            "available_providers": len(validated_providers),
            "providers": provider_status
        }