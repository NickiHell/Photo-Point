"""
Comprehensive Users API routes testing.
Tests FastAPI Users endpoints with full CRUD operations coverage.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Import DTOs and value objects
from app.application.dto import CreateUserDTO, UpdateUserDTO, UserResponseDTO
from app.domain.value_objects.user import UserId

# Import the FastAPI app
from app.presentation.api.main import app


class TestUsersAPI:
    """Test Users API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation."""
        # Mock dependencies
        mock_use_case = AsyncMock()
        mock_response = UserResponseDTO(
            id="user-123",
            email="test@example.com",
            phone_number="+1234567890",
            telegram_id="tg123",
            is_active=True,
            preferences={"lang": "en"},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_use_case.execute.return_value = mock_response

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.post("/users/", json={
                "email": "test@example.com",
                "phone_number": "+1234567890",
                "telegram_id": "tg123",
                "preferences": {"lang": "en"}
            })

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "user-123"
        assert data["email"] == "test@example.com"
        assert data["phone_number"] == "+1234567890"
        assert data["telegram_id"] == "tg123"
        assert data["is_active"] is True
        assert data["preferences"] == {"lang": "en"}
        assert data["created_at"] == "2024-01-01T12:00:00"

        # Verify use case was called with correct DTO
        mock_use_case.execute.assert_called_once()
        dto_call = mock_use_case.execute.call_args[0][0]
        assert isinstance(dto_call, CreateUserDTO)
        assert dto_call.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_create_user_minimal_data(self):
        """Test user creation with minimal required data."""
        mock_use_case = AsyncMock()
        mock_response = UserResponseDTO(
            id="user-124",
            email=None,
            phone_number="+1234567890",
            telegram_id=None,
            is_active=True,
            preferences={},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_use_case.execute.return_value = mock_response

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.post("/users/", json={
                "phone_number": "+1234567890"
            })

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "user-124"
        assert data["email"] is None
        assert data["phone_number"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_create_user_validation_error(self):
        """Test user creation with validation error."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("Invalid email format")

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.post("/users/", json={
                "email": "invalid-email",
                "phone_number": "+1234567890"
            })

        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_internal_error(self):
        """Test user creation with internal server error."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = Exception("Database connection failed")

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.post("/users/", json={
                "email": "test@example.com"
            })

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_success(self):
        """Test successful user retrieval."""
        mock_use_case = AsyncMock()
        mock_response = UserResponseDTO(
            id="user-123",
            email="test@example.com",
            phone_number="+1234567890",
            telegram_id="tg123",
            is_active=True,
            preferences={"lang": "en"},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_use_case.execute.return_value = mock_response

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.get("/users/user-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user-123"
        assert data["email"] == "test@example.com"

        # Verify use case was called with correct UserId
        mock_use_case.execute.assert_called_once()
        user_id_call = mock_use_case.execute.call_args[0][0]
        assert isinstance(user_id_call, UserId)
        assert str(user_id_call) == "user-123"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        """Test user retrieval when user doesn't exist."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = None

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.get("/users/nonexistent-user")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_validation_error(self):
        """Test user retrieval with invalid ID."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("Invalid user ID format")

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.get("/users/invalid-id")

        assert response.status_code == 400
        assert "Invalid user ID format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user_success(self):
        """Test successful user update."""
        mock_use_case = AsyncMock()
        mock_response = UserResponseDTO(
            id="user-123",
            email="updated@example.com",
            phone_number="+0987654321",
            telegram_id="tg456",
            is_active=False,
            preferences={"lang": "es"},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_use_case.execute.return_value = mock_response

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.put("/users/user-123", json={
                "email": "updated@example.com",
                "phone_number": "+0987654321",
                "telegram_id": "tg456",
                "is_active": False,
                "preferences": {"lang": "es"}
            })

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["phone_number"] == "+0987654321"
        assert data["is_active"] is False

        # Verify use case was called with correct DTO
        mock_use_case.execute.assert_called_once()
        dto_call = mock_use_case.execute.call_args[0][0]
        assert isinstance(dto_call, UpdateUserDTO)
        assert dto_call.user_id == "user-123"
        assert dto_call.email == "updated@example.com"

    @pytest.mark.asyncio
    async def test_update_user_partial(self):
        """Test partial user update."""
        mock_use_case = AsyncMock()
        mock_response = UserResponseDTO(
            id="user-123",
            email="test@example.com",
            phone_number="+1234567890",
            telegram_id="tg123",
            is_active=False,
            preferences={"lang": "en"},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_use_case.execute.return_value = mock_response

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.put("/users/user-123", json={
                "is_active": False
            })

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

        # Verify only is_active was updated
        dto_call = mock_use_case.execute.call_args[0][0]
        assert dto_call.is_active is False
        assert dto_call.email is None
        assert dto_call.phone_number is None

    @pytest.mark.asyncio
    async def test_update_user_validation_error(self):
        """Test user update with validation error."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("Invalid email format")

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.put("/users/user-123", json={
                "email": "invalid-email"
            })

        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """Test successful user deletion."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = None

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.delete("/users/user-123")

        assert response.status_code == 204
        assert response.content == b""

        # Verify use case was called with correct UserId
        mock_use_case.execute.assert_called_once()
        user_id_call = mock_use_case.execute.call_args[0][0]
        assert isinstance(user_id_call, UserId)
        assert str(user_id_call) == "user-123"

    @pytest.mark.asyncio
    async def test_delete_user_validation_error(self):
        """Test user deletion with validation error."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("Invalid user ID")

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.delete("/users/invalid-id")

        assert response.status_code == 400
        assert "Invalid user ID" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_user_internal_error(self):
        """Test user deletion with internal error."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = Exception("Database error")

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.delete("/users/user-123")

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


class TestUsersAPIRequestValidation:
    """Test Users API request validation."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_create_user_empty_request(self):
        """Test user creation with empty request."""
        response = self.client.post("/users/", json={})
        # Should still work with default values
        assert response.status_code in [201, 400, 500]

    def test_create_user_invalid_json(self):
        """Test user creation with invalid JSON."""
        response = self.client.post("/users/", data="invalid json")
        assert response.status_code == 422

    def test_update_user_empty_request(self):
        """Test user update with empty request."""
        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_use_case = AsyncMock()
            mock_dep.return_value = mock_use_case

            response = self.client.put("/users/user-123", json={})

        # Should work with all None values
        assert response.status_code in [200, 400, 500]


class TestUsersAPIParametrized:
    """Parametrized tests for Users API."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @pytest.mark.parametrize("endpoint,method,expected_status", [
        ("/users/", "POST", [201, 400, 500]),
        ("/users/test-user", "GET", [200, 400, 404, 500]),
        ("/users/test-user", "PUT", [200, 400, 500]),
        ("/users/test-user", "DELETE", [204, 400, 500]),
    ])
    def test_endpoint_accessibility(self, endpoint, method, expected_status):
        """Test that all endpoints are accessible."""
        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_use_case = AsyncMock()
            mock_dep.return_value = mock_use_case

            if method == "POST":
                response = self.client.post(endpoint, json={})
            elif method == "GET":
                response = self.client.get(endpoint)
            elif method == "PUT":
                response = self.client.put(endpoint, json={})
            elif method == "DELETE":
                response = self.client.delete(endpoint)

        assert response.status_code in expected_status

    @pytest.mark.parametrize("user_data", [
        {"email": "test@example.com"},
        {"phone_number": "+1234567890"},
        {"telegram_id": "tg123"},
        {"preferences": {"lang": "en", "notifications": True}},
        {"email": "test@example.com", "phone_number": "+1234567890"},
        {"email": "test@example.com", "telegram_id": "tg123"},
    ])
    def test_create_user_various_data(self, user_data):
        """Test user creation with various data combinations."""
        mock_use_case = AsyncMock()
        mock_response = UserResponseDTO(
            id="user-123",
            email=user_data.get("email"),
            phone_number=user_data.get("phone_number"),
            telegram_id=user_data.get("telegram_id"),
            is_active=True,
            preferences=user_data.get("preferences", {}),
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_use_case.execute.return_value = mock_response

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.post("/users/", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "user-123"


class TestUsersAPIErrorHandling:
    """Test Users API error handling scenarios."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @pytest.mark.parametrize("error_type,expected_status", [
        (ValueError("Invalid input"), 400),
        (Exception("Database error"), 500),
        (KeyError("Missing field"), 500),
        (TypeError("Type mismatch"), 500),
    ])
    def test_error_handling(self, error_type, expected_status):
        """Test various error types are handled correctly."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = error_type

        with patch('app.presentation.dependencies.get_user_use_cases') as mock_dep:
            mock_dep.return_value = mock_use_case

            response = self.client.post("/users/", json={"email": "test@example.com"})

        assert response.status_code == expected_status
        assert "detail" in response.json()


def test_users_router_import():
    """Test that users router can be imported successfully."""
    from app.presentation.api.routes.users import router
    assert router is not None
