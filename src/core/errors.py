"""
Custom exception hierarchy for the application.

Provides structured error handling with HTTP status code mapping.
"""

from typing import Optional, Dict, Any


class BaseAppException(Exception):
    """
    Base exception class for all application errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code
        error_code: Application-specific error code
        details: Additional error context
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


# Authentication & Authorization Errors
class AuthenticationError(BaseAppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTH_FAILED",
            details=details
        )


class AuthorizationError(BaseAppException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
            details=details
        )


class PermissionDeniedError(AuthorizationError):
    """Raised when user doesn't have permission for the action."""

    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            details={"error_type": "token_expired"}
        )


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(
            message=message,
            details={"error_type": "invalid_token"}
        )


# Resource Errors
class NotFoundError(BaseAppException):
    """Raised when requested resource doesn't exist."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details
        )


class ResourceNotFoundError(NotFoundError):
    """Raised when requested resource doesn't exist."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ResourceAlreadyExistsError(BaseAppException):
    """Raised when trying to create a resource that already exists."""

    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"{resource_type} with identifier '{identifier}' already exists",
            status_code=409,
            error_code="ALREADY_EXISTS",
            details={"resource_type": resource_type, "identifier": identifier}
        )


class ResourceConflictError(BaseAppException):
    """Raised when resource operation conflicts with current state."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )


# Validation Errors
class ValidationError(BaseAppException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field_errors: Optional[Dict[str, str]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or {}}
        )


# Database Errors
class DatabaseError(BaseAppException):
    """Raised when database operation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when cannot connect to database."""

    def __init__(self, db_type: str):
        super().__init__(
            message=f"Failed to connect to {db_type}",
            details={"db_type": db_type}
        )


# External Service Errors
class ExternalServiceError(BaseAppException):
    """Raised when external service call fails."""

    def __init__(self, service_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{service_name} error: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name, **(details or {})}
        )


class BedrockError(ExternalServiceError):
    """Raised when AWS Bedrock API call fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            service_name="AWS Bedrock",
            message=message,
            details=details
        )


# Business Logic Errors
class BusinessRuleViolationError(BaseAppException):
    """Raised when business rule is violated."""

    def __init__(self, message: str, rule: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule}
        )


class RateLimitExceededError(BaseAppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit: int, window_seconds: int):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window_seconds} seconds",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window_seconds": window_seconds}
        )


# WebSocket Errors
class WebSocketError(BaseAppException):
    """Raised when WebSocket operation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="WEBSOCKET_ERROR",
            details=details
        )


class ConnectionNotFoundError(WebSocketError):
    """Raised when WebSocket connection not found."""

    def __init__(self, connection_id: str):
        super().__init__(
            message=f"Connection {connection_id} not found",
            details={"connection_id": connection_id}
        )


# ============================================================================
# GitLab Integration Errors (Phase 2.1)
# ============================================================================

class GitLabError(ExternalServiceError):
    """Base exception for GitLab-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            service_name="GitLab",
            message=message,
            details=details
        )


class GitLabAuthenticationError(GitLabError):
    """Raised when GitLab authentication fails."""

    def __init__(self, message: str = "GitLab authentication failed. Invalid token or credentials."):
        super().__init__(
            message=message,
            details={"error_type": "authentication_failed"}
        )
        self.status_code = 401
        self.error_code = "GITLAB_AUTH_FAILED"


class GitLabNetworkError(GitLabError):
    """Raised when cannot connect to GitLab server."""

    def __init__(self, gitlab_url: str, message: str = "Cannot connect to GitLab"):
        super().__init__(
            message=f"{message}: {gitlab_url}",
            details={"gitlab_url": gitlab_url, "error_type": "network_error"}
        )


class GitLabAPIError(GitLabError):
    """Raised when GitLab API request fails."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if status_code:
            error_details["status_code"] = status_code
        super().__init__(message=message, details=error_details)


class GitLabRateLimitError(GitLabError):
    """Raised when GitLab API rate limit is exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"GitLab API rate limit exceeded. Please retry after {retry_after} seconds.",
            details={"retry_after": retry_after, "error_type": "rate_limit"}
        )
        self.status_code = 429
        self.error_code = "GITLAB_RATE_LIMIT"


class RepositoryNotFoundError(GitLabError):
    """Raised when GitLab repository not found."""

    def __init__(self, repo_id: str):
        super().__init__(
            message=f"Repository '{repo_id}' not found in GitLab",
            details={"repo_id": repo_id}
        )
        self.status_code = 404


class RepositoryBranchNotFoundError(GitLabError):
    """Raised when repository branch not found."""

    def __init__(self, repo_id: str, branch: str):
        super().__init__(
            message=f"Branch '{branch}' not found in repository '{repo_id}'",
            details={"repo_id": repo_id, "branch": branch}
        )
        self.status_code = 404


class FileContentFetchError(GitLabError):
    """Raised when cannot fetch file content from GitLab."""

    def __init__(self, file_path: str, message: str = "Failed to fetch file content"):
        super().__init__(
            message=f"{message}: {file_path}",
            details={"file_path": file_path}
        )


# ============================================================================
# Connector Errors
# ============================================================================

class ConnectorNotFoundError(NotFoundError):
    """Raised when connector not found."""

    def __init__(self, connector_type: str, message: Optional[str] = None):
        default_message = (
            f"{connector_type.capitalize()} connector not found. "
            f"Please setup connector via POST /api/v1/connectors/{connector_type}/token"
        )
        super().__init__(
            message=message or default_message,
            details={"connector_type": connector_type}
        )


class KnowledgeBaseNotFoundError(NotFoundError):
    """Raised when knowledge base not found."""

    def __init__(self, kb_id: int):
        super().__init__(
            message=f"Knowledge base with ID {kb_id} not found",
            details={"kb_id": kb_id}
        )


# ============================================================================
# Sync Operation Errors
# ============================================================================

class SyncError(BaseAppException):
    """Base exception for synchronization errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="SYNC_ERROR",
            details=details
        )


class SyncInProgressError(SyncError):
    """Raised when sync already in progress for the same resource."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"Sync already in progress for {resource_type} '{resource_id}'. "
                    f"Please wait for current sync to complete.",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )
        self.status_code = 409
        self.error_code = "SYNC_IN_PROGRESS"


class SyncQueueCreationError(SyncError):
    """Raised when failed to create sync queue items."""

    def __init__(self, message: str):
        super().__init__(
            message=f"Failed to create sync queue: {message}",
            details={"error_type": "queue_creation_failed"}
        )


# ============================================================================
# Vector Store Errors
# ============================================================================

class VectorStoreError(BaseAppException):
    """Base exception for vector store operations."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="VECTOR_STORE_ERROR",
            details=details
        )


class VectorStoreDimensionMismatchError(VectorStoreError):
    """Raised when embedding dimension doesn't match vector store collection."""

    def __init__(self, expected_dim: int, actual_dim: int):
        super().__init__(
            message=(
                f"Embedding dimension mismatch: collection expects {expected_dim} dimensions "
                f"but current provider uses {actual_dim} dimensions. "
                f"Please recreate the collection or use matching embedding provider."
            ),
            details={"expected_dimension": expected_dim, "actual_dimension": actual_dim}
        )


class VectorCleanupException(VectorStoreError):
    """Raised when vector cleanup operation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Vector cleanup failed: {message}",
            details=details
        )


class VectorInsertionError(VectorStoreError):
    """Raised when vector insertion fails."""

    def __init__(self, message: str, failed_count: int, total_count: int):
        success_rate = (total_count - failed_count) / total_count if total_count > 0 else 0
        super().__init__(
            message=f"{message}. Failed: {failed_count}/{total_count} ({success_rate:.1%} success rate)",
            details={
                "failed_count": failed_count,
                "total_count": total_count,
                "success_rate": success_rate
            }
        )
