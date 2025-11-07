"""
Group schemas for API request/response validation.
"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class GroupCreate(BaseModel):
    """Schema for creating a new group."""

    name: str = Field(..., min_length=1, max_length=255, description="Group name")


class GroupUpdate(BaseModel):
    """Schema for updating a group."""

    name: str = Field(..., min_length=1, max_length=255, description="New group name")


class GroupResponse(BaseModel):
    """Schema for group response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    member_count: int = Field(default=0, description="Number of members in the group")
