from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query or question")
    domain: str = Field(default="general", description="Knowledge domain")
    context_limit: int = Field(default=5, ge=1, le=20, description="Maximum contexts to retrieve")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Generated response")
    query: str = Field(..., description="Original query")
    contexts: List[Dict[str, Any]] = Field(..., description="Retrieved contexts")
    context_count: int = Field(..., description="Number of contexts used")

class SearchResponse(BaseModel):
    query: str = Field(..., description="Search query")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total results found")
    domain: str = Field(..., description="Search domain")

class ContextResponse(BaseModel):
    contexts: List[Dict[str, Any]] = Field(..., description="Retrieved contexts")
    query: str = Field(..., description="Original query")
    domain: str = Field(..., description="Query domain")