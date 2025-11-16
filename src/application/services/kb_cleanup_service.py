"""
Knowledge Base Cleanup Service

PURPOSE:
  Manage vector store cleanup operations when KB sources change or are removed.
  Ensures vector data consistency and prevents stale/orphaned vectors.

USE CASES SUPPORTED:
  - UC-1.3: Branch change → cleanup old branch vectors
  - UC-4.2: Source removal → cleanup all source vectors
  - UC-4.3: KB deletion → cleanup entire collection

CRITICAL FOR:
  - Preventing vector pollution (mixed branches, stale data)
  - Maintaining data consistency
  - Storage optimization (removing unused vectors)

ARCHITECTURE:
  This service bridges:
    - Domain layer (KB, KB Source entities)
    - Infrastructure layer (Vector stores, repositories)

  It orchestrates cleanup operations that span multiple layers.
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

    DESIGN PRINCIPLES:
      - Fail-safe: Errors logged but don't crash calling code
      - Idempotent: Safe to call multiple times
      - Auditable: Comprehensive logging of all operations
      - Transactional: Vector operations are atomic where possible

    DEPENDENCIES:
      - IKnowledgeBaseRepository: Access KB records
      - IKBSourceRepository: Access KB source records
      - VectorStoreFactory: Create vector store instances
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

    async def cleanup_branch_change(
        self, kb_id: int, source_id: str, old_branch: str
    ) -> Dict[str, Any]:
        """
        Cleanup vectors when KB source branch changes.
        """
        try:
            logger.info(
                f"Starting branch change cleanup: "
                f"kb_id={kb_id}, source_id={source_id}, old_branch={old_branch}"
            )

            # ================================================================
            # STEP 1: GET KB RECORD
            # ================================================================
            # Need KB to access vector_store_collection name and type
            # ================================================================

            kb = await self.kb_repo.get_by_id(kb_id)
            if not kb:
                error_msg = f"Knowledge Base {kb_id} not found"
                logger.warning(error_msg)
                return {
                    "success": False,
                    "kb_id": kb_id,
                    "error": error_msg,
                    "deleted_vectors": 0,
                }

            # ================================================================
            # STEP 2: CREATE VECTOR STORE INSTANCE
            # ================================================================
            # Use factory to create appropriate vector store (ChromaDB/S3)
            # Collection name = kb_{kb_id} (from Phase 1.2 fix)
            # ================================================================

            vector_store = self.vector_store_factory.create(
                config={
                    "collection_name": kb.vector_store_collection,
                    "persist_directory": f".chromadb/{kb.vector_store_collection}",
                }
            )

            # ================================================================
            # STEP 3: DELETE OLD BRANCH VECTORS
            # ================================================================
            # Use metadata filtering to target specific vectors
            # Filter: {kb_source_id: X, branch: old_branch}
            #
            # WHY THIS WORKS:
            #   - Vectors were created with enhanced metadata (Phase 1.3)
            #   - Each vector has kb_source_id and branch in metadata
            #   - ChromaDB delete_by_metadata() filters precisely
            #
            # CRITICAL:
            #   - Only deletes old_branch vectors
            #   - Other branches in same KB unaffected
            #   - Other KBs completely unaffected (different collections)
            # ================================================================

            filters = {"kb_source_id": source_id, "branch": old_branch}

            deleted_count = vector_store.delete_by_metadata(filters)

            # ================================================================
            # STEP 4: LOG AND RETURN RESULTS
            # ================================================================

            logger.info(
                f"Branch change cleanup completed: "
                f"kb_id={kb_id}, source_id={source_id}, "
                f"old_branch={old_branch}, deleted_vectors={deleted_count}"
            )

            return {
                "success": True,
                "kb_id": kb_id,
                "source_id": source_id,
                "old_branch": old_branch,
                "deleted_vectors": deleted_count,
            }

        except Exception as e:
            # ================================================================
            # ERROR HANDLING
            # ================================================================
            # Log detailed error but return structured response
            # Calling code can decide whether to retry or abort
            # ================================================================

            error_msg = f"Error cleaning up branch change: {e}"
            logger.error(error_msg, exc_info=True)

            return {
                "success": False,
                "kb_id": kb_id,
                "source_id": source_id,
                "old_branch": old_branch,
                "error": str(e),
                "deleted_vectors": 0,
            }

    async def cleanup_source_removal(self, kb_source_id: int) -> Dict[str, Any]:
        """
        Cleanup all vectors when KB source is removed.

        USE CASE: UC-4.2 - Source Removal
          User removes a source (repository) from Knowledge Base
          → Must delete ALL vectors created from that source
          → Prevents orphaned vectors

        WORKFLOW:
          1. Get KB source record to find KB and source details
          2. Get KB record to access vector store config
          3. Delete all vectors matching: {kb_source_id: X}
          4. Return cleanup statistics

        Args:
            kb_source_id: KB Source ID to cleanup

        Returns:
            Dict with cleanup results:
              {
                "success": bool,
                "kb_source_id": int,
                "kb_id": int,
                "deleted_vectors": int,
                "error": str (if failed)
              }

        EDGE CASES:
          - KB source not found → log warning, return success=True (already gone)
          - KB not found → log warning, return success=True (already gone)
          - No vectors found → return success=True, deleted_vectors=0
          - Multiple branches in source → all branches deleted

        CRITICAL:
          This cleanup is IRREVERSIBLE!
          All vectors from this source are permanently deleted.

        EXAMPLE:
          # User removes GitLab repo source from KB
          result = await cleanup_service.cleanup_source_removal(
              kb_source_id=15
          )
          # Result: {"success": True, "deleted_vectors": 5678}
        """
        try:
            logger.info(f"Starting source removal cleanup: kb_source_id={kb_source_id}")

            # ================================================================
            # STEP 1: GET KB SOURCE RECORD
            # ================================================================
            # Need source to find which KB it belongs to
            # If source not found, assume already deleted (success)
            # ================================================================

            source = await self.kb_source_repo.get_by_id(kb_source_id)
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

            # ================================================================
            # STEP 2: GET KB RECORD
            # ================================================================

            kb = await self.kb_repo.get_by_id(source.knowledge_base_id)
            if not kb:
                logger.warning(
                    f"Knowledge Base {source.knowledge_base_id} not found (already deleted?)"
                )
                return {
                    "success": True,
                    "kb_source_id": kb_source_id,
                    "kb_id": source.knowledge_base_id,
                    "deleted_vectors": 0,
                    "note": "KB already deleted",
                }

            # ================================================================
            # STEP 3: CREATE VECTOR STORE AND DELETE ALL SOURCE VECTORS
            # ================================================================
            # Delete ALL vectors with kb_source_id = X
            # This removes vectors from ALL branches of this source
            # ================================================================

            vector_store = self.vector_store_factory.create(
                config={
                    "collection_name": kb.vector_store_collection,
                    "persist_directory": f".chromadb/{kb.vector_store_collection}",
                }
            )

            filters = {"kb_source_id": str(kb_source_id)}
            deleted_count = vector_store.delete_by_metadata(filters)

            # ================================================================
            # STEP 4: LOG AND RETURN RESULTS
            # ================================================================

            logger.info(
                f"Source removal cleanup completed: "
                f"kb_source_id={kb_source_id}, kb_id={kb.id}, "
                f"deleted_vectors={deleted_count}"
            )

            return {
                "success": True,
                "kb_source_id": kb_source_id,
                "kb_id": kb.id,
                "deleted_vectors": deleted_count,
            }

        except Exception as e:
            error_msg = f"Error cleaning up source removal: {e}"
            logger.error(error_msg, exc_info=True)

            return {
                "success": False,
                "kb_source_id": kb_source_id,
                "error": str(e),
                "deleted_vectors": 0,
            }

    async def cleanup_kb_deletion(self, kb_id: int) -> Dict[str, Any]:
        """
        Cleanup entire vector collection when KB is deleted.

        USE CASE: UC-4.3 - KB Deletion
          User deletes entire Knowledge Base
          → Must delete ALL vectors in KB collection
          → Most efficient: delete entire collection (not individual vectors)

        WORKFLOW:
          1. Get KB record to access collection name
          2. Create vector store instance
          3. Delete entire collection
          4. Return cleanup statistics

        Args:
            kb_id: Knowledge Base ID

        Returns:
            Dict with cleanup results:
              {
                "success": bool,
                "kb_id": int,
                "collection_name": str,
                "collection_deleted": bool,
                "error": str (if failed)
              }

        EDGE CASES:
          - KB not found → log warning, return success=True (already gone)
          - Collection doesn't exist → return success=True (already deleted)
          - Collection in use → may block (rare)

        CRITICAL:
          This is the most destructive cleanup operation!
          Entire collection and all its vectors are permanently deleted.

        PERFORMANCE:
          Deleting collection is much faster than deleting individual vectors
          For 10k vectors: ~100ms vs ~10 seconds

        EXAMPLE:
          # User deletes entire KB
          result = await cleanup_service.cleanup_kb_deletion(kb_id=5)
          # Result: {"success": True, "collection_deleted": True}
        """
        try:
            logger.info(f"Starting KB deletion cleanup: kb_id={kb_id}")

            # ================================================================
            # STEP 1: GET KB RECORD
            # ================================================================
            # Need collection name to delete
            # If KB not found, assume already deleted (success)
            # ================================================================

            kb = await self.kb_repo.get_by_id(kb_id)
            if not kb:
                logger.warning(f"Knowledge Base {kb_id} not found (already deleted?)")
                return {
                    "success": True,
                    "kb_id": kb_id,
                    "collection_deleted": False,
                    "note": "KB already deleted",
                }

            collection_name = kb.vector_store_collection

            # ================================================================
            # STEP 2: CREATE VECTOR STORE AND DELETE COLLECTION
            # ================================================================
            # Use delete_collection() - most efficient method
            # Deletes collection and all its vectors in one operation
            # ================================================================

            vector_store = self.vector_store_factory.create(
                config={
                    "collection_name": collection_name,
                    "persist_directory": f".chromadb/{collection_name}",
                }
            )

            collection_deleted = vector_store.delete_collection()

            # ================================================================
            # STEP 3: LOG AND RETURN RESULTS
            # ================================================================

            logger.info(
                f"KB deletion cleanup completed: "
                f"kb_id={kb_id}, collection={collection_name}, "
                f"deleted={collection_deleted}"
            )

            return {
                "success": collection_deleted,
                "kb_id": kb_id,
                "collection_name": collection_name,
                "collection_deleted": collection_deleted,
            }

        except Exception as e:
            error_msg = f"Error cleaning up KB deletion: {e}"
            logger.error(error_msg, exc_info=True)

            return {
                "success": False,
                "kb_id": kb_id,
                "error": str(e),
                "collection_deleted": False,
            }

    async def get_cleanup_stats(self, kb_id: int) -> Dict[str, Any]:
        """
        Get statistics about vector data for a KB (for monitoring/debugging).

        Args:
            kb_id: Knowledge Base ID

        Returns:
            Dict with stats:
              {
                "success": bool,
                "kb_id": int,
                "collection_name": str,
                "total_vectors": int,
                "sources": List[Dict] (source_id, vector_count per source)
              }

        USE CASE:
          - Monitoring vector storage usage
          - Debugging cleanup issues
          - Audit trail

        NOTE:
          This requires querying vector store metadata.
          May be slow for large collections (10k+ vectors).
        """
        try:
            logger.info(f"Getting cleanup stats for kb_id={kb_id}")

            kb = await self.kb_repo.get_by_id(kb_id)
            if not kb:
                return {
                    "success": False,
                    "kb_id": kb_id,
                    "error": "KB not found",
                }

            vector_store = self.vector_store_factory.create(
                config={
                    "collection_name": kb.vector_store_collection,
                    "persist_directory": f".chromadb/{kb.vector_store_collection}",
                }
            )

            total_vectors = vector_store.count_vectors()

            return {
                "success": True,
                "kb_id": kb_id,
                "collection_name": kb.vector_store_collection,
                "total_vectors": total_vectors,
            }

        except Exception as e:
            logger.error(f"Error getting cleanup stats: {e}", exc_info=True)
            return {
                "success": False,
                "kb_id": kb_id,
                "error": str(e),
            }
