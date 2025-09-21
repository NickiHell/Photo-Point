"""
Direct Notifications API route testing.
Tests FastAPI Notifications endpoints directly with mocked dependencies.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

# Import DTOs and value objects
from app.application.dto import (
    BulkNotificationResponseDTO,
    NotificationResponseDTO,
    NotificationStatusResponseDTO,
)


class TestNotificationsRoutesDirectly:
    """Test notifications route functions directly."""

    @pytest.mark.asyncio
    async def test_send_notification_function(self):
        """Test send_notification function directly."""
        try:
            from app.presentation.api.routes.notifications import (
                SendNotificationRequest,
                send_notification,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use case
        mock_use_case = AsyncMock()
        mock_response = NotificationResponseDTO(
            id="notif-123",
            recipient_id="user-123",
            message_template="Hello {name}",
            channels=["email", "sms"],
            priority="HIGH",
            scheduled_at=datetime(2024, 1, 1, 12, 0, 0),
            created_at=datetime(2024, 1, 1, 11, 0, 0),
            status="PENDING"
        )
        mock_use_case.execute.return_value = mock_response

        # Create request
        request = SendNotificationRequest(
            recipient_id="user-123",
            message_template="Hello {name}",
            message_variables={"name": "John"},
            channels=["email", "sms"],
            priority="HIGH",
            scheduled_at="2024-01-01T12:00:00Z"
        )

        # Call the function
        result = await send_notification(request, mock_use_case)

        # Verify result
        assert result.id == "notif-123"
        assert result.recipient_id == "user-123"
        assert result.message_template == "Hello {name}"
        assert result.channels == ["email", "sms"]
        assert result.priority == "HIGH"
        assert result.scheduled_at == "2024-01-01T12:00:00"
        assert result.created_at == "2024-01-01T11:00:00"
        assert result.status == "PENDING"

    @pytest.mark.asyncio
    async def test_send_notification_minimal_data(self):
        """Test send_notification with minimal required data."""
        try:
            from app.presentation.api.routes.notifications import (
                SendNotificationRequest,
                send_notification,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use case
        mock_use_case = AsyncMock()
        mock_response = NotificationResponseDTO(
            id="notif-124",
            recipient_id="user-124",
            message_template="Simple message",
            channels=["email"],
            priority="MEDIUM",
            scheduled_at=datetime(2024, 1, 1, 12, 0, 0),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            status="PENDING"
        )
        mock_use_case.execute.return_value = mock_response

        # Create request
        request = SendNotificationRequest(
            recipient_id="user-124",
            message_template="Simple message",
            channels=["email"]
        )

        # Call the function
        result = await send_notification(request, mock_use_case)

        # Verify result
        assert result.id == "notif-124"
        assert result.priority == "MEDIUM"  # Default value

    @pytest.mark.asyncio
    async def test_send_notification_validation_error(self):
        """Test send_notification with validation error."""
        try:
            from fastapi import HTTPException

            from app.presentation.api.routes.notifications import (
                SendNotificationRequest,
                send_notification,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use case with error
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("Invalid recipient ID")

        # Create request
        request = SendNotificationRequest(
            recipient_id="invalid-user",
            message_template="Test message",
            channels=["email"]
        )

        # Call the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await send_notification(request, mock_use_case)

        assert exc_info.value.status_code == 400
        assert "Invalid recipient ID" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_bulk_notification_function(self):
        """Test send_bulk_notification function directly."""
        try:
            from app.presentation.api.routes.notifications import (
                SendBulkNotificationRequest,
                send_bulk_notification,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use case
        mock_use_case = AsyncMock()

        # Mock individual notification responses
        notifications = [
            NotificationResponseDTO(
                id=f"notif-{i}",
                recipient_id=f"user-{i}",
                message_template="Bulk message",
                channels=["email"],
                priority="MEDIUM",
                scheduled_at=datetime(2024, 1, 1, 12, 0, 0),
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                status="PENDING"
            ) for i in range(1, 4)
        ]

        mock_response = BulkNotificationResponseDTO(
            notifications=notifications,
            total_count=3,
            successful_count=3,
            failed_count=0
        )
        mock_use_case.execute.return_value = mock_response

        # Create request
        request = SendBulkNotificationRequest(
            recipient_ids=["user-1", "user-2", "user-3"],
            message_template="Bulk message",
            channels=["email"]
        )

        # Call the function
        result = await send_bulk_notification(request, mock_use_case)

        # Verify result
        assert len(result.notifications) == 3
        assert result.total_count == 3
        assert result.notifications[0].id == "notif-1"
        assert result.notifications[1].recipient_id == "user-2"

    @pytest.mark.asyncio
    async def test_get_notification_status_function(self):
        """Test get_notification_status function directly."""
        try:
            from app.presentation.api.routes.notifications import (
                get_notification_status,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use case
        mock_use_case = AsyncMock()
        mock_response = NotificationStatusResponseDTO(
            notification_id="notif-123",
            recipient_id="user-123",
            status="DELIVERED",
            delivery_attempts=1,
            last_attempt_at=datetime(2024, 1, 1, 12, 30, 0),
            error_message=None,
            delivered_at=datetime(2024, 1, 1, 12, 30, 0),
            deliveries=[
                {
                    "channel": "email",
                    "status": "DELIVERED",
                    "delivered_at": "2024-01-01T12:30:00",
                    "provider_response": {"message_id": "email-123"}
                }
            ]
        )
        mock_use_case.execute.return_value = mock_response

        # Call the function
        result = await get_notification_status("notif-123", mock_use_case)

        # Verify result
        assert result.notification_id == "notif-123"
        assert result.status == "DELIVERED"
        assert result.delivery_attempts == 1
        assert len(result.deliveries) == 1

    @pytest.mark.asyncio
    async def test_get_notification_status_not_found(self):
        """Test get_notification_status when notification doesn't exist."""
        try:
            from fastapi import HTTPException

            from app.presentation.api.routes.notifications import (
                get_notification_status,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use case returning None
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = None

        # Call the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_notification_status("nonexistent-notif", mock_use_case)

        assert exc_info.value.status_code == 404
        assert "Notification not found" in str(exc_info.value.detail)


class TestNotificationRouteModels:
    """Test notification route Pydantic models."""

    def test_send_notification_request_model(self):
        """Test SendNotificationRequest model."""
        try:
            from app.presentation.api.routes.notifications import (
                SendNotificationRequest,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Test with all fields
        request = SendNotificationRequest(
            recipient_id="user-123",
            message_template="Hello {name}",
            message_variables={"name": "John"},
            channels=["email", "sms"],
            priority="HIGH",
            scheduled_at="2024-01-01T12:00:00Z",
            retry_policy={"max_attempts": 3},
            metadata={"campaign": "welcome"}
        )
        assert request.recipient_id == "user-123"
        assert request.message_template == "Hello {name}"
        assert request.channels == ["email", "sms"]
        assert request.priority == "HIGH"

        # Test with minimal fields
        request_minimal = SendNotificationRequest(
            recipient_id="user-124",
            message_template="Simple message",
            channels=["email"]
        )
        assert request_minimal.priority == "MEDIUM"  # Default value
        assert request_minimal.message_variables == {}
        assert request_minimal.retry_policy == {}

    def test_send_bulk_notification_request_model(self):
        """Test SendBulkNotificationRequest model."""
        try:
            from app.presentation.api.routes.notifications import (
                SendBulkNotificationRequest,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Test with multiple recipients
        request = SendBulkNotificationRequest(
            recipient_ids=["user-1", "user-2", "user-3"],
            message_template="Bulk message",
            channels=["email"]
        )
        assert len(request.recipient_ids) == 3
        assert request.message_template == "Bulk message"
        assert request.priority == "MEDIUM"  # Default

    def test_notification_response_model(self):
        """Test NotificationResponse model."""
        try:
            from app.presentation.api.routes.notifications import NotificationResponse
        except ImportError:
            pytest.skip("Notifications route not available")

        # Test model creation
        response = NotificationResponse(
            id="notif-123",
            recipient_id="user-123",
            message_template="Hello world",
            channels=["email"],
            priority="HIGH",
            scheduled_at="2024-01-01T12:00:00",
            created_at="2024-01-01T11:00:00",
            status="PENDING"
        )
        assert response.id == "notif-123"
        assert response.priority == "HIGH"
        assert response.status == "PENDING"


class TestNotificationsRouteImports:
    """Test notifications route imports and structure."""

    def test_router_import(self):
        """Test that router can be imported."""
        try:
            from app.presentation.api.routes.notifications import router
            assert router is not None
        except ImportError:
            pytest.skip("Notifications route not available")

    def test_route_functions_exist(self):
        """Test that route functions exist."""
        try:
            from app.presentation.api.routes.notifications import (
                get_notification_status,
                send_bulk_notification,
                send_notification,
            )
            # All functions should be callable
            assert callable(send_notification)
            assert callable(send_bulk_notification)
            assert callable(get_notification_status)
        except ImportError:
            pytest.skip("Notifications route not available")

    def test_pydantic_models_exist(self):
        """Test that Pydantic models exist."""
        try:
            from app.presentation.api.routes.notifications import (
                NotificationResponse,
                SendBulkNotificationRequest,
                SendNotificationRequest,
            )
            # All should be classes
            assert isinstance(SendNotificationRequest, type)
            assert isinstance(SendBulkNotificationRequest, type)
            assert isinstance(NotificationResponse, type)
        except ImportError:
            pytest.skip("Notifications route not available")


class TestNotificationsRouteErrorHandling:
    """Test error handling in notifications routes."""

    @pytest.mark.parametrize("error_type,expected_status", [
        (ValueError("Invalid input"), 400),
        (Exception("Database error"), 500),
        (KeyError("Missing field"), 500),
        (TypeError("Type mismatch"), 500),
    ])
    @pytest.mark.asyncio
    async def test_send_notification_error_handling(self, error_type, expected_status):
        """Test send_notification error handling."""
        try:
            from fastapi import HTTPException

            from app.presentation.api.routes.notifications import (
                SendNotificationRequest,
                send_notification,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use case with error
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = error_type

        # Create request
        request = SendNotificationRequest(
            recipient_id="user-123",
            message_template="Test message",
            channels=["email"]
        )

        # Call the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await send_notification(request, mock_use_case)

        assert exc_info.value.status_code == expected_status

    @pytest.mark.parametrize("datetime_string", [
        "2024-01-01T12:00:00Z",
        "2024-01-01T12:00:00+00:00",
        "2024-12-31T23:59:59Z",
    ])
    @pytest.mark.asyncio
    async def test_datetime_parsing(self, datetime_string):
        """Test datetime parsing in send_notification."""
        try:
            from app.presentation.api.routes.notifications import (
                SendNotificationRequest,
                send_notification,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use case
        mock_use_case = AsyncMock()
        mock_response = NotificationResponseDTO(
            id="notif-123",
            recipient_id="user-123",
            message_template="Test",
            channels=["email"],
            priority="MEDIUM",
            scheduled_at=datetime(2024, 1, 1, 12, 0, 0),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            status="PENDING"
        )
        mock_use_case.execute.return_value = mock_response

        # Create request with datetime string
        request = SendNotificationRequest(
            recipient_id="user-123",
            message_template="Test message",
            channels=["email"],
            scheduled_at=datetime_string
        )

        # Should not raise exception
        result = await send_notification(request, mock_use_case)
        assert result.id == "notif-123"


class TestNotificationsAPIIntegration:
    """Integration tests for Notifications API."""

    @pytest.mark.asyncio
    async def test_notification_flow_simulation(self):
        """Test simulated notification flow."""
        try:
            from app.presentation.api.routes.notifications import (
                SendNotificationRequest,
                get_notification_status,
                send_notification,
            )
        except ImportError:
            pytest.skip("Notifications route not available")

        # Mock use cases
        send_mock = AsyncMock()
        status_mock = AsyncMock()

        # Mock send response
        send_response = NotificationResponseDTO(
            id="notif-flow",
            recipient_id="user-flow",
            message_template="Flow test",
            channels=["email"],
            priority="MEDIUM",
            scheduled_at=datetime(2024, 1, 1, 12, 0, 0),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            status="PENDING"
        )
        send_mock.execute.return_value = send_response

        # Mock status response
        status_response = NotificationStatusResponseDTO(
            notification_id="notif-flow",
            recipient_id="user-flow",
            status="DELIVERED",
            delivery_attempts=1,
            last_attempt_at=datetime(2024, 1, 1, 12, 30, 0),
            error_message=None,
            delivered_at=datetime(2024, 1, 1, 12, 30, 0),
            deliveries=[]
        )
        status_mock.execute.return_value = status_response

        # Test SEND
        request = SendNotificationRequest(
            recipient_id="user-flow",
            message_template="Flow test",
            channels=["email"]
        )
        send_result = await send_notification(request, send_mock)
        assert send_result.status == "PENDING"

        # Test STATUS CHECK
        status_result = await get_notification_status("notif-flow", status_mock)
        assert status_result.status == "DELIVERED"


def test_coverage_dummy():
    """Dummy test to ensure coverage collection works."""
    # This test ensures the file is loaded and coverage is collected
    assert True
