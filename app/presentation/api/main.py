"""
FastAPI application main module.
"""
from fastapi import FastAPI

# Create FastAPI app
app = FastAPI(
    title="Notification Service API",
    description="Clean Architecture notification service",
    version="1.0.0"
)

# Import and include routers
try:
    from .routes.deliveries import router as deliveries_router
    from .routes.health import router as health_router
    from .routes.notifications import router as notifications_router
    from .routes.users import router as users_router

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
    app.include_router(deliveries_router, prefix="/deliveries", tags=["deliveries"])

except ImportError:
    # Fallback when routers are not available
    pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Notification Service API", "version": "1.0.0"}
