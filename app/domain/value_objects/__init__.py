"""
Base value object implementation.
"""

from typing import Any


class ValueObject:
    """Base class for all value objects."""

    def __eq__(self, other: Any) -> bool:
        """Default equality implementation for value objects."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Default hash implementation for value objects."""
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"
