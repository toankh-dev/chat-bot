"""
ChromaDB Vector Store Implementation

PURPOSE:
  Store and retrieve vector embeddings with metadata for semantic search.
  Each Knowledge Base has its own isolated collection.

USE CASES SUPPORTED:
  - UC-2.1: Multiple chatbots, same repo → different collections (isolation)
  - UC-2.2: Same chatbot, multiple KBs → different collections (isolation)
  - UC-4.3: KB deletion → delete entire collection
  - UC-1.3: Branch change → cleanup old branch vectors
  - UC-4.2: Source removal → cleanup source vectors

CRITICAL FIX (2025-11-16):
  Previously hardcoded collection="vectors" → all KBs shared 1 collection (BUG)
  Now uses dynamic collection_name parameter → each KB isolated (FIXED)
"""

from ..base import BaseVectorStore
import chromadb
from chromadb.config import Settings
from typing import List, Any, Dict, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class ChromaDBVectorStore(BaseVectorStore):
    """
    ChromaDB-based vector storage with collection-per-KB isolation.

    DESIGN DECISION:
      Collection name = kb_{knowledge_base_id} for perfect isolation.
      Each KB gets its own collection to prevent vector mixing.

    CRITICAL ARCHITECTURE:
      - Collection isolation prevents UC-2.2 collision (same chatbot, multiple KBs)
      - Metadata filtering enables UC-1.3 cleanup (branch change)
      - Collection deletion supports UC-4.3 (KB deletion)
    """

    def __init__(self, collection_name: str, persist_directory: str = ".chromadb"):
        """
        Initialize ChromaDB vector store.

        Args:
            collection_name: Unique collection name (format: kb_{kb_id})
            persist_directory: Directory to persist ChromaDB data

        USE CASES:
            - UC-2.1: Different chatbots get different collection_names
            - UC-2.2: Different KBs get different collection_names

        EDGE CASES:
            - Collection already exists → get_or_create reuses it
            - Invalid collection_name → ChromaDB validates and raises error
            - Persist directory doesn't exist → ChromaDB creates it

        CRITICAL FIX:
            OLD: self.collection = self.client.get_or_create_collection("vectors")
            NEW: self.collection = self.client.get_or_create_collection(collection_name)
        """
        try:
            self.collection_name = collection_name
            self.client = chromadb.Client(
                Settings(persist_directory=persist_directory)
            )

            # CRITICAL: Use dynamic collection name (not hardcoded "vectors")
            self.collection = self.client.get_or_create_collection(collection_name)

            logger.info(
                f"Initialized ChromaDB collection: {collection_name} "
                f"at {persist_directory}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_vector(self, vector: List[float], metadata: dict) -> str:
        """
        Add single vector with metadata to collection.

        Args:
            vector: Embedding vector (e.g., 768-dim for Gemini, 1536-dim for Titan)
            metadata: Metadata dict (MUST include: kb_source_id, branch, commit_sha)

        Returns:
            Vector ID in collection

        USE CASES:
            - UC-1.1: First time sync → add all file vectors
            - UC-1.2: Incremental sync → add changed file vectors
            - UC-1.3: Branch change → add new branch vectors (after cleanup)

        CRITICAL METADATA REQUIRED:
            - kb_source_id: Link to kb_source record (for cleanup UC-4.2)
            - branch: Branch name (for branch change cleanup UC-1.3)
            - commit_sha: Commit SHA (for audit trail)
            - file_path: Source file path

        EDGE CASES:
            - Duplicate vector_id → ChromaDB upserts (updates existing)
            - Missing required metadata → still added (validation should happen before)
            - Vector dimension mismatch → ChromaDB auto-detects on first add
        """
        vector_id = str(uuid.uuid4())
        self.collection.add(
            ids=[vector_id],
            embeddings=[vector],
            metadatas=[metadata]
        )
        return vector_id

    def query(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query vectors and return structured results matching interface."""
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k
        )
        
        formatted_results = []
        if results["ids"]:
            for i, vector_id in enumerate(results["ids"][0]):
                context = {
                    "context_id": vector_id,
                    "text": results["metadatas"][0][i].get("text", ""),
                    "source": results["metadatas"][0][i].get("source", ""),
                    "retrieval_score": 1 - results["distances"][0][i] if "distances" in results else 1.0,
                    "metadata": results["metadatas"][0][i]
                }
                formatted_results.append(self.format_context_response(context))
        
        return formatted_results

    def get_context_by_id(self, context_id: str) -> Dict[str, Any]:
        """Retrieve specific context by ID."""
        try:
            results = self.collection.get(ids=[context_id])
            if results["ids"]:
                metadata = results["metadatas"][0] if results["metadatas"] else {}
                return {
                    "context_id": context_id,
                    "text": metadata.get("text", ""),
                    "metadata": metadata
                }
        except Exception as e:
            print(f"Error retrieving context {context_id}: {e}")
        return {}

    def store_contexts(self, contexts: List[Dict[str, Any]], source_id: str = "") -> List[str]:
        """Store multiple contexts (implements BaseVectorStore interface)."""
        context_ids = []
        for context in contexts:
            # Add source_id to metadata
            context["source_id"] = source_id
            # Assuming vector is empty or generated elsewhere
            vector = context.get("vector", [0.0] * 768)  # Default embedding size
            context_id = self.add_vector(vector, context)
            context_ids.append(context_id)
        return context_ids

    def add_batch(
        self,
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]],
        vector_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add batch of vectors (more efficient than individual adds).

        Args:
            vectors: List of embedding vectors
            metadatas: List of metadata dicts (same length as vectors)
            vector_ids: Optional list of IDs

        Returns:
            List of vector IDs

        USE CASES:
            - UC-1.1: Batch add during initial sync
            - UC-6.1: Large repo → process in batches of 20 files

        EDGE CASES:
            - Empty batch → skip silently
            - Vectors/metadatas length mismatch → ChromaDB raises error
            - Partial failure → ChromaDB transaction (all-or-nothing)
        """
        try:
            if not vectors:
                logger.warning("Empty batch, skipping add")
                return []

            # Generate IDs if not provided
            if not vector_ids:
                vector_ids = [str(uuid.uuid4()) for _ in vectors]

            # Validate lengths match
            if len(vectors) != len(metadatas) or len(vectors) != len(vector_ids):
                raise ValueError(
                    f"Length mismatch: vectors={len(vectors)}, "
                    f"metadatas={len(metadatas)}, ids={len(vector_ids)}"
                )

            # Batch add
            self.collection.add(
                ids=vector_ids,
                embeddings=vectors,
                metadatas=metadatas
            )

            logger.info(f"Added batch of {len(vectors)} vectors")
            return vector_ids

        except Exception as e:
            logger.error(f"Error adding batch: {e}")
            raise

    def delete_by_metadata(self, filters: Dict[str, Any]) -> int:
        """
        Delete vectors matching metadata filters.

        Args:
            filters: Metadata filter dict (e.g., {"branch": "main", "kb_source_id": "15"})

        Returns:
            Number of vectors deleted

        USE CASES:
            - UC-1.3: Branch change → delete old branch vectors
            - UC-4.2: Source removal → delete all source vectors

        IMPLEMENTATION:
            1. Query to get IDs matching filters (using where clause)
            2. Delete by IDs

        EDGE CASES:
            - No matches → delete 0, return 0
            - Large result set → ChromaDB handles pagination internally
            - Invalid filter → ChromaDB raises error

        CRITICAL FOR:
            - Preventing vector pollution when branch changes
            - Cleanup when KB source removed

        EXAMPLE:
            # Delete all main branch vectors for a specific source
            deleted = store.delete_by_metadata({
                "kb_source_id": "15",
                "branch": "main"
            })
        """
        try:
            # Query to get IDs matching filters
            results = self.collection.get(where=filters)
            vector_ids = results.get("ids", [])

            if not vector_ids:
                logger.info(f"No vectors found matching filters {filters}")
                return 0

            # Delete by IDs
            self.collection.delete(ids=vector_ids)

            logger.info(
                f"Deleted {len(vector_ids)} vectors matching filters {filters}"
            )
            return len(vector_ids)

        except Exception as e:
            logger.error(f"Error deleting vectors by metadata: {e}")
            raise

    def delete_by_ids(self, vector_ids: List[str]) -> int:
        """
        Delete vectors by specific IDs.

        Args:
            vector_ids: List of vector IDs to delete

        Returns:
            Number of vectors deleted

        USE CASES:
            - UC-4.1: Content change → delete old file vectors (tracked in file_embeddings)

        EDGE CASES:
            - IDs don't exist → ChromaDB silently skips
            - Empty list → delete 0
        """
        try:
            if not vector_ids:
                return 0

            self.collection.delete(ids=vector_ids)

            logger.info(f"Deleted {len(vector_ids)} vectors by IDs")
            return len(vector_ids)

        except Exception as e:
            logger.error(f"Error deleting vectors by IDs: {e}")
            raise

    def delete_collection(self) -> bool:
        """
        Delete entire collection (all vectors).

        Returns:
            True if successful

        USE CASES:
            - UC-4.3: KB deletion → remove all vectors

        WARNING:
            This is destructive and irreversible!

        EDGE CASES:
            - Collection doesn't exist → ChromaDB raises error (catch and return True)
            - Collection in use → ChromaDB may block
        """
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection {self.collection_name}")
            return True

        except Exception as e:
            # Collection might not exist (already deleted)
            if "does not exist" in str(e).lower():
                logger.warning(
                    f"Collection {self.collection_name} already deleted or doesn't exist"
                )
                return True

            logger.error(f"Error deleting collection: {e}")
            raise

    def count_vectors(self) -> int:
        """
        Count total vectors in collection.

        Returns:
            Vector count

        USE CASES:
            - Monitoring, metrics
            - Verification after sync

        EDGE CASES:
            - Empty collection → returns 0
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error counting vectors: {e}")
            return 0
