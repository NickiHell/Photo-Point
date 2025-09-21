#!/usr/bin/env python3
"""
Пример массовой отправки уведомлений.
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
    """Основная функция примера массовой отправки."""
    
    # Настраиваем логирование
    setup_logging("INFO")
    
    try:
        # Создаем сервис уведомлений
        service = create_notification_service()
        
        # Создаем список тестовых пользователей
        users = [
            User(
                id="user_1",
                name="Анна Иванова",
                email="anna@example.com",
                phone="+1234567890",
                telegram_chat_id="111111111"
            ),
            User(
                id="user_2",
                name="Петр Петров",
                email="peter@example.com",
                phone="+1234567891"
                # У этого пользователя нет Telegram
            ),
            User(
                id="user_3",
                name="Мария Сидорова",
                telegram_chat_id="333333333"
                # У этого пользователя есть только Telegram
            ),
            User(
                id="user_4",
                name="Алексей Смирнов",
                # У этого пользователя нет контактных данных
            )
        ]
        
        # Создаем сообщение для массовой отправки
        message = NotificationMessage(
            subject="Важное объявление",
            content="""
Уважаемый {user_name}!

Уведомляем вас о важном событии, которое состоится {event_date}.

Пожалуйста, подтвердите ваше участие до {deadline}.

С уважением,
Команда организаторов
            """.strip(),
            template_data={
                "event_date": "15 января 2024 года",
                "deadline": "10 января 2024 года"
            }
        )
        
        print(f"Массовая отправка уведомления для {len(users)} пользователей...")
        print(f"Тема: {message.subject}")
        
        # Персонализируем сообщения для каждого пользователя
        personalized_reports = []
        
        for user in users:
            # Создаем персонализированное сообщение
            personalized_message = NotificationMessage(
                subject=message.subject,
                content=message.content,
                template_data={
                    **message.template_data,
                    "user_name": user.name
                }
            )
            
            # Отправляем уведомление
            report = await service.send_notification(
                user=user,
                message=personalized_message,
                strategy=DeliveryStrategy.FIRST_SUCCESS
            )
            
            personalized_reports.append(report)
        
        # Альтернативный способ: массовая отправка через bulk метод
        print("\n" + "="*60)
        print("Альтернатива: использование bulk_notifications")
        
        # Для bulk отправки используем общий шаблон
        bulk_reports = await service.send_bulk_notifications(
            users=users,
            message=NotificationMessage(
                subject="Рассылка через Bulk API",
                content="Это сообщение отправлено через массовую рассылку пользователю {user_name}.",
                template_data={"user_name": "Участник"}  # Будет одинаково для всех
            ),
            strategy=DeliveryStrategy.FIRST_SUCCESS,
            max_concurrent=5
        )
        
        # Анализируем результаты
        successful_count = sum(1 for report in bulk_reports if report.success)
        failed_count = len(bulk_reports) - successful_count
        
        print(f"\nРезультаты массовой отправки:")
        print(f"- Всего пользователей: {len(users)}")
        print(f"- Успешно доставлено: {successful_count}")
        print(f"- Ошибок доставки: {failed_count}")
        
        # Подробная статистика по пользователям
        print(f"\nПодробная статистика:")
        for i, (user, report) in enumerate(zip(users, bulk_reports), 1):
            status = "✓" if report.success else "✗"
            print(f"{i}. {user.name} ({user.id}): {status}")
            
            if report.success:
                print(f"   Провайдер: {report.successful_providers[0]}")
                print(f"   Время: {report.delivery_time:.2f} сек")
            else:
                print(f"   Ошибка: Недоступны каналы связи")
            
            # Показываем доступные каналы для каждого пользователя
            available_channels = []
            if user.email:
                available_channels.append("Email")
            if user.phone:
                available_channels.append("SMS")
            if user.telegram_chat_id:
                available_channels.append("Telegram")
            
            if available_channels:
                print(f"   Доступные каналы: {', '.join(available_channels)}")
            else:
                print(f"   Доступные каналы: Нет")
        
        # Статистика по провайдерам
        provider_stats = {}
        for report in bulk_reports:
            for provider in report.successful_providers:
                provider_stats[provider] = provider_stats.get(provider, 0) + 1
        
        if provider_stats:
            print(f"\nСтатистика по провайдерам:")
            for provider, count in provider_stats.items():
                print(f"- {provider}: {count} сообщений")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())