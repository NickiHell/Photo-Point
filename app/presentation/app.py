"""
FastAPI application factory and main app configuration.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from ..infrastructure.config import get_config
    from ..infrastructure.logging import setup_logging
    from .api.routes import deliveries, health, notifications, users
    from .dependencies import get_container


    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan manager."""
        config = get_config()

        # Setup logging
        setup_logging(config.logging)

        # Initialize dependencies
        container = get_container()
        await container.init_resources()

        yield

        # Cleanup
        await container.shutdown_resources()


    def create_app() -> FastAPI:
        """Create and configure FastAPI application."""
        config = get_config()

        app = FastAPI(
            title="Notification Service",
            description="Clean Architecture Notification Service with DDD",
            version="1.0.0",
            debug=config.debug,
            docs_url=config.api.docs_url,
            redoc_url=config.api.redoc_url,
            lifespan=lifespan
        )

        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.api.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Include routers
        app.include_router(health.router, prefix="/health", tags=["health"])
        app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
        app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
        app.include_router(deliveries.router, prefix="/api/v1/deliveries", tags=["deliveries"])

        return app

except ImportError:
    # Fallback when FastAPI is not available
    def create_app():
        raise ImportError("FastAPI is not installed. Please install it with: pip install fastapi uvicorn")
