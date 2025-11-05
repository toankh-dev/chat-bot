"""Group domain model"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Group(BaseModel):
    """Group domain model"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationships (populated when needed)
    user_count: Optional[int] = 0
    chatbot_count: Optional[int] = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
