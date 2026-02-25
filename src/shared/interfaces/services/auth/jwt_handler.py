"""JWT handler interface for application layer.

This defines the contract the application layer expects from any JWT handler
implementation. Infrastructure code can implement this interface.
"""
from typing import Protocol, Dict, Any


class IJWTHandler(Protocol):
    """Protocol describing JWT handler behaviour expected by the application layer."""

    def create_access_token(self, subject: str, additional_claims: Dict[str, Any] | None = None) -> str:
        ...

    def create_refresh_token(self, subject: str) -> str:
        ...

    def decode_token(self, token: str) -> Dict[str, Any]:
        ...
