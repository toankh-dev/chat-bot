"""
Feedback domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
from ..value_objects.uuid_vo import UUID


class FeedbackType(str, Enum):
    """Feedback type enumeration."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    STAR_RATING = "star_rating"
    COMMENT = "comment"


@dataclass
class FeedbackEntity:
    """
    Feedback entity for user ratings on AI responses.

    Attributes:
        id: Unique feedback identifier
        conversation_id: Conversation this feedback belongs to
        message_id: Specific message being rated
        user_id: User who provided feedback
        feedback_type: Type of feedback
        rating: Numerical rating (1-5 for star ratings)
        comment: Optional text comment
        metadata: Additional feedback metadata
        created_at: Feedback creation timestamp
    """

    id: UUID
    conversation_id: UUID
    message_id: UUID
    user_id: UUID
    feedback_type: FeedbackType
    rating: Optional[int] = None
    comment: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate feedback invariants."""
        if self.feedback_type == FeedbackType.STAR_RATING:
            if self.rating is None or not 1 <= self.rating <= 5:
                raise ValueError("Star rating must be between 1 and 5")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "message_id": str(self.message_id),
            "user_id": str(self.user_id),
            "feedback_type": self.feedback_type.value,
            "rating": self.rating,
            "comment": self.comment,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

# Backwards compatibility alias
Feedback = FeedbackEntity