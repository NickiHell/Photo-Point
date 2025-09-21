"""
Base entity implementation.
"""
from abc import ABC
from typing import Any
from datetime import datetime, timezone


class Entity(ABC):
    """Base class for all entities."""
    
    def __init__(self, entity_id: Any) -> None:
        self._id = entity_id
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = self._created_at
    
    @property
    def id(self) -> Any:
        return self._id
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def _mark_updated(self) -> None:
        """Mark entity as updated."""
        self._updated_at = datetime.now(timezone.utc)
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id!r})"