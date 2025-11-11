"""
Chatbot domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from decimal import Decimal


@dataclass
class ChatbotEntity:
    """
    Chatbot entity representing an AI assistant configuration.

    Attributes:
        id: Unique chatbot identifier
        name: Chatbot name
        description: Chatbot description
        model: AI model identifier
        temperature: Model temperature (0.0-2.0)
        max_tokens: Maximum tokens for response
        top_p: Nucleus sampling parameter (0.0-1.0)
        system_prompt: System prompt for the AI model
        welcome_message: First message sent to users
        fallback_message: Response when API fails
        max_conversation_length: Messages to remember in context
        enable_function_calling: Allow AI to use available tools
        created_by: Admin who created this chatbot
        status: active, disabled, archived
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[int]
    name: str
    description: Optional[str]
    model: str
    temperature: Decimal = Decimal("0.7")
    max_tokens: int = 2048
    top_p: Decimal = Decimal("1.0")
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    fallback_message: Optional[str] = None
    max_conversation_length: int = 50
    enable_function_calling: bool = True
    created_by: int = 1
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate chatbot invariants."""
        if len(self.name) < 3:
            raise ValueError("Chatbot name must be at least 3 characters")
        if not Decimal("0.0") <= self.temperature <= Decimal("2.0"):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens < 1:
            raise ValueError("Max tokens must be positive")
        if not Decimal("0.0") <= self.top_p <= Decimal("1.0"):
            raise ValueError("Top p must be between 0.0 and 1.0")

    def deactivate(self) -> None:
        """Deactivate chatbot."""
        self.status = "disabled"
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate chatbot."""
        self.status = "active"
        self.updated_at = datetime.now()

    def archive(self) -> None:
        """Archive chatbot."""
        self.status = "archived"
        self.updated_at = datetime.now()

    @property
    def is_active(self) -> bool:
        """Check if chatbot is active (for backward compatibility)."""
        return self.status == "active"

    def update_config(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[Decimal] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[Decimal] = None
    ) -> None:
        """Update chatbot configuration."""
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if temperature is not None:
            if not Decimal("0.0") <= temperature <= Decimal("2.0"):
                raise ValueError("Temperature must be between 0.0 and 2.0")
            self.temperature = temperature
        if max_tokens is not None:
            if max_tokens < 1:
                raise ValueError("Max tokens must be positive")
            self.max_tokens = max_tokens
        if top_p is not None:
            if not Decimal("0.0") <= top_p <= Decimal("1.0"):
                raise ValueError("Top p must be between 0.0 and 1.0")
            self.top_p = top_p
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "system_prompt": self.system_prompt,
            "welcome_message": self.welcome_message,
            "fallback_message": self.fallback_message,
            "max_conversation_length": self.max_conversation_length,
            "enable_function_calling": self.enable_function_calling,
            "created_by": self.created_by,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# Backwards compatibility alias
Chatbot = ChatbotEntity
