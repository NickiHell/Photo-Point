# Система уведомлений

Надежная система для отправки уведомлений пользователям через Email, SMS и Telegram.

## Быстрый старт

### Запуск с Docker

```bash
# Клонирование репозитория
git clone https://github.com/NickiHell/Photo-Point.git
cd Photo-Point/notification_service

# Создание и настройка .env файла
cp .env.example .env
# Отредактируйте .env с вашими настройками

# Сборка и запуск через Docker Compose
docker-compose up --build

# Для запуска в фоне
docker-compose up -d --build

# Проверка работы
curl http://localhost:8000/health
```

### Docker команды для разработки

```bash
# Сборка образа
docker build -t notification-service .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env notification-service

# Запуск с монтированием кода (для разработки)
docker run -p 8000:8000 -v $(pwd):/app --env-file .env notification-service

# Проверка логов
docker-compose logs -f notification-service

# Остановка всех сервисов
docker-compose down

# Полная пересборка
docker-compose down --volumes --remove-orphans
docker-compose build --no-cache
docker-compose up
```

### Makefile команды (быстрый доступ)

```bash

# Настройка проекта с нуля
make setup          # Создает .venv
source .venv/bin/activate
make dev-install    # Устанавливает зависимости и pre-commit

# Разработка
make format         # Форматирование кода (black + isort + ruff format)
make lint           # Проверка кода (ruff + mypy + bandit)
make lint-fix       # Автоматическое исправление проблем
make test           # Запуск всех тестов
make test-cov       # Тесты с покрытием кода

# Docker
make docker-build   # Сборка образа
make docker-compose # Запуск через docker-compose
make docker-dev     # Запуск для разработки
make docker-clean   # Очистка Docker ресурсов

# Утилиты  
make clean          # Очистка кэша и временных файлов
make run-dev        # Запуск dev сервера
make all            # Полная проверка (clean + lint + format + test)
```


## API Endpoints

- `GET /admin/` - Admin panel interface
- `POST /admin/send-sms` - Send test SMS
- `GET /admin/api/status` - Service health check



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



## Быстрые команды для разработки

```bash
# Мгновенный запуск всей системы
git clone https://github.com/NickiHell/Photo-Point.git
cd Photo-Point/notification_service
docker-compose up --build

# Разработка (локально)
make setup                    # Создать .venv  
source .venv/bin/activate     # Активировать окружение
make dev-install              # Установить все зависимости
make run-dev                  # Запустить сервер разработки

# Проверка качества кода
make format                   # Форматирование (ruff + black)
make lint                     # Проверка кода (ruff + mypy)  
make test                     # Запуск всех тестов
make all                      # Полная проверка

# Docker команды
make docker-compose           # Запуск в контейнерах
make docker-dev              # Разработка с Docker
make docker-clean            # Очистка Docker ресурсов
```