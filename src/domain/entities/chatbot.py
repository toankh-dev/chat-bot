"""
Chatbot domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from ..value_objects.uuid_vo import UUID


@dataclass
class ChatbotEntity:
    """
    Chatbot entity representing an AI assistant configuration.

    Attributes:
        id: Unique chatbot identifier
        workspace_id: Parent workspace ID
        name: Chatbot name
        description: Chatbot description
        system_prompt: System prompt for the AI model
        model_id: Bedrock model identifier
        temperature: Model temperature (0.0-1.0)
        max_tokens: Maximum tokens for response
        tools: List of tool IDs this chatbot can use
        is_active: Whether chatbot is active
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    workspace_id: UUID
    name: str
    description: str
    system_prompt: str
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate chatbot invariants."""
        if len(self.name) < 3:
            raise ValueError("Chatbot name must be at least 3 characters")
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        if self.max_tokens < 1:
            raise ValueError("Max tokens must be positive")

    def deactivate(self) -> None:
        """Deactivate chatbot."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate chatbot."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def update_config(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> None:
        """Update chatbot configuration."""
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if temperature is not None:
            if not 0.0 <= temperature <= 1.0:
                raise ValueError("Temperature must be between 0.0 and 1.0")
            self.temperature = temperature
        if max_tokens is not None:
            if max_tokens < 1:
                raise ValueError("Max tokens must be positive")
            self.max_tokens = max_tokens
        self.updated_at = datetime.utcnow()

    def add_tool(self, tool_id: str) -> None:
        """Add a tool to the chatbot."""
        if tool_id not in self.tools:
            self.tools.append(tool_id)
            self.updated_at = datetime.utcnow()

    def remove_tool(self, tool_id: str) -> None:
        """Remove a tool from the chatbot."""
        if tool_id in self.tools:
            self.tools.remove(tool_id)
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": self.tools,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# Backwards compatibility alias
Chatbot = ChatbotEntity
