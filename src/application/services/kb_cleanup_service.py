"""
Knowledge Base Cleanup Service
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from src.shared.interfaces.repositories.knowledge_base_repository import (
    IKnowledgeBaseRepository,
)
from src.shared.interfaces.repositories.knowledge_base_source_repository import IKnowledgeBaseSourceRepository
from src.infrastructure.vector_store.factory import VectorStoreFactory

logger = logging.getLogger(__name__)


class KBCleanupService:
    """
    Service for cleaning up vector store data when KB sources change.
    """

    def __init__(
        self,
        kb_repo: IKnowledgeBaseRepository,
        kb_source_repo: IKnowledgeBaseSourceRepository,
        vector_store_factory: VectorStoreFactory,
    ):
        """
        Initialize KB Cleanup Service.

        Args:
            kb_repo: Knowledge Base repository interface
            kb_source_repo: KB Source repository interface
            vector_store_factory: Factory for creating vector stores
        """
        self.kb_repo = kb_repo
        self.kb_source_repo = kb_source_repo
        self.vector_store_factory = vector_store_factory

        logger.info("KBCleanupService initialized")

    def cleanup_branch_change(
        self, kb_id: int, source_id: str, old_branch: str
    ) -> Dict[str, Any]:
        """
        Cleanup vectors when KB source branch changes.
        """
        try:
            kb = self.kb_repo.get_by_id(kb_id)
            if not kb:
                return {
                    "success": False,
                    "kb_id": kb_id,
                    "error": f"Knowledge Base {kb_id} not found",
                    "deleted_vectors": 0,
                }

            vector_store = self.vector_store_factory.create(
                config={
                    "collection_name": kb.vector_store_collection,
                    "persist_directory": f".chromadb/{kb.vector_store_collection}",
                }
            )

            filters = {"kb_source_id": source_id, "branch": old_branch}

            deleted_count = vector_store.delete_by_metadata(filters)

            return {
                "success": True,
                "kb_id": kb_id,
                "source_id": source_id,
                "old_branch": old_branch,
                "deleted_vectors": deleted_count,
            }

        except Exception as e:
            logger.error(f"Error cleaning up branch change: {e}", exc_info=True)

            return {
                "success": False,
                "kb_id": kb_id,
                "source_id": source_id,
                "old_branch": old_branch,
                "error": str(e),
                "deleted_vectors": 0,
            }

    def cleanup_source_removal(self, kb_source_id: int) -> Dict[str, Any]:
        """
        Cleanup all vectors when KB source is removed.
        """
        try:
            source = self.kb_source_repo.get_by_id(kb_source_id)
            if not source:
                logger.warning(
                    f"KB Source {kb_source_id} not found (already deleted?)"
                )
                return {
                    "success": True,
                    "kb_source_id": kb_source_id,
                    "deleted_vectors": 0,
                    "note": "Source already deleted",
                }

            kb = self.kb_repo.get_by_id(source.knowledge_base_id)
            if not kb:
                return {
                    "success": True,
                    "kb_source_id": kb_source_id,
                    "kb_id": source.knowledge_base_id,
                    "deleted_vectors": 0,
                    "note": "KB already deleted",
                }

            vector_store = self.vector_store_factory.create(
                config={
                    "collection_name": kb.vector_store_collection,
                    "persist_directory": f".chromadb/{kb.vector_store_collection}",
                }
            )

            filters = {"kb_source_id": str(kb_source_id)}
            deleted_count = vector_store.delete_by_metadata(filters)

            return {
                "success": True,
                "kb_source_id": kb_source_id,
                "kb_id": kb.id,
                "deleted_vectors": deleted_count,
            }

        except Exception as e:
            logger.error(f"Error cleaning up source removal: {e}", exc_info=True)

            return {
                "success": False,
                "kb_source_id": kb_source_id,
                "error": str(e),
                "deleted_vectors": 0,
            }

    def cleanup_source_removal_sync(self, kb_source_id: int) -> Dict[str, Any]:
        """
        Synchronous version of cleanup_source_removal for SQLAlchemy event listeners.

        This method is called within database transactions (before_delete event).
        It must be synchronous and should not raise exceptions.
        """
        try:
            logger.info(f"[SYNC] Starting source removal cleanup: kb_source_id={kb_source_id}")

            # NOTE: Cannot use async repo methods in sync context
            # Need to query directly using session from event context
            # This is called BEFORE the delete, so source still exists

            from infrastructure.postgresql.models.knowledge_base_source_model import KnowledgeBaseSourceModel
            from infrastructure.postgresql.models.knowledge_base_model import KnowledgeBaseModel

            # Get session from repository (assumes sync repository)
            session = self.kb_source_repo.db_session

            # STEP 1: Get KB source
            source = session.query(KnowledgeBaseSourceModel).filter(
                KnowledgeBaseSourceModel.id == kb_source_id
            ).first()

            if not source:
                logger.warning(f"[SYNC] KB Source {kb_source_id} not found")
                return {
                    "success": True,
                    "kb_source_id": kb_source_id,
                    "deleted_vectors": 0,
                }

            # STEP 2: Get KB
            kb = session.query(KnowledgeBaseModel).filter(
                KnowledgeBaseModel.id == source.knowledge_base_id
            ).first()

            if not kb:
                logger.warning(f"[SYNC] KB {source.knowledge_base_id} not found")
                return {
                    "success": True,
                    "kb_source_id": kb_source_id,
                    "deleted_vectors": 0,
                }

            # STEP 3: Delete vectors
            vector_store = self.vector_store_factory.create(
                config={
                    "collection_name": kb.vector_store_collection,
                    "persist_directory": f".chromadb/{kb.vector_store_collection}",
                }
            )

            filters = {"kb_source_id": str(kb_source_id)}
            deleted_count = vector_store.delete_by_metadata(filters)

            logger.info(
                f"[SYNC] Source removal cleanup completed: "
                f"kb_source_id={kb_source_id}, deleted_vectors={deleted_count}"
            )

            return {
                "success": True,
                "kb_source_id": kb_source_id,
                "kb_id": kb.id,
                "deleted_vectors": deleted_count,
            }

        except Exception as e:
            logger.error(f"[SYNC] Error in source removal cleanup: {e}", exc_info=True)
            # Don't raise - allow KB source deletion to proceed
            return {
                "success": False,
                "kb_source_id": kb_source_id,
                "error": str(e),
                "deleted_vectors": 0,
            }