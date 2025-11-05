"""Chatbot domain model"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal


class ChatbotStatus(str, Enum):
    """Chatbot status"""
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class ChatbotProvider(str, Enum):
    """LLM provider options"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    BEDROCK = "bedrock"


class Chatbot(BaseModel):
    """Chatbot domain model"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    provider: ChatbotProvider
    model: str = Field(..., max_length=100)
    temperature: Decimal = Field(default=Decimal("0.7"), ge=0, le=2)
    max_tokens: int = Field(default=2048, gt=0)
    top_p: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    fallback_message: Optional[str] = None
    max_conversation_length: int = Field(default=50, gt=0)
    enable_function_calling: bool = True
    api_base_url: Optional[str] = Field(None, max_length=500)
    created_by: int
    status: ChatbotStatus = ChatbotStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationships (populated when needed)
    creator_name: Optional[str] = None
    tools: List[int] = Field(default_factory=list)
    tool_names: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v)
        }


class ChatbotConfig(BaseModel):
    """Chatbot configuration (for updates)"""
    temperature: Optional[Decimal] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    top_p: Optional[Decimal] = Field(None, ge=0, le=1)
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    fallback_message: Optional[str] = None
    max_conversation_length: Optional[int] = Field(None, gt=0)
    enable_function_calling: Optional[bool] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
