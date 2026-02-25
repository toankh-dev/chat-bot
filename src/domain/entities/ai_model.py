"""
AI Model domain entity.

Represents an AI model that can be used by chatbots.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional


@dataclass
class AiModelEntity:
    """
    AI Model entity representing an AI model configuration.

    Attributes:
        id: Unique model identifier (integer)
        name: Model name (e.g., "gpt-4o", "claude-3-5-sonnet", "gemini-pro")
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate model data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Model name cannot be empty")

        if self.name != self.name.strip():
            self.name = self.name.strip()

    @property
    def is_persisted(self) -> bool:
        """Check if the model has been persisted to database."""
        return self.id is not None

    def update_name(self, name: str):
        """
        Update model name.

        Args:
            name: New model name
        """
        if not name.strip():
            raise ValueError("Model name cannot be empty")
        self.name = name.strip()
        self.updated_at = datetime.now(UTC)

    def __str__(self) -> str:
        """String representation of the model."""
        return f"AiModel(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return (
            f"AiModel(id={self.id}, name='{self.name}', "
            f"created_at={self.created_at}, updated_at={self.updated_at})"
        )

