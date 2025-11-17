"""
KnowledgeBase Sync Repository - Database operations for knowledge base management (SYNC).
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from infrastructure.postgresql.models.knowledge_base_model import KnowledgeBaseModel
from shared.interfaces.repositories.knowledge_base_repository import IKnowledgeBaseRepository


class KnowledgeBaseRepository(IKnowledgeBaseRepository):
    """Repository for managing knowledge base records (SYNC version for GitLab)."""

    def __init__(self, db_session: Session):
        """
        Initialize knowledge base repository.

        Args:
            db_session: SQLAlchemy database session (sync)
        """
        self.db_session = db_session

    def get_by_name_and_chatbot(
        self, kb_name: str, chatbot_id: int
    ) -> Optional[KnowledgeBaseModel]:
        """
        Get knowledge base by name and chatbot ID.

        Args:
            kb_name: Knowledge base name
            chatbot_id: Chatbot ID

        Returns:
            KnowledgeBase model or None
        """
        return self.db_session.query(KnowledgeBaseModel).filter(
            and_(
                KnowledgeBaseModel.name == kb_name,
                KnowledgeBaseModel.chatbot_id == chatbot_id
            )
        ).first()

    def create(self, kb_data: dict) -> KnowledgeBaseModel:
        """
        Create a new knowledge base.

        Args:
            kb_data: Dictionary with KB fields (chatbot_id, name, description, etc.)

        Returns:
            Created KnowledgeBase model
        """
        kb = KnowledgeBaseModel(**kb_data)
        self.db_session.add(kb)
        self.db_session.flush()
        self.db_session.refresh(kb)
        return kb

    def get_by_id(self, kb_id: int) -> Optional[KnowledgeBaseModel]:
        """
        Get knowledge base by ID.

        Args:
            kb_id: Knowledge base ID

        Returns:
            KnowledgeBase model or None
        """
        return self.db_session.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == kb_id
        ).first()

    def get_or_create(
        self,
        knowledge_base_id: Optional[int] = None,
        defaults: dict = None
    ) -> tuple[KnowledgeBaseModel, bool]:
        """
        Get existing knowledge base or create new one.

        Args:
            knowledge_base_id: knowledge base ID
            defaults: Default values if creating new knowledge base

        Returns:
            Tuple of (knowledge base, created) where created is True if new
        """
        knowledge_base = self.db_session.query(KnowledgeBaseModel).filter(
            and_(
                KnowledgeBaseModel.id == knowledge_base_id,
            )
        ).first()

        if knowledge_base:
            return knowledge_base, False

        # Create new knowledge base
        repo_data = defaults or {}
        knowledge_base = KnowledgeBaseModel(
            **repo_data
        )
        return self.create(knowledge_base), True