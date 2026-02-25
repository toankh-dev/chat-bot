"""AI service schemas for LLM management and testing."""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class LLMProvidersResponse(BaseModel):
    """Response schema for available LLM providers."""
    providers: List[str] = Field(..., description="List of available provider names")
    models: Dict[str, List[str]] = Field(..., description="Available models for each provider")
    current_provider: str = Field(..., description="Currently configured provider")

    class Config:
        from_attributes = True


class AISystemInfoResponse(BaseModel):
    """Response schema for AI system information."""
    ai_system: str = Field(..., description="AI system description")
    current_llm_provider: str = Field(..., description="Current LLM provider name")
    model_info: Dict[str, Any] = Field(..., description="Model information")
    knowledge_base: str = Field(..., description="Knowledge base system")
    vector_store: str = Field(..., description="Vector store system")
    available_endpoints: List[str] = Field(..., description="List of available API endpoints")

    model_config = {"protected_namespaces": ()}


class LLMTestResponse(BaseModel):
    """Response schema for LLM testing."""
    response: str = Field(..., description="LLM generated response")
    provider: str = Field(..., description="LLM provider used")
    model_info: Dict[str, Any] = Field(..., description="Model information")
    prompt: str = Field(..., description="Original prompt sent to LLM")

    model_config = {"protected_namespaces": ()}
