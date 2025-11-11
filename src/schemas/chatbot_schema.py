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
    model_id: int = Field(..., description="ID of the AI model to use")
    temperature: Decimal = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, gt=0)
    top_p: Decimal = Field(default=1.0, ge=0, le=1)
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    fallback_message: Optional[str] = None
    max_conversation_length: int = Field(default=50, gt=0)
    enable_function_calling: bool = True
    group_ids: Optional[List[int]] = Field(default=None, description="List of group IDs to assign chatbot to")
    user_ids: Optional[List[int]] = Field(default=None, description="List of user IDs to assign chatbot to")


class ChatbotUpdate(BaseModel):
    """Chatbot update request."""
    name: Optional[str] = None
    description: Optional[str] = None
    model_id: Optional[int] = Field(None, description="ID of the AI model to use")
    temperature: Optional[Decimal] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    top_p: Optional[Decimal] = Field(None, ge=0, le=1)
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    fallback_message: Optional[str] = None
    max_conversation_length: Optional[int] = Field(None, gt=0)
    enable_function_calling: Optional[bool] = None
    status: Optional[str] = None
    group_ids: Optional[List[int]] = Field(default=None, description="List of group IDs to assign chatbot to (replaces existing)")
    user_ids: Optional[List[int]] = Field(default=None, description="List of user IDs to assign chatbot to (replaces existing)")


class ChatbotResponse(BaseModel):
    """Chatbot response model."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    name: str
    description: Optional[str]
    model_id: int
    model_name: str = Field(..., description="Name of the AI model")
    temperature: Decimal
    max_tokens: int
    top_p: Decimal
    system_prompt: Optional[str]
    welcome_message: Optional[str]
    fallback_message: Optional[str]
    max_conversation_length: int
    enable_function_calling: bool
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
