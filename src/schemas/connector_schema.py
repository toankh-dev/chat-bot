"""
Pydantic schemas for admin connector management.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import re


class ConnectorResponse(BaseModel):
    """Response schema for connector information."""
    
    id: int
    name: str
    provider_type: str
    auth_type: str
    is_active: bool
    config_schema: Dict[str, Any]
    created_at: datetime
    has_credentials: bool

    class Config:
        from_attributes = True


class GitLabPersonalTokenSetupRequest(BaseModel):
    """Request schema for setting up GitLab personal token connector.

    This endpoint is idempotent - calling it multiple times will update the
    existing connector (preserving the ID) or create a new one if it doesn't exist.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Connector display name")
    gitlab_url: str = Field(..., description="GitLab instance URL")
    admin_token: Optional[str] = Field(None, description="Personal access token (optional if using env var)")
    
    @validator('gitlab_url')
    def validate_gitlab_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('GitLab URL must start with http:// or https://')
        return v.rstrip('/')
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Name can only contain letters, numbers, spaces, hyphens, and underscores')
        return v.strip()


class ConnectorCredentialsUpdateRequest(BaseModel):
    """Request schema for updating connector credentials."""

    personal_token: Optional[str] = Field(None, description="New personal access token")

    @validator('personal_token')
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Personal token cannot be empty if provided')
        return v.strip() if v else v


class ConnectorCreateRequest(BaseModel):
    """Generic request schema for creating connectors."""
    
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: str = Field(..., description="Provider type (gitlab)")
    auth_type: str = Field(..., description="Authentication type (personal_token)")
    config_schema: Dict[str, Any] = Field(..., description="Connector configuration")
    
    @validator('provider_type')
    def validate_provider_type(cls, v):
        allowed_providers = ['gitlab']  # Only GitLab for now
        if v.lower() not in allowed_providers:
            raise ValueError(f'Provider type must be one of: {", ".join(allowed_providers)}')
        return v.lower()
    
    @validator('auth_type')
    def validate_auth_type(cls, v):
        allowed_auth_types = ['personal_token']  # Only personal token for now
        if v.lower() not in allowed_auth_types:
            raise ValueError(f'Auth type must be one of: {", ".join(allowed_auth_types)}')
        return v.lower()