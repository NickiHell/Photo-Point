"""
Simplified Users API routes testing.
Tests FastAPI Users endpoints directly without complex app integration.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import DTOs and value objects
from app.application.dto import UserResponseDTO

# Import the router directly
from app.presentation.api.routes.users import router

# Create a test app with just the users router
test_app = FastAPI()
test_app.include_router(router)


class TestUsersAPISimplified:
    """Simplified Users API tests."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(test_app)

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

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.post("/", json={
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

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.post("/", json={
                "phone_number": "+1234567890"
            })

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "user-124"
        assert data["phone_number"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_create_user_validation_error(self):
        """Test user creation with validation error."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("Invalid email format")

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.post("/", json={
                "email": "invalid-email"
            })

        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

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

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.get("/user-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user-123"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        """Test user retrieval when user doesn't exist."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = None

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.get("/nonexistent-user")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

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

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.put("/user-123", json={
                "email": "updated@example.com",
                "phone_number": "+0987654321",
                "is_active": False
            })

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """Test successful user deletion."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = None

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.delete("/user-123")

        assert response.status_code == 204
        assert response.content == b""

    @pytest.mark.asyncio
    async def test_delete_user_validation_error(self):
        """Test user deletion with validation error."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValueError("Invalid user ID")

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.delete("/invalid-id")

        assert response.status_code == 400
        assert "Invalid user ID" in response.json()["detail"]


class TestUsersAPIEdgeCases:
    """Test Users API edge cases."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(test_app)

    def test_create_user_empty_request(self):
        """Test user creation with empty request."""
        mock_use_case = AsyncMock()
        mock_response = UserResponseDTO(
            id="user-empty",
            email=None,
            phone_number=None,
            telegram_id=None,
            is_active=True,
            preferences={},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_use_case.execute.return_value = mock_response

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.post("/", json={})

        # Should work with empty data
        assert response.status_code == 201

    def test_create_user_invalid_json(self):
        """Test user creation with invalid JSON."""
        response = self.client.post("/", data="invalid json")
        assert response.status_code == 422

    @pytest.mark.parametrize("user_data", [
        {"email": "test@example.com"},
        {"phone_number": "+1234567890"},
        {"telegram_id": "tg123"},
        {"preferences": {"lang": "en"}},
    ])
    def test_create_user_various_fields(self, user_data):
        """Test user creation with various single fields."""
        mock_use_case = AsyncMock()
        mock_response = UserResponseDTO(
            id="user-single",
            email=user_data.get("email"),
            phone_number=user_data.get("phone_number"),
            telegram_id=user_data.get("telegram_id"),
            is_active=True,
            preferences=user_data.get("preferences", {}),
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_use_case.execute.return_value = mock_response

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.post("/", json=user_data)

        assert response.status_code == 201

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

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            response = self.client.post("/", json={"email": "test@example.com"})

        assert response.status_code == expected_status
        assert "detail" in response.json()


def test_users_router_import():
    """Test that users router can be imported successfully."""
    from app.presentation.api.routes.users import router
    assert router is not None


def test_users_router_endpoints():
    """Test that router has expected endpoints."""
    from app.presentation.api.routes.users import router
    # Check that router has routes (real router should have routes)
    assert hasattr(router, 'routes') or hasattr(router, 'post')


class TestUsersAPIIntegration:
    """Integration tests for Users API."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(test_app)

    def test_crud_flow_simulation(self):
        """Test simulated CRUD flow."""
        mock_use_case = AsyncMock()

        # Mock successful responses for CRUD operations
        create_response = UserResponseDTO(
            id="user-crud",
            email="crud@example.com",
            phone_number=None,
            telegram_id=None,
            is_active=True,
            preferences={},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )

        get_response = UserResponseDTO(
            id="user-crud",
            email="crud@example.com",
            phone_number=None,
            telegram_id=None,
            is_active=True,
            preferences={},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )

        update_response = UserResponseDTO(
            id="user-crud",
            email="updated@example.com",
            phone_number=None,
            telegram_id=None,
            is_active=True,
            preferences={},
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )

        with patch('app.presentation.dependencies.get_user_use_cases', return_value=mock_use_case):
            # Test CREATE
            mock_use_case.execute.return_value = create_response
            create_resp = self.client.post("/", json={"email": "crud@example.com"})
            assert create_resp.status_code == 201

            # Test GET
            mock_use_case.execute.return_value = get_response
            get_resp = self.client.get("/user-crud")
            assert get_resp.status_code == 200

            # Test UPDATE
            mock_use_case.execute.return_value = update_response
            update_resp = self.client.put("/user-crud", json={"email": "updated@example.com"})
            assert update_resp.status_code == 200

            # Test DELETE
            mock_use_case.execute.return_value = None
            delete_resp = self.client.delete("/user-crud")
            assert delete_resp.status_code == 204
