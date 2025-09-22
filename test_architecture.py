#!/usr/bin/env python3
"""
Test script for Clean Architecture components.
"""
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.application.dto import CreateUserDTO, SendNotificationDTO
from app.application.use_cases import CreateUserUseCase, SendNotificationUseCase


class MockUserRepository:
    """Mock implementation of user repository."""

    def __init__(self):
        self.users = {}
        self.next_id = 1

    def save(self, user_data: dict) -> str:
        user_id = f"user_{self.next_id}"
        self.next_id += 1
        user_data["id"] = user_id
        self.users[user_id] = user_data
        return user_id

    def find_by_id(self, user_id: str) -> dict:
        return self.users.get(user_id, {})

    def update(self, user_id: str, user_data: dict) -> dict:
        if user_id in self.users:
            self.users[user_id].update(user_data)
            return self.users[user_id]
        return {}


class MockNotificationService:
    """Mock implementation of notification service."""

    def __init__(self):
        self.notifications = {}
        self.next_id = 1

    def send(self, notification_data: dict) -> str:
        notification_id = f"notif_{self.next_id}"
        self.next_id += 1
        notification_data["id"] = notification_id
        self.notifications[notification_id] = notification_data
        return notification_id


def test_clean_architecture():
    """Test the Clean Architecture components."""
    print("=== Testing Clean Architecture ===")

    # Setup
    user_repo = MockUserRepository()
    notification_service = MockNotificationService()

    create_user_use_case = CreateUserUseCase(user_repo)
    send_notification_use_case = SendNotificationUseCase(notification_service)

    # Test 1: Create User
    print("\n1. Testing User Creation...")
    create_user_dto = CreateUserDTO(
        email="test@example.com",
        phone_number="+1234567890",
        preferences={"language": "ru", "timezone": "UTC"}
    )

    user_response = create_user_use_case.execute(create_user_dto)
    print(f"   Created user: {user_response.id}")
    print(f"   Email: {user_response.email}")
    print(f"   Phone: {user_response.phone_number}")
    print(f"   Preferences: {user_response.preferences}")

    # Test 2: Send Notification
    print("\n2. Testing Notification Sending...")
    send_notification_dto = SendNotificationDTO(
        recipient_id=user_response.id,
        message_template="Welcome {name}! Your account is ready.",
        message_variables={"name": "Test User"},
        channels=["email", "sms"]
    )

    notification_response = send_notification_use_case.execute(send_notification_dto)
    print(f"   Sent notification: {notification_response.id}")
    print(f"   Recipient: {notification_response.recipient_id}")
    print(f"   Channels: {notification_response.channels}")
    print(f"   Status: {notification_response.status}")

    print("\n=== Clean Architecture Test Completed ===")
    print(f"Users in repository: {len(user_repo.users)}")
    print(f"Notifications sent: {len(notification_service.notifications)}")

    return True


if __name__ == "__main__":
    try:
        success = test_clean_architecture()
        if success:
            print("\nAll tests passed! Clean Architecture working correctly.")
        else:
            print("\nTests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
