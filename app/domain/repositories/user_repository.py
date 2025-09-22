"""
Repository interface for user entities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.user import User
from app.domain.value_objects.user import Email, UserId


class UserRepository(ABC):
    """Abstract repository for managing user entities."""

    @abstractmethod
    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get a user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        """Get a user by email."""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save a user."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users."""
        pass
