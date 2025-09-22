"""
Application exceptions.
"""

from fastapi import HTTPException, status


class ApplicationError(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EntityNotFoundError(ApplicationError):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(message)


class ValidationError(ApplicationError):
    """Raised when validation fails."""

    def __init__(self, message: str):
        super().__init__(message)


class DuplicateEntityError(ApplicationError):
    """Raised when an entity already exists."""

    def __init__(self, entity_type: str, identifier: str):
        self.entity_type = entity_type
        self.identifier = identifier
        message = f"{entity_type} with identifier {identifier} already exists"
        super().__init__(message)


class UnauthorizedError(ApplicationError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class ForbiddenError(ApplicationError):
    """Raised when operation is forbidden."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)


class ConfigurationError(ApplicationError):
    """Raised when there is a configuration error."""

    def __init__(self, message: str):
        super().__init__(message)


class ExternalServiceError(ApplicationError):
    """Raised when an external service returns an error."""

    def __init__(self, service: str, message: str):
        self.service = service
        full_message = f"Error from {service}: {message}"
        super().__init__(full_message)


def http_exception_from_application_error(error: ApplicationError) -> HTTPException:
    """Convert application error to HTTP exception."""
    if isinstance(error, EntityNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.message,
        )
    elif isinstance(error, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.message,
        )
    elif isinstance(error, DuplicateEntityError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.message,
        )
    elif isinstance(error, UnauthorizedError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif isinstance(error, ForbiddenError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.message,
        )
    elif isinstance(error, ConfigurationError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration error",
        )
    elif isinstance(error, ExternalServiceError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error.message,
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
