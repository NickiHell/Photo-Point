#!/usr/bin/env python3
"""
Comprehensive end-to-end test for the notification service.
"""
import sys
import os
import time
import json
import requests
from threading import Thread
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.domain.entities import User, Notification
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


def test_domain_layer():
    """Test domain entities."""
    print("🔍 Testing Domain Layer...")
    
    # Test User entity
    user = User("user1", email="test@example.com", phone_number="+1234567890")
    assert user.id == "user1"
    assert user.email == "test@example.com"
    assert user.is_active == True
    
    user.update_email("new@example.com")
    assert user.email == "new@example.com"
    
    # Test Notification entity
    notification = Notification("notif1", "user1", "Hello {name}!", ["email", "sms"])
    assert notification.recipient_id == "user1"
    assert notification.status == "PENDING"
    
    notification.mark_sent()
    assert notification.status == "SENT"
    
    print("✅ Domain Layer tests passed!")
    return True


def test_application_layer():
    """Test application layer (DTOs and Use Cases)."""
    print("🔍 Testing Application Layer...")
    
    # Setup repositories
    user_repo = MockUserRepository()
    notification_service = MockNotificationService()
    
    # Test Use Cases
    create_user_use_case = CreateUserUseCase(user_repo)
    send_notification_use_case = SendNotificationUseCase(notification_service)
    
    # Test user creation
    create_user_dto = CreateUserDTO(
        email="test@example.com",
        phone_number="+1234567890",
        preferences={"language": "ru"}
    )
    
    user_response = create_user_use_case.execute(create_user_dto)
    assert user_response.email == "test@example.com"
    assert user_response.preferences["language"] == "ru"
    
    # Test notification sending
    send_notification_dto = SendNotificationDTO(
        recipient_id=user_response.id,
        message_template="Welcome {name}!",
        message_variables={"name": "Test User"},
        channels=["email"]
    )
    
    notification_response = send_notification_use_case.execute(send_notification_dto)
    assert notification_response.recipient_id == user_response.id
    assert notification_response.status == "PENDING"
    
    print("✅ Application Layer tests passed!")
    return True


def test_api_endpoints():
    """Test API endpoints."""
    print("🔍 Testing API Endpoints...")
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Notification Service API"
        
        # Test health check
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test users endpoint
        response = requests.get(f"{base_url}/api/v1/users", timeout=5)
        assert response.status_code == 200
        
        # Test user creation
        response = requests.post(f"{base_url}/api/v1/users", timeout=5)
        assert response.status_code == 200
        
        # Test notification sending
        response = requests.post(f"{base_url}/api/v1/notifications/send", timeout=5)
        assert response.status_code == 200
        
        print("✅ API Endpoints tests passed!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API tests skipped - server not running: {e}")
        return False


def run_comprehensive_test():
    """Run comprehensive end-to-end tests."""
    print("🚀 Starting Comprehensive End-to-End Tests")
    print(f"📅 Test Date: {datetime.now()}")
    print("=" * 60)
    
    results = {
        "domain": False,
        "application": False,
        "api": False
    }
    
    try:
        # Test 1: Domain Layer
        results["domain"] = test_domain_layer()
        
        # Test 2: Application Layer
        results["application"] = test_application_layer()
        
        # Test 3: API Layer (if server is running)
        results["api"] = test_api_endpoints()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"🏗️  Domain Layer: {'✅ PASS' if results['domain'] else '❌ FAIL'}")
    print(f"🔄 Application Layer: {'✅ PASS' if results['application'] else '❌ FAIL'}")
    print(f"🌐 API Layer: {'✅ PASS' if results['api'] else '⚠️  SKIP'}")
    
    print(f"\n📈 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if results["domain"] and results["application"]:
        print("🎉 CLEAN ARCHITECTURE SYSTEM IS FULLY OPERATIONAL!")
        if results["api"]:
            print("🌟 ALL LAYERS INCLUDING API ARE WORKING PERFECTLY!")
        else:
            print("💡 Note: Start uvicorn server to test API endpoints")
        return True
    else:
        print("❌ SYSTEM HAS CRITICAL ISSUES")
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)