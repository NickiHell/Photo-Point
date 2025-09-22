"""
Tortoise ORM configuration for database connectivity.
"""

import os
from typing import Dict, List

# Get database configuration from environment variables or use defaults
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "notification_service")

# Base Tortoise ORM config
TORTOISE_ORM = {
    "connections": {
        "default": f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    },
    "apps": {
        "models": {
            "models": [
                "app.infrastructure.repositories.tortoise_models",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
    "use_tz": True,
}


def get_tortoise_config() -> Dict:
    """
    Get the Tortoise ORM configuration.

    Returns:
        Dict: The Tortoise ORM configuration dictionary.
    """
    return TORTOISE_ORM


def get_app_models() -> List[str]:
    """
    Get the list of application models.

    Returns:
        List[str]: List of application model module paths.
    """
    return TORTOISE_ORM["apps"]["models"]["models"]
