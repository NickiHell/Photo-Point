"""Admin panel routes."""

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/presentation/admin/templates")


@router.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Admin panel main page."""
    return templates.TemplateResponse("admin.html", {"request": request})


@router.post("/send-sms")
async def send_test_sms(
    phone: str = Form(...),
    message: str = Form(...),
    subject: str = Form(default="Test SMS"),
):
    """Send test SMS through admin panel."""
    try:
        # Import SMS provider directly for testing
        from src.models import NotificationMessage, NotificationType, User
        from src.providers.sms import SMSProvider

        # Create SMS provider
        sms_provider = SMSProvider.from_env()

        # Create test user
        user = User(
            id="1",
            name="test_user",
            email=None,
            phone=phone.strip(),
        )

        # Create message
        notification_message = NotificationMessage(
            subject=subject,
            content=message,
        )

        # Send SMS
        result = await sms_provider.send(user, notification_message)

        return {
            "success": result.success,
            "message": result.message,
            "provider": result.provider.value if result.provider else "SMS",
        }

    except ImportError as e:
        return {
            "success": False,
            "message": f"SMS provider not available: {str(e)}",
            "provider": None,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending SMS: {str(e)}",
            "provider": None,
        }


@router.get("/api/status")
async def api_status():
    """API health check for admin panel."""
    return {"status": "ok", "service": "notification-admin"}
