"""Chatbot request/response schemas."""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class GroupInChatbot(BaseModel):
    """Group information in chatbot response."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class UserInChatbot(BaseModel):
    """User information in chatbot response."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str


class CreatorInfo(BaseModel):
    """Creator information in chatbot response."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str


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
    group_ids: Optional[List[int]] = Field(default=None, description="List of group IDs to assign chatbot to")
    user_ids: Optional[List[int]] = Field(default=None, description="List of user IDs to assign chatbot to")


class ChatbotUpdate(BaseModel):
    """Chatbot update request."""
    name: Optional[str] = None
    description: Optional[str] = None
    temperature: Optional[Decimal] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    top_p: Optional[Decimal] = Field(None, ge=0, le=1)
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    fallback_message: Optional[str] = None
    max_conversation_length: Optional[int] = Field(None, gt=0)
    enable_function_calling: Optional[bool] = None
    api_key: Optional[str] = Field(None, min_length=1, description="New API key (full key required, not masked)")
    api_base_url: Optional[str] = Field(None, description="Custom API base URL")
    status: Optional[str] = None
    group_ids: Optional[List[int]] = Field(default=None, description="List of group IDs to assign chatbot to (replaces existing)")
    user_ids: Optional[List[int]] = Field(default=None, description="List of user IDs to assign chatbot to (replaces existing)")

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate that API key is not a masked key."""
        if v is not None and '*' in v:
            raise ValueError("Cannot update with a masked API key. Please provide the full API key.")
        return v


class ChatbotResponse(BaseModel):
    """Chatbot response model."""
    model_config = ConfigDict(from_attributes=True)

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
    api_key_masked: Optional[str] = Field(default=None, description="Masked API key (shows first 4 and last 4 characters)")
    api_base_url: Optional[str] = Field(default=None, description="Custom API base URL")
    created_by: Optional[CreatorInfo] = Field(default=None, description="User who created this chatbot")
    status: str
    created_at: datetime
    updated_at: datetime
    assigned_groups: Optional[List[GroupInChatbot]] = Field(default=None, description="Groups that have access to this chatbot")
    assigned_users: Optional[List[UserInChatbot]] = Field(default=None, description="Users that have individual access to this chatbot")


class ChatbotListResponse(BaseModel):
    """List of chatbots."""
    items: List[ChatbotResponse]
    total: int
