"""
IngestionJob domain entity.
"""
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class IngestionJobEntity:
    id: Optional[int]
    provider: str
    status: str = "pending"
    source: Optional[str] = None
    user_id: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    details: Optional[Any] = None
    error_message: Optional[str] = None

# Backwards compatibility alias
IngestionJob = IngestionJobEntity