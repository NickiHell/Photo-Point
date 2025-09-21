# Система уведомлений

Надежная система для отправки уведомлений пользователям через Email, SMS и Telegram с поддержкой fallback механизмов.

## Особенности

- ✅ **Множественные каналы**: Email, SMS (Twilio), Telegram
- 🔄 **Надежная доставка**: Автоматический переход к альтернативным каналам при сбоях
- ⚡ **Асинхронная работа**: Высокая производительность с использованием async/await
- 🎯 **Гибкие стратегии**: Различные стратегии доставки для разных сценариев
- 📊 **Детальная отчетность**: Подробные отчеты о статусе доставки
- 🔧 **Простая настройка**: Конфигурация через переменные окружения
- 📝 **Шаблонизация**: Поддержка динамических шаблонов сообщений

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните нужные поля:

```bash
cp .env.example .env
```

Пример конфигурации:

```env
# Email настройки
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# SMS настройки (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# Telegram настройки
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### 3. Простой пример использования

```python
import asyncio
from src.models import User, NotificationMessage
from src.config import create_notification_service

async def send_notification():
    # Создаем сервис
    service = create_notification_service()
    
    # Создаем пользователя
    user = User(
        id="user123",
        name="Иван Иванов",
        email="ivan@example.com",
        phone="+79123456789",
        telegram_chat_id="123456789"
    )
    
    # Создаем сообщение
    message = NotificationMessage(
        subject="Добро пожаловать!",
        content="Здравствуйте, {name}! Добро пожаловать в нашу систему.",
        template_data={"name": user.name}
    )
    
    # Отправляем уведомление
    report = await service.send_notification(user, message)
    
    print(f"Доставлено: {report.success}")
    print(f"Провайдер: {report.successful_providers}")

asyncio.run(send_notification())
```

## Архитектура

### Основные компоненты

1. **NotificationService** - Главный сервис для управления отправкой
2. **NotificationProvider** - Базовый класс для всех провайдеров
3. **EmailProvider** - Провайдер для отправки email через SMTP
4. **SMSProvider** - Провайдер для отправки SMS через Twilio
5. **TelegramProvider** - Провайдер для отправки сообщений через Telegram Bot API

### Модели данных

- **User** - Модель пользователя с контактными данными
- **NotificationMessage** - Модель сообщения с поддержкой шаблонов
- **NotificationResult** - Результат отправки уведомления
- **DeliveryReport** - Детальный отчет о доставке

## Стратегии доставки

### FIRST_SUCCESS (по умолчанию)
Останавливается после первой успешной доставки.

```python
report = await service.send_notification(
    user, message, 
    DeliveryStrategy.FIRST_SUCCESS
)
```

### TRY_ALL
Пытается доставить через все доступные каналы.

```python
report = await service.send_notification(
    user, message, 
    DeliveryStrategy.TRY_ALL
)
```

### FAIL_FAST
Останавливается при первой ошибке.

```python
report = await service.send_notification(
    user, message, 
    DeliveryStrategy.FAIL_FAST
)
```

## Примеры использования

### Массовая отправка

```python
users = [user1, user2, user3, ...]

reports = await service.send_bulk_notifications(
    users=users,
    message=message,
    max_concurrent=10  # Максимум параллельных отправок
)

# Анализируем результаты
successful = sum(1 for r in reports if r.success)
print(f"Успешно доставлено: {successful}/{len(reports)}")
```

### Настройка повторных попыток

```python
report = await service.send_notification(
    user=user,
    message=message,
    max_retries=5,        # Максимум попыток на провайдер
    retry_delay=2.0       # Задержка между попытками (сек)
)
```

### Проверка статуса сервиса

```python
status = await service.get_service_status()
print(f"Статус: {status['service_status']}")
print(f"Доступные провайдеры: {status['available_providers']}")
```

## Провайдеры

### Email Provider

Поддерживает отправку через любой SMTP сервер:

- Gmail, Outlook, Yahoo и другие
- Поддержка TLS шифрования
- Валидация email адресов
- Автоматическая аутентификация

### SMS Provider (Twilio)

Отправка SMS через Twilio API:

- Международные номера
- Автоматическая нормализация номеров
- Обработка ошибок и лимитов
- Поддержка длинных сообщений

### Telegram Provider

Отправка сообщений через Telegram Bot API:

- Поддержка Markdown форматирования
- Обработка длинных сообщений
- Валидация chat_id
- Обработка rate limits

## Обработка ошибок

Система предоставляет детальную информацию об ошибках:

```python
report = await service.send_notification(user, message)

if not report.success:
    for attempt in report.attempts:
        if not attempt.result.success:
            print(f"Провайдер {attempt.provider.provider_name} failed:")
            print(f"  Error: {attempt.result.error}")
            print(f"  Message: {attempt.result.message}")
```

### Типы исключений

- `ConfigurationError` - Ошибки конфигурации провайдера
- `AuthenticationError` - Ошибки аутентификации
- `SendError` - Общие ошибки отправки
- `RateLimitError` - Превышение лимитов API
- `UserNotReachableError` - Пользователь недоступен для провайдера

## Логирование

Настройка уровня логирования:

```python
from src.config import setup_logging

setup_logging("DEBUG")  # DEBUG, INFO, WARNING, ERROR
```

Или через переменную окружения:
```env
LOG_LEVEL=INFO
```

## Тестирование

### Запуск тестов

```bash
# Базовые тесты
python -m pytest tests/test_basic.py

# Или используя unittest
python -m unittest tests.test_basic
```

### Примеры тестирования

```bash
# Простой пример
python examples/simple_example.py

# Массовая отправка
python examples/bulk_example.py

# Тест надежности
python examples/reliability_test.py
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `MAX_RETRIES` | Максимум повторных попыток | `3` |
| `RETRY_DELAY` | Задержка между попытками (сек) | `1.0` |
| `MAX_CONCURRENT` | Максимум параллельных отправок | `10` |
| `PROVIDER_ORDER` | Порядок провайдеров | `email,telegram,sms` |

### Email настройки

| Переменная | Описание |
|------------|----------|
| `EMAIL_SMTP_HOST` | SMTP сервер |
| `EMAIL_SMTP_PORT` | Порт SMTP (587 для TLS) |
| `EMAIL_USER` | Имя пользователя |
| `EMAIL_PASSWORD` | Пароль (app password для Gmail) |
| `EMAIL_FROM` | Email отправителя |
| `EMAIL_USE_TLS` | Использовать TLS (`true`/`false`) |

### SMS настройки (Twilio)

| Переменная | Описание |
|------------|----------|
| `TWILIO_ACCOUNT_SID` | Account SID из Twilio Console |
| `TWILIO_AUTH_TOKEN` | Auth Token из Twilio Console |
| `TWILIO_PHONE_NUMBER` | Номер отправителя (+1234567890) |

### Telegram настройки

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather |
| `TELEGRAM_TIMEOUT` | Таймаут HTTP запросов (сек) |

## Структура проекта

```
notification_service/
├── src/
│   ├── __init__.py
│   ├── base.py              # Базовые интерфейсы
│   ├── models.py            # Модели данных
│   ├── exceptions.py        # Исключения
│   ├── service.py           # Основной сервис
│   ├── config.py            # Конфигурация
│   └── providers/
│       ├── __init__.py
│       ├── email.py         # Email провайдер
│       ├── sms.py           # SMS провайдер
│       └── telegram.py      # Telegram провайдер
├── examples/
│   ├── simple_example.py    # Простой пример
│   ├── bulk_example.py      # Массовая отправка
│   └── reliability_test.py  # Тест надежности
├── tests/
│   └── test_basic.py        # Базовые тесты
├── requirements.txt         # Зависимости
├── .env.example            # Пример конфигурации
├── .gitignore             # Git ignore
└── README.md              # Документация
```

## Расширение системы

### Создание нового провайдера

```python
from src.base import NotificationProvider
from src.models import NotificationResult, NotificationType

class CustomProvider(NotificationProvider):
    async def send(self, user, message):
        # Логика отправки
        return NotificationResult(
            success=True,
            provider=NotificationType.EMAIL,  # Или создать новый тип
            message="Sent successfully"
        )
    
    def is_user_reachable(self, user):
        # Проверка доступности пользователя
        return True
    
    @property
    def provider_name(self):
        return "Custom Provider"
    
    async def validate_config(self):
        # Валидация конфигурации
        return True
```

### Интеграция нового провайдера

```python
from src.service import NotificationService

service = NotificationService([
    EmailProvider.from_env(),
    CustomProvider(),
    TelegramProvider.from_env()
])
```

## Производительность

### Оптимизация

- Используйте `send_bulk_notifications` для массовых отправок
- Настройте `max_concurrent` в зависимости от лимитов API
- Используйте стратегию `FIRST_SUCCESS` для экономии ресурсов
- Настройте подходящие значения `max_retries` и `retry_delay`

### Метрики

Система предоставляет детальные метрики:

```python
report = await service.send_notification(user, message)

print(f"Время доставки: {report.delivery_time:.2f} сек")
print(f"Количество попыток: {report.total_attempts}")
print(f"Успешные провайдеры: {report.successful_providers}")
```

## FAQ

### Как получить Telegram chat_id?

1. Создайте бота через @BotFather
2. Пользователь должен отправить `/start` боту
3. Используйте Telegram Bot API для получения updates
4. chat_id будет в поле `message.chat.id`

### Как настроить Gmail для отправки email?

1. Включите двухфакторную аутентификацию
2. Создайте App Password в настройках Google аккаунта
3. Используйте App Password вместо обычного пароля

### Как получить Twilio credentials?

1. Зарегистрируйтесь на [twilio.com](https://www.twilio.com)
2. Account SID и Auth Token находятся в Console Dashboard
3. Купите номер телефона в разделе Phone Numbers

## Лицензия

MIT License - см. файл LICENSE для деталей.

## Поддержка

При возникновении проблем:

1. Проверьте логи с уровнем DEBUG
2. Убедитесь в правильности конфигурации
3. Проверьте статус сервиса через `get_service_status()`
4. Создайте issue в репозитории проекта