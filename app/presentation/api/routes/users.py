"""
User management API endpoints.
"""

try:
    from fastapi import APIRouter, Depends, HTTPException, status
    from pydantic import BaseModel, Field

    from ....application.dto import CreateUserDTO, UpdateUserDTO, UserResponseDTO
    from ....application.use_cases.user_management import (
        CreateUserUseCase,
        DeleteUserUseCase,
        GetUserUseCase,
        UpdateUserUseCase,
    )
    from ....domain.value_objects.user import UserId
    from ...dependencies import get_user_use_cases

    router = APIRouter()


    class CreateUserRequest(BaseModel):
        """Create user request model."""
        email: str | None = Field(None, description="User email address")
        phone_number: str | None = Field(None, description="User phone number")
        telegram_id: str | None = Field(None, description="User Telegram ID")
        preferences: dict = Field(default_factory=dict, description="User preferences")


    class UpdateUserRequest(BaseModel):
        """Update user request model."""
        email: str | None = Field(None, description="User email address")
        phone_number: str | None = Field(None, description="User phone number")
        telegram_id: str | None = Field(None, description="User Telegram ID")
        is_active: bool | None = Field(None, description="User active status")
        preferences: dict | None = Field(None, description="User preferences")


    class UserResponse(BaseModel):
        """User response model."""
        id: str = Field(description="User ID")
        email: str | None = Field(None, description="User email address")
        phone_number: str | None = Field(None, description="User phone number")
        telegram_id: str | None = Field(None, description="User Telegram ID")
        is_active: bool = Field(description="User active status")
        preferences: dict = Field(description="User preferences")
        created_at: str = Field(description="User creation timestamp")


    @router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
    async def create_user(
        request: CreateUserRequest,
        use_case: CreateUserUseCase = Depends(get_user_use_cases)
    ):
        """Create a new user."""
        try:
            dto = CreateUserDTO(
                email=request.email,
                phone_number=request.phone_number,
                telegram_id=request.telegram_id,
                preferences=request.preferences
            )

            user_response = await use_case.execute(dto)

            return UserResponse(
                id=user_response.id,
                email=user_response.email,
                phone_number=user_response.phone_number,
                telegram_id=user_response.telegram_id,
                is_active=user_response.is_active,
                preferences=user_response.preferences,
                created_at=user_response.created_at.isoformat()
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


    @router.get("/{user_id}", response_model=UserResponse)
    async def get_user(
        user_id: str,
        use_case: GetUserUseCase = Depends(get_user_use_cases)
    ):
        """Get user by ID."""
        try:
            user_response = await use_case.execute(UserId(user_id))

            if not user_response:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            return UserResponse(
                id=user_response.id,
                email=user_response.email,
                phone_number=user_response.phone_number,
                telegram_id=user_response.telegram_id,
                is_active=user_response.is_active,
                preferences=user_response.preferences,
                created_at=user_response.created_at.isoformat()
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


    @router.put("/{user_id}", response_model=UserResponse)
    async def update_user(
        user_id: str,
        request: UpdateUserRequest,
        use_case: UpdateUserUseCase = Depends(get_user_use_cases)
    ):
        """Update user by ID."""
        try:
            dto = UpdateUserDTO(
                user_id=user_id,
                email=request.email,
                phone_number=request.phone_number,
                telegram_id=request.telegram_id,
                is_active=request.is_active,
                preferences=request.preferences
            )

            user_response = await use_case.execute(dto)

            return UserResponse(
                id=user_response.id,
                email=user_response.email,
                phone_number=user_response.phone_number,
                telegram_id=user_response.telegram_id,
                is_active=user_response.is_active,
                preferences=user_response.preferences,
                created_at=user_response.created_at.isoformat()
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


    @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_user(
        user_id: str,
        use_case: DeleteUserUseCase = Depends(get_user_use_cases)
    ):
        """Delete user by ID."""
        try:
            await use_case.execute(UserId(user_id))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

except ImportError:
    # Fallback for when dependencies are not available - create real APIRouter
    from fastapi import APIRouter
    router = APIRouter()
