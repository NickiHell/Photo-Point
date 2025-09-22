# Миграции с Tortoise ORM и Aerich

В этом проекте для работы с базой данных используется Tortoise ORM с Aerich для управления миграциями.

## Структура БД

База данных построена на PostgreSQL и включает следующие основные таблицы:

- `users` - пользователи системы
- `notifications` - уведомления
- `deliveries` - способы доставки уведомлений
- `delivery_attempts` - попытки доставки уведомлений

## Начало работы

1. Установка зависимостей:
   ```bash
   make dev-install
   ```

2. Запуск сервисов:
   ```bash
   docker compose up -d
   ```

3. Инициализация Aerich:
   ```bash
   make aerich-init
   ```

## Управление миграциями

### Создание новой миграции

После внесения изменений в модели Tortoise ORM, создайте новую миграцию:

```bash
make aerich-migrate
```

Вам будет предложено ввести имя миграции. Используйте описательные имена, например:

- `add_user_preferences`
- `update_delivery_status_field`
- `create_notification_templates`

### Применение миграций

Для применения всех доступных миграций:

```bash
make aerich-upgrade
```

### Структура файлов миграций

Миграции хранятся в директории `migrations/`. Каждая миграция содержит два основных метода:

- `upgrade()` - применяет изменения в схеме БД
- `downgrade()` - откатывает изменения (если поддерживается)

## Взаимодействие с моделями

Все модели определены в `app/infrastructure/repositories/tortoise_models.py`. 

Для работы с данными используйте репозитории:

- `TortoiseUserRepository`
- `TortoiseNotificationRepository`
- `TortoiseDeliveryRepository`

## Тестирование

Для тестов используется отдельная тестовая база данных. При запуске тестов можно использовать:

```bash
python -m pytest tests/ --create-db
```

Флаг `--create-db` автоматически создает тестовую схему.