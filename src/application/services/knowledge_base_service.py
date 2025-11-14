"""
KnowledgeBase service layer.

Business logic for knowledge base management.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.knowledge_base import KnowledgeBaseEntity
from domain.entities.knowledge_base_source import KnowledgeBaseSourceEntity
from infrastructure.postgresql.repositories.knowledge_base_repository import KnowledgeBaseRepository
from infrastructure.postgresql.repositories.knowledge_base_source_repository import KnowledgeBaseSourceRepository


class KnowledgeBaseService:
    """
    Service for knowledge base operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize service with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.kb_repo = KnowledgeBaseRepository(session)
        self.source_repo = KnowledgeBaseSourceRepository(session)

    async def create_knowledge_base(
        self,
        chatbot_id: int,
        name: str,
        description: Optional[str] = None,
        vector_store_type: str = "chromadb",
        vector_store_config: Optional[dict] = None
    ) -> KnowledgeBaseEntity:
        """
        Create a new knowledge base.

        Args:
            chatbot_id: Chatbot ID
            name: Knowledge base name
            description: Optional description
            vector_store_type: Vector store type (default: chromadb)
            vector_store_config: Vector store configuration

        Returns:
            Created KnowledgeBase entity
        """
        entity = KnowledgeBaseEntity(
            id=None,
            chatbot_id=chatbot_id,
            name=name,
            description=description,
            vector_store_type=vector_store_type,
            vector_store_collection=f"kb_{chatbot_id}_{name.lower().replace(' ', '_')}",
            vector_store_config=vector_store_config,
            is_active=True
        )
        return await self.kb_repo.create(entity)

    async def get_or_create_kb_for_repository(
        self,
        chatbot_id: int,
        repo_name: str
    ) -> KnowledgeBaseEntity:
        """
        Get or create knowledge base for a repository.

        Args:
            chatbot_id: Chatbot ID
            repo_name: Repository name (extracted from URL)

        Returns:
            KnowledgeBase entity
        """
        kb_name = f"{repo_name} Knowledge Base"

        # Try to find existing KB
        existing_kb = await self.kb_repo.find_by_name_and_chatbot(kb_name, chatbot_id)
        if existing_kb:
            return existing_kb

        # Create new KB
        return await self.create_knowledge_base(
            chatbot_id=chatbot_id,
            name=kb_name,
            description=f"Knowledge base for {repo_name} repository"
        )

    async def add_repository_source(
        self,
        knowledge_base_id: int,
        repository_id: str,
        config: Optional[dict] = None,
        auto_sync: bool = False
    ) -> KnowledgeBaseSourceEntity:
        """
        Add a repository as a source to knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID
            repository_id: Repository ID (as string)
            config: Source configuration (include/exclude patterns)
            auto_sync: Enable auto-sync

        Returns:
            Created KnowledgeBaseSource entity
        """
        # Check if source already exists
        existing_source = await self.source_repo.find_by_source(
            kb_id=knowledge_base_id,
            source_type=KnowledgeBaseSourceEntity.SOURCE_TYPE_REPOSITORY,
            source_id=repository_id
        )

        if existing_source:
            # Update sync status to pending
            existing_source.sync_status = KnowledgeBaseSourceEntity.SYNC_STATUS_PENDING
            existing_source.auto_sync = auto_sync
            if config:
                existing_source.config = config
            return await self.source_repo.update(existing_source)

        # Create new source
        entity = KnowledgeBaseSourceEntity(
            id=None,
            knowledge_base_id=knowledge_base_id,
            source_type=KnowledgeBaseSourceEntity.SOURCE_TYPE_REPOSITORY,
            source_id=repository_id,
            config=config,
            auto_sync=auto_sync,
            sync_status=KnowledgeBaseSourceEntity.SYNC_STATUS_PENDING
        )
        return await self.source_repo.create(entity)

    async def update_source_sync_status(
        self,
        source_id: int,
        status: str,
        mark_completed: bool = False
    ) -> KnowledgeBaseSourceEntity:
        """
        Update sync status of a source.

        Args:
            source_id: Source ID
            status: New sync status
            mark_completed: If True, also update last_synced_at

        Returns:
            Updated KnowledgeBaseSource entity

        Raises:
            ValueError: If source not found
        """
        source = await self.source_repo.get_by_id(source_id)
        if not source:
            raise ValueError(f"Source with ID {source_id} not found")

        source.sync_status = status
        if mark_completed and status == KnowledgeBaseSourceEntity.SYNC_STATUS_COMPLETED:
            source.mark_completed()

        return await self.source_repo.update(source)

    async def get_knowledge_bases_for_chatbot(
        self,
        chatbot_id: int,
        active_only: bool = True
    ) -> List[KnowledgeBaseEntity]:
        """
        Get all knowledge bases for a chatbot.

        Args:
            chatbot_id: Chatbot ID
            active_only: Return only active KBs

        Returns:
            List of KnowledgeBase entities
        """
        if active_only:
            return await self.kb_repo.get_active_by_chatbot_id(chatbot_id)
        return await self.kb_repo.get_by_chatbot_id(chatbot_id)

    async def get_sources_for_kb(
        self,
        kb_id: int,
        source_type: Optional[str] = None
    ) -> List[KnowledgeBaseSourceEntity]:
        """
        Get all sources for a knowledge base.

        Args:
            kb_id: Knowledge base ID
            source_type: Filter by source type (optional)

        Returns:
            List of KnowledgeBaseSource entities
        """
        if source_type:
            return await self.source_repo.get_by_source_type(kb_id, source_type)
        return await self.source_repo.get_by_knowledge_base_id(kb_id)

    async def deactivate_knowledge_base(self, kb_id: int) -> KnowledgeBaseEntity:
        """
        Deactivate a knowledge base.

        Args:
            kb_id: Knowledge base ID

        Returns:
            Updated KnowledgeBase entity

        Raises:
            ValueError: If KB not found
        """
        kb = await self.kb_repo.get_by_id(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base with ID {kb_id} not found")

        kb.deactivate()
        return await self.kb_repo.update(kb)

    async def activate_knowledge_base(self, kb_id: int) -> KnowledgeBaseEntity:
        """
        Activate a knowledge base.

        Args:
            kb_id: Knowledge base ID

        Returns:
            Updated KnowledgeBase entity

        Raises:
            ValueError: If KB not found
        """
        kb = await self.kb_repo.get_by_id(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base with ID {kb_id} not found")

        kb.activate()
        return await self.kb_repo.update(kb)
