"""
Tortoise ORM initialization for the FastAPI application.
"""

import logging
from typing import Callable

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.infrastructure.config.tortoise_config import get_tortoise_config

logger = logging.getLogger(__name__)


def init_tortoise(
    app: FastAPI,
    generate_schemas: bool = False,
    on_startup: bool = True,
    on_shutdown: bool = True,
) -> None:
    """
    Initialize Tortoise ORM with FastAPI application.

    Args:
        app: The FastAPI application instance
        generate_schemas: Whether to generate schemas on startup
        on_startup: Whether to initialize on application startup
        on_shutdown: Whether to close connections on application shutdown
    """
    logger.info("Initializing Tortoise ORM")

    config = get_tortoise_config()

    register_tortoise(
        app,
        config=config,
        generate_schemas=generate_schemas,
        add_exception_handlers=True,
    )

    logger.info("Tortoise ORM initialized successfully")


def get_init_tortoise_handler(
    generate_schemas: bool = False,
) -> Callable[[FastAPI], None]:
    """
    Get a handler for initializing Tortoise ORM.

    Args:
        generate_schemas: Whether to generate schemas on startup

    Returns:
        Callable: A handler function to initialize Tortoise ORM
    """

    def handler(app: FastAPI) -> None:
        init_tortoise(app, generate_schemas=generate_schemas)

    return handler
