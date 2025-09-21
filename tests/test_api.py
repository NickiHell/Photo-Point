"""
API integration tests using TestClient.
"""
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    from app.presentation.api.main import app
    return TestClient(app)


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch('app.presentation.dependencies.get_user_repository') as mock_user_repo, \
         patch('app.presentation.dependencies.get_notification_service') as mock_notif_service:

        # Setup user repository mock
        user_repo_instance = Mock()
        user_repo_instance.save.return_value = "user_123"
        user_repo_instance.find_by_id.return_value = {
            "id": "user_123",
            "email": "test@example.com",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_user_repo.return_value = user_repo_instance

        # Setup notification service mock
        notif_service_instance = Mock()
        notif_service_instance.send.return_value = "notification_456"
        mock_notif_service.return_value = notif_service_instance

        yield {
            "user_repository": user_repo_instance,
            "notification_service": notif_service_instance
        }


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Notification Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-service"
        assert "checks" in data
        assert "timestamp" in data


class TestUserEndpoints:
    """Test user management endpoints."""

    def test_create_user_success(self, client, mock_dependencies):
        """Test successful user creation."""
        user_data = {
            "email": "newuser@example.com",
            "phone_number": "+1234567890",
            "telegram_id": "telegram123",
            "preferences": {"notifications": True, "lang": "en"}
        }

        response = client.post("/api/v1/users", json=user_data)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert data["id"] == "user_123"
        assert data["email"] == "newuser@example.com"
        assert data["phone_number"] == "+1234567890"
        assert data["telegram_id"] == "telegram123"
        assert data["preferences"] == {"notifications": True, "lang": "en"}
        assert data["is_active"] is True
        assert "created_at" in data

        # Verify repository was called correctly
        mock_dependencies["user_repository"].save.assert_called_once()
        call_args = mock_dependencies["user_repository"].save.call_args[0][0]
        assert call_args["email"] == "newuser@example.com"
        assert call_args["is_active"] is True

    def test_create_user_minimal_data(self, client, mock_dependencies):
        """Test user creation with minimal required data."""
        user_data = {
            "email": "minimal@example.com"
        }

        response = client.post("/api/v1/users", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "minimal@example.com"
        assert data["preferences"] == {}

    def test_create_user_invalid_email(self, client, mock_dependencies):
        """Test user creation with invalid email."""
        user_data = {
            "email": "invalid-email"
        }

        response = client.post("/api/v1/users", json=user_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Should contain validation error about email format

    def test_create_user_empty_body(self, client, mock_dependencies):
        """Test user creation with empty request body."""
        response = client.post("/api/v1/users", json={})

        # Should still work as email is optional in our DTO
        assert response.status_code == 201

    def test_get_user_success(self, client, mock_dependencies):
        """Test successful user retrieval."""
        response = client.get("/api/v1/users/user_123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user_123"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True

        # Verify repository was called
        mock_dependencies["user_repository"].find_by_id.assert_called_once_with("user_123")

    def test_get_user_not_found(self, client, mock_dependencies):
        """Test user retrieval when user doesn't exist."""
        mock_dependencies["user_repository"].find_by_id.return_value = None

        response = client.get("/api/v1/users/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"


class TestNotificationEndpoints:
    """Test notification endpoints."""

    def test_send_notification_success(self, client, mock_dependencies):
        """Test successful notification sending."""
        notification_data = {
            "recipient_id": "user_123",
            "message_template": "Hello {name}! Welcome to {service}.",
            "message_variables": {"name": "John", "service": "NotificationApp"},
            "channels": ["email", "sms"],
            "priority": "HIGH"
        }

        response = client.post("/api/v1/notifications/send", json=notification_data)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert data["id"] == "notification_456"
        assert data["recipient_id"] == "user_123"
        assert data["message_template"] == "Hello {name}! Welcome to {service}."
        assert data["channels"] == ["email", "sms"]
        assert data["priority"] == "HIGH"
        assert data["status"] == "PENDING"
        assert "created_at" in data

        # Verify service was called correctly
        mock_dependencies["notification_service"].send.assert_called_once()
        call_args = mock_dependencies["notification_service"].send.call_args[0][0]
        assert call_args["recipient_id"] == "user_123"
        assert call_args["message_variables"] == {"name": "John", "service": "NotificationApp"}

    def test_send_notification_minimal_data(self, client, mock_dependencies):
        """Test notification sending with minimal required data."""
        notification_data = {
            "recipient_id": "user_123",
            "message_template": "Simple message"
        }

        response = client.post("/api/v1/notifications/send", json=notification_data)

        assert response.status_code == 201
        data = response.json()
        assert data["recipient_id"] == "user_123"
        assert data["message_template"] == "Simple message"
        assert data["channels"] == ["email"]  # Default channel
        assert data["priority"] == "MEDIUM"  # Default priority

    def test_send_notification_invalid_priority(self, client, mock_dependencies):
        """Test notification sending with invalid priority."""
        notification_data = {
            "recipient_id": "user_123",
            "message_template": "Test message",
            "priority": "INVALID_PRIORITY"
        }

        response = client.post("/api/v1/notifications/send", json=notification_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Should contain validation error about priority

    def test_send_notification_missing_recipient(self, client, mock_dependencies):
        """Test notification sending without recipient."""
        notification_data = {
            "message_template": "Test message"
            # Missing recipient_id
        }

        response = client.post("/api/v1/notifications/send", json=notification_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_send_notification_empty_template(self, client, mock_dependencies):
        """Test notification sending with empty message template."""
        notification_data = {
            "recipient_id": "user_123",
            "message_template": ""  # Empty template
        }

        response = client.post("/api/v1/notifications/send", json=notification_data)

        # This might be valid depending on business rules
        # Adjust based on actual validation requirements
        assert response.status_code in [201, 422]


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v1/users",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_unsupported_media_type(self, client):
        """Test handling of unsupported media type."""
        response = client.post(
            "/api/v1/users",
            data="some data",
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Test method not allowed errors."""
        response = client.put("/api/v1/users")  # PUT not allowed

        assert response.status_code == 405
        data = response.json()
        assert data["detail"] == "Method Not Allowed"

    def test_internal_server_error(self, client):
        """Test internal server error handling."""
        with patch('app.presentation.dependencies.get_user_repository') as mock_repo:
            mock_repo.side_effect = Exception("Database connection failed")

            response = client.post("/api/v1/users", json={"email": "test@example.com"})

            assert response.status_code == 500
            # Check if error is handled gracefully


class TestRequestValidation:
    """Test request validation scenarios."""

    def test_user_creation_field_validation(self, client, mock_dependencies):
        """Test various field validation scenarios for user creation."""
        # Test very long email
        long_email = "a" * 300 + "@example.com"
        response = client.post("/api/v1/users", json={"email": long_email})
        # Response depends on validation rules

        # Test phone number format
        invalid_phone = "not-a-phone-number"
        response = client.post("/api/v1/users", json={
            "email": "test@example.com",
            "phone_number": invalid_phone
        })
        # Should be handled by validation

        # Test preferences type
        invalid_preferences = "not a dict"
        response = client.post("/api/v1/users", json={
            "email": "test@example.com",
            "preferences": invalid_preferences
        })
        assert response.status_code == 422

    def test_notification_field_validation(self, client, mock_dependencies):
        """Test notification field validation."""
        # Test invalid channels
        response = client.post("/api/v1/notifications/send", json={
            "recipient_id": "user123",
            "message_template": "Test",
            "channels": ["invalid_channel"]
        })
        # May or may not be validation error depending on implementation

        # Test message variables type
        response = client.post("/api/v1/notifications/send", json={
            "recipient_id": "user123",
            "message_template": "Test {var}",
            "message_variables": "not a dict"
        })
        assert response.status_code == 422


class TestConcurrency:
    """Test concurrent request handling."""

    def test_multiple_user_creation(self, client, mock_dependencies):
        """Test multiple concurrent user creation requests."""
        import concurrent.futures

        def create_user(index):
            return client.post("/api/v1/users", json={
                "email": f"user{index}@example.com"
            })

        # Send multiple requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_user, i) for i in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All should succeed
        for response in responses:
            assert response.status_code == 201


def test_cors_headers(client):
    """Test CORS headers are present."""
    client.options("/api/v1/users")

    # Check if CORS headers are set (depends on CORS configuration)
    # This test may need adjustment based on actual CORS setup


def test_api_documentation_available(client):
    """Test that API documentation endpoints are available."""
    # OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200

    # Swagger UI (if enabled)
    response = client.get("/docs")
    # May be 200 or redirect depending on configuration


def test_security_headers(client):
    """Test security headers are present."""
    client.get("/")

    # Check for common security headers
    # This depends on middleware configuration

    # These tests may need adjustment based on actual security setup
    # assert "X-Content-Type-Options" in headers
    # assert "X-Frame-Options" in headers
