#!/usr/bin/env python3
"""
Тест отказоустойчивости системы уведомлений.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import User, NotificationMessage
from src.config import setup_logging, create_notification_service, Config
from src.service import DeliveryStrategy


class FailingProvider:
    """Мок-провайдер, который всегда возвращает ошибку (для тестирования fallback)."""
    
    def __init__(self, name: str, should_fail: bool = True):
        self.name = name
        self.should_fail = should_fail
    
    async def send(self, user, message):
        from src.models import NotificationResult, NotificationType
        
        if self.should_fail:
            return NotificationResult(
                success=False,
                provider=NotificationType.EMAIL,
                message=f"{self.name} intentionally failed",
                error="Simulated failure for testing"
            )
        else:
            return NotificationResult(
                success=True,
                provider=NotificationType.EMAIL,
                message=f"{self.name} succeeded",
                metadata={"test": True}
            )
    
    def is_user_reachable(self, user):
        return True
    
    @property
    def provider_name(self):
        return self.name
    
    async def validate_config(self):
        return True


async def test_fallback_behavior():
    """Тестирование fallback поведения."""
    
    print("Тест 1: Проверка fallback механизма")
    print("="*50)
    
    from src.service import NotificationService
    
    # Создаем провайдеров: первые два будут падать, третий сработает
    providers = [
        FailingProvider("Primary (Failing)", should_fail=True),
        FailingProvider("Secondary (Failing)", should_fail=True),
        FailingProvider("Backup (Working)", should_fail=False),
    ]
    
    service = NotificationService(providers)
    
    user = User(
        id="test_user",
        name="Тестовый пользователь",
        email="test@example.com"
    )
    
    message = NotificationMessage(
        subject="Fallback тест",
        content="Тестирование отказоустойчивости системы"
    )
    
    # Тестируем стратегию FIRST_SUCCESS
    print("Стратегия: FIRST_SUCCESS")
    report = await service.send_notification(
        user=user,
        message=message,
        strategy=DeliveryStrategy.FIRST_SUCCESS
    )
    
    print(f"Результат: {report.success}")
    print(f"Попыток: {report.total_attempts}")
    print(f"Время: {report.delivery_time:.3f} сек")
    
    for i, attempt in enumerate(report.attempts, 1):
        status = "✓" if attempt.result.success else "✗"
        print(f"  {i}. {attempt.provider.provider_name}: {status} - {attempt.result.message}")
    
    print()


async def test_all_strategies():
    """Тестирование всех стратегий доставки."""
    
    print("Тест 2: Сравнение стратегий доставки")
    print("="*50)
    
    from src.service import NotificationService
    
    # Создаем смешанных провайдеров
    providers = [
        FailingProvider("Provider 1", should_fail=True),
        FailingProvider("Provider 2", should_fail=False),
        FailingProvider("Provider 3", should_fail=False),
    ]
    
    service = NotificationService(providers)
    
    user = User(
        id="test_user",
        name="Тестовый пользователь",
        email="test@example.com"
    )
    
    message = NotificationMessage(
        subject="Стратегии доставки",
        content="Тестирование разных стратегий доставки"
    )
    
    strategies = [
        DeliveryStrategy.FIRST_SUCCESS,
        DeliveryStrategy.TRY_ALL,
        DeliveryStrategy.FAIL_FAST
    ]
    
    for strategy in strategies:
        print(f"\nСтратегия: {strategy}")
        report = await service.send_notification(
            user=user,
            message=message,
            strategy=strategy
        )
        
        print(f"  Результат: {report.success}")
        print(f"  Попыток: {report.total_attempts}")
        print(f"  Время: {report.delivery_time:.3f} сек")
        print(f"  Успешные: {report.successful_providers}")
        print(f"  Неудачные: {report.failed_providers}")


async def test_retry_mechanism():
    """Тестирование механизма повторных попыток."""
    
    print("\n\nТест 3: Механизм повторных попыток")
    print("="*50)
    
    from src.service import NotificationService
    
    class FluctuatingProvider:
        """Провайдер, который падает несколько раз, а потом работает."""
        
        def __init__(self, name: str, fail_times: int = 2):
            self.name = name
            self.fail_times = fail_times
            self.attempt_count = 0
        
        async def send(self, user, message):
            from src.models import NotificationResult, NotificationType
            
            self.attempt_count += 1
            
            if self.attempt_count <= self.fail_times:
                return NotificationResult(
                    success=False,
                    provider=NotificationType.EMAIL,
                    message=f"{self.name} failed (attempt {self.attempt_count})",
                    error=f"Temporary failure {self.attempt_count}/{self.fail_times}"
                )
            else:
                return NotificationResult(
                    success=True,
                    provider=NotificationType.EMAIL,
                    message=f"{self.name} succeeded after {self.attempt_count} attempts"
                )
        
        def is_user_reachable(self, user):
            return True
        
        @property
        def provider_name(self):
            return self.name
        
        async def validate_config(self):
            return True
    
    provider = FluctuatingProvider("Unreliable Provider", fail_times=2)
    service = NotificationService([provider])
    
    user = User(
        id="test_user",
        name="Тестовый пользователь",
        email="test@example.com"
    )
    
    message = NotificationMessage(
        subject="Retry тест",
        content="Тестирование механизма повторных попыток"
    )
    
    # Тестируем с различным количеством retry
    for max_retries in [1, 2, 3, 5]:
        provider.attempt_count = 0  # Сброс счетчика
        
        print(f"\nМаксимум повторных попыток: {max_retries}")
        report = await service.send_notification(
            user=user,
            message=message,
            strategy=DeliveryStrategy.FIRST_SUCCESS,
            max_retries=max_retries
        )
        
        print(f"  Результат: {report.success}")
        print(f"  Попыток: {report.total_attempts}")
        
        for i, attempt in enumerate(report.attempts, 1):
            status = "✓" if attempt.result.success else "✗"
            print(f"    {i}. {status} - {attempt.result.message}")


async def main():
    """Основная функция тестирования."""
    
    # Настраиваем логирование
    setup_logging("WARNING")  # Только предупреждения, чтобы не засорять вывод
    
    print("Тестирование отказоустойчивости системы уведомлений")
    print("="*60)
    
    try:
        await test_fallback_behavior()
        await test_all_strategies()
        await test_retry_mechanism()
        
        print("\n\n" + "="*60)
        print("Все тесты завершены успешно!")
        
    except Exception as e:
        print(f"Ошибка во время тестирования: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())