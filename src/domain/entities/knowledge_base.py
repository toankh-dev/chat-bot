"""
KnowledgeBase domain entity.

Represents a knowledge base containing data sources for a chatbot.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KnowledgeBaseEntity:
    """
    Knowledge Base entity.

    A knowledge base aggregates multiple data sources (repositories, documents, APIs)
    for a specific chatbot to use for RAG (Retrieval Augmented Generation).
    """

    id: Optional[int]
    chatbot_id: int
    name: str
    description: Optional[str]
    vector_store_type: str  # chromadb, pinecone, opensearch, etc
    vector_store_collection: Optional[str]
    vector_store_config: Optional[dict]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate knowledge base data."""
        if not self.name or not self.name.strip():
            raise ValueError("Knowledge base name cannot be empty")

        if self.chatbot_id <= 0:
            raise ValueError("Chatbot ID must be a positive integer")

        if not self.vector_store_type:
            raise ValueError("Vector store type is required")

    @property
    def is_persisted(self) -> bool:
        """Check if KB has been saved to database."""
        return self.id is not None

    def deactivate(self) -> None:
        """Deactivate this knowledge base."""
        self.is_active = False

    def activate(self) -> None:
        """Activate this knowledge base."""
        self.is_active = True

    def __str__(self) -> str:
        """String representation."""
        return f"KnowledgeBase(id={self.id}, name='{self.name}', chatbot_id={self.chatbot_id})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"KnowledgeBase(id={self.id}, chatbot_id={self.chatbot_id}, "
            f"name='{self.name}', is_active={self.is_active})"
        )


# Backwards compatibility alias
KnowledgeBase = KnowledgeBaseEntity
