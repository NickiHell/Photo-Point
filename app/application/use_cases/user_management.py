"""
User management use cases.
"""
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from ..dto import (
    CreateUserRequest, UpdateUserRequest, UserResponse, OperationResponse
)
from ...domain.entities.user import User
from ...domain.value_objects.user import UserId, UserName, Email, PhoneNumber, TelegramChatId
from ...domain.repositories import UserRepository


class CreateUserUseCase:
    """Use case for creating a new user."""
    
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository
    
    async def execute(self, request: CreateUserRequest) -> OperationResponse:
        """Execute the create user use case."""
        try:
            # Create value objects
            user_id = UserId(str(uuid.uuid4()))
            name = UserName(request.name)
            
            email = None
            if request.email:
                email = Email(request.email)
            
            phone = None
            if request.phone:
                phone = PhoneNumber(request.phone)
            
            telegram_chat_id = None
            if request.telegram_chat_id:
                telegram_chat_id = TelegramChatId(request.telegram_chat_id)
            
            # Create user entity
            user = User(
                user_id=user_id,
                name=name,
                email=email,
                phone=phone,
                telegram_chat_id=telegram_chat_id,
                is_active=True
            )
            
            # Add preferences
            for preference in request.preferences:
                user.add_preference(preference)
            
            # Save user
            await self._user_repository.save(user)
            
            # Create response
            response_data = UserResponse(
                id=str(user.id.value),
                name=user.name.value,
                email=user.email.value if user.email else None,
                phone=user.phone.value if user.phone else None,
                telegram_chat_id=user.telegram_chat_id.value if user.telegram_chat_id else None,
                is_active=user.is_active,
                preferences=list(user.preferences),
                available_channels=list(user.get_available_channels()),
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return OperationResponse(
                success=True,
                message="User created successfully",
                data=response_data
            )
            
        except ValueError as e:
            return OperationResponse(
                success=False,
                message="Invalid input data",
                errors=[str(e)]
            )
        except Exception as e:
            return OperationResponse(
                success=False,
                message="Failed to create user",
                errors=[str(e)]
            )


class GetUserUseCase:
    """Use case for retrieving a user."""
    
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository
    
    async def execute(self, user_id: str) -> OperationResponse:
        """Execute the get user use case."""
        try:
            user_id_vo = UserId(user_id)
            user = await self._user_repository.get_by_id(user_id_vo)
            
            if not user:
                return OperationResponse(
                    success=False,
                    message="User not found",
                    errors=["User with given ID does not exist"]
                )
            
            response_data = UserResponse(
                id=str(user.id.value),
                name=user.name.value,
                email=user.email.value if user.email else None,
                phone=user.phone.value if user.phone else None,
                telegram_chat_id=user.telegram_chat_id.value if user.telegram_chat_id else None,
                is_active=user.is_active,
                preferences=list(user.preferences),
                available_channels=list(user.get_available_channels()),
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return OperationResponse(
                success=True,
                message="User retrieved successfully",
                data=response_data
            )
            
        except ValueError as e:
            return OperationResponse(
                success=False,
                message="Invalid user ID",
                errors=[str(e)]
            )
        except Exception as e:
            return OperationResponse(
                success=False,
                message="Failed to retrieve user",
                errors=[str(e)]
            )


class UpdateUserUseCase:
    """Use case for updating a user."""
    
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository
    
    async def execute(self, user_id: str, request: UpdateUserRequest) -> OperationResponse:
        """Execute the update user use case."""
        try:
            user_id_vo = UserId(user_id)
            user = await self._user_repository.get_by_id(user_id_vo)
            
            if not user:
                return OperationResponse(
                    success=False,
                    message="User not found",
                    errors=["User with given ID does not exist"]
                )
            
            # Update fields if provided
            if request.name is not None:
                user.update_name(UserName(request.name))
            
            if request.email is not None:
                user.update_email(Email(request.email) if request.email else None)
            
            if request.phone is not None:
                user.update_phone(PhoneNumber(request.phone) if request.phone else None)
            
            if request.telegram_chat_id is not None:
                user.update_telegram_chat_id(
                    TelegramChatId(request.telegram_chat_id) if request.telegram_chat_id else None
                )
            
            if request.is_active is not None:
                if request.is_active:
                    user.activate()
                else:
                    user.deactivate()
            
            if request.preferences is not None:
                # Clear existing preferences and add new ones
                current_preferences = user.preferences.copy()
                for pref in current_preferences:
                    user.remove_preference(pref)
                
                for pref in request.preferences:
                    user.add_preference(pref)
            
            # Save updated user
            await self._user_repository.save(user)
            
            # Create response
            response_data = UserResponse(
                id=str(user.id.value),
                name=user.name.value,
                email=user.email.value if user.email else None,
                phone=user.phone.value if user.phone else None,
                telegram_chat_id=user.telegram_chat_id.value if user.telegram_chat_id else None,
                is_active=user.is_active,
                preferences=list(user.preferences),
                available_channels=list(user.get_available_channels()),
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return OperationResponse(
                success=True,
                message="User updated successfully",
                data=response_data
            )
            
        except ValueError as e:
            return OperationResponse(
                success=False,
                message="Invalid input data",
                errors=[str(e)]
            )
        except Exception as e:
            return OperationResponse(
                success=False,
                message="Failed to update user",
                errors=[str(e)]
            )


class GetAllActiveUsersUseCase:
    """Use case for retrieving all active users."""
    
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository
    
    async def execute(self) -> OperationResponse:
        """Execute the get all active users use case."""
        try:
            users = await self._user_repository.get_all_active()
            
            response_data = []
            for user in users:
                response_data.append(UserResponse(
                    id=str(user.id.value),
                    name=user.name.value,
                    email=user.email.value if user.email else None,
                    phone=user.phone.value if user.phone else None,
                    telegram_chat_id=user.telegram_chat_id.value if user.telegram_chat_id else None,
                    is_active=user.is_active,
                    preferences=list(user.preferences),
                    available_channels=list(user.get_available_channels()),
                    created_at=user.created_at,
                    updated_at=user.updated_at
                ))
            
            return OperationResponse(
                success=True,
                message=f"Retrieved {len(users)} active users",
                data=response_data
            )
            
        except Exception as e:
            return OperationResponse(
                success=False,
                message="Failed to retrieve users",
                errors=[str(e)]
            )