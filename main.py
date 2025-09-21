#!/usr/bin/env python3
"""
Главный файл для запуска и демонстрации системы уведомлений.
"""

import asyncio
import os
import sys

# Добавляем путь к проекту для импортов
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

async def main():
    """Главная функция демонстрации."""
    print("🔔 Система уведомлений")
    print("=" * 50)
    print()

    try:
        # Импортируем модули после добавления пути
        from src.config import Config, create_notification_service, setup_logging
        from src.models import NotificationMessage, User

        # Настраиваем логирование
        setup_logging("INFO")

        print("✅ Модули загружены успешно")

        # Показываем конфигурацию
        config_summary = Config.get_summary()
        print("📋 Конфигурация:")
        print(f"   - Email настроен: {config_summary['email_configured']}")
        print(f"   - SMS настроен: {config_summary['sms_configured']}")
        print(f"   - Telegram настроен: {config_summary['telegram_configured']}")
        print(f"   - Порядок провайдеров: {', '.join(config_summary['provider_order'])}")
        print()

        # Проверяем, что хотя бы один провайдер настроен
        if not any([
            config_summary['email_configured'],
            config_summary['sms_configured'],
            config_summary['telegram_configured']
        ]):
            print("⚠️  Не настроен ни один провайдер!")
            print("   Пожалуйста, скопируйте .env.example в .env и заполните необходимые поля.")
            print()
            print("📖 Для запуска демонстрации можно использовать:")
            print("   python examples/reliability_test.py  # Тест с мок-провайдерами")
            return 1

        # Создаем сервис уведомлений
        try:
            service = create_notification_service()
            print("✅ Сервис уведомлений создан")

            # Проверяем статус всех провайдеров
            status = await service.get_service_status()
            print(f"🏥 Статус сервиса: {status['service_status']}")
            print(f"   Доступно провайдеров: {status['available_providers']}/{status['total_providers']}")

            for provider in status['providers']:
                icon = "✅" if provider['available'] else "❌"
                print(f"   {icon} {provider['name']}")
                if provider['error']:
                    print(f"      Ошибка: {provider['error']}")

            print()

            if status['available_providers'] == 0:
                print("❌ Ни один провайдер не доступен!")
                print("   Проверьте настройки в .env файле")
                return 1

            # Создаем тестового пользователя
            user = User(
                id="demo_user",
                name="Демо Пользователь",
                email="demo@example.com",  # Может не работать без настройки
                phone="+1234567890",       # Может не работать без Twilio
                telegram_chat_id="123456789"  # Может не работать без бота
            )

            # Создаем демонстрационное сообщение
            message = NotificationMessage(
                subject="🎉 Добро пожаловать в систему уведомлений!",
                content="""
Здравствуйте, {user_name}!

Это демонстрационное сообщение от системы уведомлений.

🔹 Время отправки: {timestamp}
🔹 Ваш ID: {user_id}

Система поддерживает:
✅ Email уведомления
✅ SMS сообщения
✅ Telegram уведомления
✅ Надежную доставку с fallback
✅ Массовые рассылки

С уважением,
Система уведомлений
                """.strip(),
                template_data={
                    "user_name": user.name,
                    "user_id": user.id,
                    "timestamp": "21 сентября 2025 г."
                }
            )

            print("📤 Отправляем демонстрационное уведомление...")
            print(f"   Получатель: {user.name}")
            print(f"   Тема: {message.subject}")

            # Отправляем уведомление
            from src.service import DeliveryStrategy

            report = await service.send_notification(
                user=user,
                message=message,
                strategy=DeliveryStrategy.FIRST_SUCCESS
            )

            print()
            print("📊 Результат отправки:")
            print(f"   Успешно: {'✅ Да' if report.success else '❌ Нет'}")
            print(f"   Время доставки: {report.delivery_time:.2f} сек")
            print(f"   Попыток: {report.total_attempts}")

            if report.success:
                print(f"   Успешные провайдеры: {', '.join(report.successful_providers)}")
                print(f"   Финальный результат: {report.final_result.message}")

            if report.failed_providers:
                print(f"   Неудачные провайдеры: {', '.join(report.failed_providers)}")

            print()
            print("🔍 Детализация попыток:")
            for i, attempt in enumerate(report.attempts, 1):
                status_icon = "✅" if attempt.result.success else "❌"
                print(f"   {i}. {attempt.provider.provider_name}: {status_icon}")
                print(f"      Сообщение: {attempt.result.message}")
                if attempt.result.error:
                    print(f"      Ошибка: {attempt.result.error}")

            print()
            if report.success:
                print("🎉 Демонстрация завершена успешно!")
            else:
                print("⚠️  Демонстрация завершена с ошибками")
                print("   Это нормально, если провайдеры не настроены полностью")

            print()
            print("📚 Дополнительные примеры:")
            print("   python examples/simple_example.py     # Простой пример")
            print("   python examples/bulk_example.py       # Массовая отправка")
            print("   python examples/reliability_test.py   # Тест надежности")

        except Exception as e:
            print(f"❌ Ошибка при создании сервиса: {e}")
            return 1

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("   Убедитесь, что установлены все зависимости: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return 1

    return 0


if __name__ == "__main__":
    print("Запуск системы уведомлений...")
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Работа прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
