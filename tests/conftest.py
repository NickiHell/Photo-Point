"""
Test configuration and fixtures.
"""
from unittest.mock import AsyncMock, Mock

import pytest

try:
    import pytest_asyncio

    @pytest_asyncio.fixture
    async def async_session():
        """Fixture for async test session."""
        # This would be a real database session in a full implementation
        mock_session = Mock()
        yield mock_session

except ImportError:
    # Fallback fixture for when pytest-asyncio is not available
    @pytest.fixture
    def async_session():
        return Mock()


@pytest.fixture
def mock_user_repository():
    """Mock user repository for testing."""
    repository = Mock()
    repository.save = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.get_all_active = AsyncMock()
    repository.delete = AsyncMock()
    return repository


@pytest.fixture
def mock_notification_repository():
    """Mock notification repository for testing."""
    repository = Mock()
    repository.save = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.get_pending = AsyncMock()
    repository.get_by_recipient = AsyncMock()
    repository.delete = AsyncMock()
    return repository


@pytest.fixture
def mock_delivery_repository():
    """Mock delivery repository for testing."""
    repository = Mock()
    repository.save = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.get_by_notification = AsyncMock()
    repository.get_pending_retries = AsyncMock()
    repository.get_statistics = AsyncMock()
    return repository


@pytest.fixture
def mock_email_provider():
    """Mock email notification provider."""
    provider = Mock()
    provider.send_notification = AsyncMock()
    provider.validate_configuration = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_sms_provider():
    """Mock SMS notification provider."""
    provider = Mock()
    provider.send_notification = AsyncMock()
    provider.validate_configuration = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_telegram_provider():
    """Mock Telegram notification provider."""
    provider = Mock()
    provider.send_notification = AsyncMock()
    provider.validate_configuration = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "phone_number": "+1234567890",
        "telegram_id": "@testuser",
        "is_active": True,
        "preferences": {"email_notifications": True}
    }


@pytest.fixture
def sample_notification_data():
    """Sample notification data for testing."""
    return {
        "id": "test-notification-456",
        "recipient_id": "test-user-123",
        "message_template": "Hello {{name}}!",
        "message_variables": {"name": "John"},
        "channels": ["email", "sms"],
        "priority": "MEDIUM",
        "metadata": {"source": "test"}
    }


@pytest.fixture
def sample_delivery_data():
    """Sample delivery data for testing."""
    return {
        "id": "test-delivery-789",
        "notification_id": "test-notification-456",
        "channel": "email",
        "provider": "smtp",
        "status": "PENDING"
    }
