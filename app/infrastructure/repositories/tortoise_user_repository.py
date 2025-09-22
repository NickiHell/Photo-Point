"""
User repository implementation based on Tortoise ORM.
"""

from typing import List, Optional, Union

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.user import Email, PhoneNumber, TelegramChatId, UserId
from app.infrastructure.repositories.tortoise_models import UserModel


class TortoiseUserRepository(UserRepository):
    """Tortoise ORM implementation of the UserRepository."""

    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get a user by ID."""
        user_model = await UserModel.get_or_none(id=user_id.value)
        if not user_model:
            return None

        return self._model_to_entity(user_model)

    async def get_by_email(self, email: Email) -> Optional[User]:
        """Get a user by email."""
        user_model = await UserModel.get_or_none(email=str(email))
        if not user_model:
            return None

        return self._model_to_entity(user_model)

    async def get_by_phone(self, phone: PhoneNumber) -> Optional[User]:
        """Get a user by phone number."""
        user_model = await UserModel.get_or_none(phone_number=str(phone))
        if not user_model:
            return None

        return self._model_to_entity(user_model)

    async def get_by_telegram_id(self, telegram_id: TelegramChatId) -> Optional[User]:
        """Get a user by Telegram chat ID."""
        user_model = await UserModel.get_or_none(telegram_id=str(telegram_id))
        if not user_model:
            return None

        return self._model_to_entity(user_model)

    async def save(self, user: User) -> User:
        """Save a user."""
        user_data = {
            "id": user.id.value,
            "email": str(user.email) if user.email else None,
            "phone_number": str(user.phone_number) if user.phone_number else None,
            "telegram_id": str(user.telegram_id) if user.telegram_id else None,
            "is_active": user.is_active,
            "preferences": user.preferences,
        }

        user_model, created = await UserModel.update_or_create(
            id=user.id.value, defaults=user_data
        )

        return self._model_to_entity(user_model)

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users."""
        user_models = await UserModel.all().limit(limit).offset(offset)
        return [self._model_to_entity(user_model) for user_model in user_models]

    def _model_to_entity(self, user_model: UserModel) -> User:
        """Convert a UserModel to a User entity."""
        return User(
            id=UserId(user_model.id),
            email=Email(user_model.email) if user_model.email else None,
            phone_number=PhoneNumber(user_model.phone_number)
            if user_model.phone_number
            else None,
            telegram_id=TelegramChatId(user_model.telegram_id)
            if user_model.telegram_id
            else None,
            is_active=user_model.is_active,
            preferences=user_model.preferences,
        )
