"""
Custom application errors and exception handling
"""

from typing import Optional, Any


class AppError(Exception):
    """Base application error"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON response"""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


class ValidationError(AppError):
    """Validation error"""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundError(AppError):
    """Resource not found error"""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details
        )


class UnauthorizedError(AppError):
    """Unauthorized access error"""

    def __init__(self, message: str = "Unauthorized", details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
            details=details
        )


class AIProviderError(AppError):
    """Error from AI provider"""

    def __init__(self, message: str, provider: str, details: Optional[dict[str, Any]] = None):
        details = details or {}
        details["provider"] = provider
        super().__init__(
            message=message,
            status_code=502,
            error_code="AI_PROVIDER_ERROR",
            details=details
        )
