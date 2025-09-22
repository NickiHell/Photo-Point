"""
User management API endpoints.
"""

try:
    from fastapi import APIRouter, Depends, HTTPException, status
    from pydantic import BaseModel, Field

    from ....application.dto import (
        CreateUserRequest,
        UpdateUserRequest,
        UserResponseDTO,
    )
    from ....application.use_cases.user_management import (
        CreateUserUseCase,
        GetUserUseCase,
        UpdateUserUseCase,
    )
    from ....domain.value_objects.user import UserId
    from ...dependencies import (
        get_create_user_use_case,
        get_get_user_use_case,
        get_update_user_use_case,
    )

    router = APIRouter()

    class CreateUserRequestModel(BaseModel):
        """Create user request model."""

        name: str = Field(..., description="User name")
        email: str | None = Field(None, description="User email address")
        phone: str | None = Field(None, description="User phone number")
        telegram_chat_id: str | None = Field(None, description="User Telegram chat ID")
        preferences: list[str] | None = Field(None, description="User preferences")

    class UpdateUserRequestModel(BaseModel):
        """Update user request model."""

        name: str | None = Field(None, description="User name")
        email: str | None = Field(None, description="User email address")
        phone: str | None = Field(None, description="User phone number")
        telegram_chat_id: str | None = Field(None, description="User Telegram chat ID")
        is_active: bool | None = Field(None, description="User active status")
        preferences: list[str] | None = Field(None, description="User preferences")

    class UserResponse(BaseModel):
        """User response model."""

        id: str
        email: str | None = None
        phone_number: str | None = None
        telegram_id: str | None = None
        is_active: bool = True
        preferences: list[str] | None = None
        created_at: str

    @router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
    async def create_user(
        request: CreateUserRequestModel,
        use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    ):
        """Create a new user."""
        try:
            request_obj = CreateUserRequest(
                name=request.name,
                email=request.email,
                phone=request.phone,
                telegram_chat_id=request.telegram_chat_id,
                preferences=request.preferences or [],
            )

            user_response = await use_case.execute(request_obj)

            if not user_response.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=user_response.message,
                )

            return UserResponse(
                id=user_response.data.id,
                email=user_response.data.email,
                phone_number=user_response.data.phone,
                telegram_id=user_response.data.telegram_chat_id,
                is_active=user_response.data.is_active,
                preferences=user_response.data.preferences,
                created_at=user_response.data.created_at.isoformat(),
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @router.get("/{user_id}", response_model=UserResponse)
    async def get_user(
        user_id: str, use_case: GetUserUseCase = Depends(get_get_user_use_case)
    ):
        """Get user by ID."""
        try:
            user_response = await use_case.execute(user_id)

            if not user_response.success or not user_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            return UserResponse(
                id=user_response.data.id,
                email=user_response.data.email,
                phone_number=user_response.data.phone,
                telegram_id=user_response.data.telegram_chat_id,
                is_active=user_response.data.is_active,
                preferences=user_response.data.preferences,
                created_at=user_response.data.created_at.isoformat(),
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @router.put("/{user_id}", response_model=UserResponse)
    async def update_user(
        user_id: str,
        request: UpdateUserRequestModel,
        use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
    ):
        """Update user by ID."""
        try:
            request_obj = UpdateUserRequest(
                name=request.name,
                email=request.email,
                phone=request.phone,
                telegram_chat_id=request.telegram_chat_id,
                is_active=request.is_active,
                preferences=request.preferences,
            )

            user_response = await use_case.execute(user_id, request_obj)

            if not user_response.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=user_response.message,
                )

            return UserResponse(
                id=user_response.data.id,
                email=user_response.data.email,
                phone_number=user_response.data.phone,
                telegram_id=user_response.data.telegram_chat_id,
                is_active=user_response.data.is_active,
                preferences=user_response.data.preferences,
                created_at=user_response.data.created_at.isoformat(),
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

except ImportError:
    # Fallback for when dependencies are not available - create real APIRouter
    from fastapi import APIRouter

    router = APIRouter()
