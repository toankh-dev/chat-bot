"""
EmbeddingIndex domain entity.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class EmbeddingIndexEntity:
    id: Optional[int]
    document_id: int
    user_id: int
    chatbot_id: Optional[int]
    embedding_type: str
    vector_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Backwards compatibility alias
EmbeddingIndex = EmbeddingIndexEntity