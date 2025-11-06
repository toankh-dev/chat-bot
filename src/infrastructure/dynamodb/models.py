"""
DynamoDB model for Conversation table.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Conversation:
    id: str
    user_id: str
    chatbot_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
