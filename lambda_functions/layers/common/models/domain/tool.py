"""Tool domain model"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class ToolStatus(str, Enum):
    """Tool status"""
    ACTIVE = "active"
    DISABLED = "disabled"


class Tool(BaseModel):
    """Tool domain model"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: ToolStatus = ToolStatus.ACTIVE

    class Config:
        use_enum_values = True
