"""
AI Model schemas for API request/response validation.
"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AiModelCreate(BaseModel):
    """Schema for creating a new AI model."""

    name: str = Field(..., min_length=1, max_length=100, description="Model name (e.g., gpt-4o, claude-3-5-sonnet)")


class AiModelUpdate(BaseModel):
    """Schema for updating an AI model."""

    name: str = Field(..., min_length=1, max_length=100, description="New model name")


class AiModelResponse(BaseModel):
    """Schema for AI model response."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    name: str
    created_at: datetime
    updated_at: datetime

