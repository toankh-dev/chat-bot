"""Chatbot request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class ChatbotCreate(BaseModel):
    """Chatbot creation request."""
    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    provider: str = Field(..., pattern="^(openai|anthropic|google)$")
    model: str = Field(..., min_length=1)
    temperature: Decimal = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, gt=0)
    top_p: Decimal = Field(default=1.0, ge=0, le=1)
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    fallback_message: Optional[str] = None
    max_conversation_length: int = Field(default=50, gt=0)
    enable_function_calling: bool = True
    api_key: str = Field(..., min_length=1)
    api_base_url: Optional[str] = None


class ChatbotUpdate(BaseModel):
    """Chatbot update request."""
    name: Optional[str] = None
    description: Optional[str] = None
    temperature: Optional[Decimal] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    status: Optional[str] = None


class ChatbotResponse(BaseModel):
    """Chatbot response model."""
    id: int
    name: str
    description: Optional[str]
    provider: str
    model: str
    temperature: Decimal
    max_tokens: int
    top_p: Decimal
    system_prompt: Optional[str]
    welcome_message: Optional[str]
    fallback_message: Optional[str]
    max_conversation_length: int
    enable_function_calling: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatbotListResponse(BaseModel):
    """List of chatbots."""
    items: List[ChatbotResponse]
    total: int
