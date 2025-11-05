"""Custom exception classes"""


class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, code: str = "ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """Validation error exception"""
    def __init__(self, message: str, details=None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=400)
        self.details = details


class NotFoundError(AppException):
    """Resource not found exception"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND", status_code=404)


class UnauthorizedError(AppException):
    """Unauthorized exception"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


class ForbiddenError(AppException):
    """Forbidden exception"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, code="FORBIDDEN", status_code=403)


class ConflictError(AppException):
    """Resource conflict exception"""
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, code="CONFLICT", status_code=409)


class DatabaseError(AppException):
    """Database operation error"""
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message, code="DATABASE_ERROR", status_code=500)
