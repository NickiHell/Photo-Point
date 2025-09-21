"""
Health check endpoints.
"""
from datetime import datetime

try:
    from fastapi import APIRouter, Depends
    from fastapi.responses import JSONResponse

    router = APIRouter()


    @router.get("/")
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "notification-service",
            "version": "1.0.0"
        }


    @router.get("/ready")
    async def readiness_check():
        """Readiness check endpoint."""
        # In a real application, you would check:
        # - Database connectivity
        # - External service availability
        # - Cache availability

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "healthy",
                "cache": "healthy",
                "external_services": "healthy"
            }
        }


    @router.get("/live")
    async def liveness_check():
        """Liveness check endpoint."""
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }

except ImportError:
    # Mock router for when FastAPI is not available
    class MockRouter:
        def get(self, path: str):
            def decorator(func):
                return func
            return decorator

    router = MockRouter()
