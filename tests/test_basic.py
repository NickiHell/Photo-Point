"""
Базовые тесты для системы уведомлений.
"""

import asyncio
import os
import sys
import unittest

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base import NotificationProvider
from src.models import NotificationMessage, NotificationResult, NotificationType, User
from src.service import DeliveryStrategy, NotificationService


class MockProvider(NotificationProvider):
    """Мок-провайдер для тестирования."""

    def __init__(self, name: str, success: bool = True, reachable_check=None):
        self.name = name
        self.success = success
        self.reachable_check = reachable_check or (lambda user: True)
        self.call_count = 0

    async def send(self, user, message):
        self.call_count += 1
        return NotificationResult(
            success=self.success,
            provider=NotificationType.EMAIL,
            message=f"{self.name} {'succeeded' if self.success else 'failed'}",
            error=None if self.success else "Mock error"
        )

    def is_user_reachable(self, user):
        return self.reachable_check(user)

    @property
    def provider_name(self):
        return self.name

    async def validate_config(self):
        return True


class TestNotificationService(unittest.TestCase):
    """Тесты для NotificationService."""

    def setUp(self):
        """Подготовка тестов."""
        self.user = User(
            id="test_user",
            name="Test User",
            email="test@example.com",
            phone="+1234567890",
            telegram_chat_id="123456789"
        )

        self.message = NotificationMessage(
            subject="Test Subject",
            content="Test content"
        )

    def test_first_success_strategy(self):
        """Тест стратегии FIRST_SUCCESS."""
        providers = [
            MockProvider("Provider1", success=False),
            MockProvider("Provider2", success=True),
            MockProvider("Provider3", success=True)
        ]

        service = NotificationService(providers)

        async def run_test():
            report = await service.send_notification(
                self.user,
                self.message,
                DeliveryStrategy.FIRST_SUCCESS
            )

            self.assertTrue(report.success)
            self.assertEqual(report.total_attempts, 4)  # 3 попытки для Provider1 + 1 для Provider2
            self.assertEqual(providers[0].call_count, 3)  # 3 неудачных попытки
            self.assertEqual(providers[1].call_count, 1)  # 1 успешная попытка
            self.assertEqual(providers[2].call_count, 0)  # Не должен быть вызван

        asyncio.run(run_test())

    def test_try_all_strategy(self):
        """Тест стратегии TRY_ALL."""
        providers = [
            MockProvider("Provider1", success=False),
            MockProvider("Provider2", success=True),
            MockProvider("Provider3", success=True)
        ]

        service = NotificationService(providers)

        async def run_test():
            report = await service.send_notification(
                self.user,
                self.message,
                DeliveryStrategy.TRY_ALL
            )

            self.assertTrue(report.success)
            self.assertEqual(report.total_attempts, 9)  # 3 попытки для каждого провайдера (3+3+3)
            # Проверяем что есть успешные провайдеры
            self.assertGreater(len(report.successful_providers), 0)

        asyncio.run(run_test())

    def test_fail_fast_strategy(self):
        """Тест стратегии FAIL_FAST."""
        providers = [
            MockProvider("Provider1", success=False),
            MockProvider("Provider2", success=True),
            MockProvider("Provider3", success=True)
        ]

        service = NotificationService(providers)

        async def run_test():
            report = await service.send_notification(
                self.user,
                self.message,
                DeliveryStrategy.FAIL_FAST
            )

            self.assertFalse(report.success)
            self.assertEqual(report.total_attempts, 1)  # Должен остановиться после ошибки
            self.assertEqual(providers[0].call_count, 1)
            self.assertEqual(providers[1].call_count, 0)
            self.assertEqual(providers[2].call_count, 0)

        asyncio.run(run_test())

    def test_unreachable_user(self):
        """Тест с недоступным пользователем."""
        # Провайдер, который считает пользователя недоступным
        provider = MockProvider(
            "Provider1",
            success=True,
            reachable_check=lambda user: False
        )

        service = NotificationService([provider])

        async def run_test():
            report = await service.send_notification(
                self.user,
                self.message,
                DeliveryStrategy.FIRST_SUCCESS
            )

            self.assertFalse(report.success)
            self.assertEqual(report.total_attempts, 0)
            self.assertEqual(provider.call_count, 0)

        asyncio.run(run_test())

    def test_bulk_notifications(self):
        """Тест массовой отправки уведомлений."""
        users = [
            User(id="user1", name="User 1", email="user1@example.com"),
            User(id="user2", name="User 2", email="user2@example.com"),
            User(id="user3", name="User 3", email="user3@example.com")
        ]

        provider = MockProvider("Provider1", success=True)
        service = NotificationService([provider])

        async def run_test():
            reports = await service.send_bulk_notifications(
                users,
                self.message,
                max_concurrent=2
            )

            self.assertEqual(len(reports), 3)
            self.assertTrue(all(report.success for report in reports))
            self.assertEqual(provider.call_count, 3)

        asyncio.run(run_test())


class TestMessageTemplating(unittest.TestCase):
    """Тесты для шаблонизации сообщений."""

    def test_message_rendering(self):
        """Тест рендеринга сообщений с шаблонными данными."""
        message = NotificationMessage(
            subject="Hello, {name}!",
            content="Your order #{order_id} is ready. Total: ${total}",
            template_data={
                "name": "John",
                "order_id": "12345",
                "total": "29.99"
            }
        )

        rendered = message.render()

        self.assertEqual(rendered["subject"], "Hello, John!")
        self.assertEqual(rendered["content"], "Your order #12345 is ready. Total: $29.99")

    def test_message_without_template(self):
        """Тест сообщения без шаблонных данных."""
        message = NotificationMessage(
            subject="Static subject",
            content="Static content"
        )

        rendered = message.render()

        self.assertEqual(rendered["subject"], "Static subject")
        self.assertEqual(rendered["content"], "Static content")


class TestUserReachability(unittest.TestCase):
    """Тесты для проверки доступности пользователей."""

    def test_user_with_email(self):
        """Тест пользователя с email."""
        user = User(
            id="user1",
            name="User with Email",
            email="user@example.com"
        )

        # Для тестирования создаем простую проверку
        # В реальном коде это делается в конкретных провайдерах
        self.assertTrue(bool(user.email))

    def test_user_with_phone(self):
        """Тест пользователя с телефоном."""
        user = User(
            id="user2",
            name="User with Phone",
            phone="+1234567890"
        )

        self.assertTrue(bool(user.phone))

    def test_user_with_telegram(self):
        """Тест пользователя с Telegram."""
        user = User(
            id="user3",
            name="User with Telegram",
            telegram_chat_id="123456789"
        )

        self.assertTrue(bool(user.telegram_chat_id))

    def test_user_without_contacts(self):
        """Тест пользователя без контактных данных."""
        user = User(
            id="user4",
            name="User without contacts"
        )

        self.assertFalse(bool(user.email))
        self.assertFalse(bool(user.phone))
        self.assertFalse(bool(user.telegram_chat_id))


if __name__ == "__main__":
    unittest.main()
