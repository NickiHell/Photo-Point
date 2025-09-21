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


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Notification Service API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notification-service"}


@app.get("/api/v1/users")
async def list_users():
    """List users endpoint (placeholder)."""
    return {"users": []}


@app.post("/api/v1/users")
async def create_user():
    """Create user endpoint (placeholder)."""
    return {"message": "User creation endpoint"}


@app.post("/api/v1/notifications/send")
async def send_notification():
    """Send notification endpoint (placeholder)."""
    return {"message": "Notification sent"}
