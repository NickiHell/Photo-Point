#!/usr/bin/env python3
"""
Простой пример использования системы уведомлений.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import User, NotificationMessage
from src.config import setup_logging, create_notification_service, Config
from src.service import DeliveryStrategy


async def main():
    """Основная функция примера."""
    
    # Настраиваем логирование
    setup_logging("INFO")
    
    try:
        # Проверяем конфигурацию
        Config.validate()
        
        # Создаем сервис уведомлений
        service = create_notification_service()
        
        # Получаем статус сервиса
        status = await service.get_service_status()
        print("Статус сервиса уведомлений:")
        print(f"- Общий статус: {status['service_status']}")
        print(f"- Доступно провайдеров: {status['available_providers']} из {status['total_providers']}")
        
        for provider in status['providers']:
            status_icon = "✓" if provider['available'] else "✗"
            print(f"- {status_icon} {provider['name']}")
        
        print("\n" + "="*50 + "\n")
        
        # Создаем тестового пользователя
        user = User(
            id="test_user_1",
            name="Тестовый пользователь",
            email="test@example.com",
            phone="+1234567890",
            telegram_chat_id="123456789"
        )
        
        # Создаем сообщение
        message = NotificationMessage(
            subject="Тестовое уведомление",
            content="Это тестовое сообщение от системы уведомлений. Время отправки: {timestamp}",
            template_data={
                "timestamp": "2024-01-01 12:00:00"
            }
        )
        
        print("Отправка уведомления...")
        print(f"Пользователь: {user.name} ({user.id})")
        print(f"Тема: {message.subject}")
        print(f"Содержание: {message.content}")
        
        # Отправляем уведомление
        report = await service.send_notification(
            user=user,
            message=message,
            strategy=DeliveryStrategy.FIRST_SUCCESS
        )
        
        # Выводим результат
        print(f"\nРезультат доставки:")
        print(f"- Успешно: {report.success}")
        print(f"- Время доставки: {report.delivery_time:.2f} сек")
        print(f"- Количество попыток: {report.total_attempts}")
        
        if report.success:
            print(f"- Успешные провайдеры: {', '.join(report.successful_providers)}")
        
        if report.failed_providers:
            print(f"- Неудачные провайдеры: {', '.join(report.failed_providers)}")
        
        # Подробная информация о попытках
        print(f"\nПодробности попыток:")
        for i, attempt in enumerate(report.attempts, 1):
            status = "✓ Успех" if attempt.result.success else "✗ Ошибка"
            print(f"{i}. {attempt.provider.provider_name}: {status}")
            print(f"   Сообщение: {attempt.result.message}")
            if attempt.result.error:
                print(f"   Ошибка: {attempt.result.error}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())