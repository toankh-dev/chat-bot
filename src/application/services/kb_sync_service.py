"""
Knowledge Base Sync Service - Add processed documents to vector store.
"""

from typing import List, Dict, Any, Optional
from application.services.document_chunking_service import TextChunk
from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from shared.interfaces.services.ai_services.vector_store_service import IVectorStore
from shared.interfaces.repositories.document_repository import DocumentRepository
from domain.entities.document import DocumentEntity
import asyncio

from src.infrastructure.vector_store.factory import VectorStoreFactory


class KBSyncService:
    """Service for syncing document chunks to Knowledge Base (vector store)."""

    def __init__(
        self,
        embedding_service: IEmbeddingService,
        document_repository: DocumentRepository
    ):
        """
        Initialize KB Sync Service.

        Args:
            embedding_service: Service for creating embeddings
            vector_store: Vector store for storing embeddings
            document_repository: Repository for updating document status
        """
        self.embedding_service = embedding_service
        self.document_repository = document_repository

    async def add_document_to_kb(
        self,
        document: DocumentEntity,
        chunks: List[TextChunk],
        knowledge_base_id: str
    ) -> Dict[str, Any]:
        """
        Add document chunks to Knowledge Base.

        Args:
            document: Document entity
            chunks: List of text chunks
            knowledge_base_id: ID of the target knowledge base

        Returns:
            Dictionary with sync results

        Raises:
            ValueError: If chunks are empty or invalid
        """
        if not chunks:
            raise ValueError("Cannot add document to KB: no chunks provided")

        try:
            # Mark document as processing
            document.mark_as_processing(knowledge_base_id)
            await self.document_repository.update(document)

            # Extract texts from chunks
            chunk_texts = [chunk.text for chunk in chunks]

            # Create embeddings for all chunks
            print(f"Creating embeddings for {len(chunk_texts)} chunks...")
            embeddings = await self.embedding_service.create_embeddings(chunk_texts)

            if len(embeddings) != len(chunks):
                raise ValueError(f"Embedding count mismatch: {len(embeddings)} != {len(chunks)}")

            # Add vectors to vector store
            print(f"Adding {len(embeddings)} vectors to KB: {knowledge_base_id}")
            vector_ids = []

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                try:
                    # Prepare metadata for vector store
                    metadata = {
                        **chunk.metadata,
                        "text": chunk.text,
                        "source": document.filename,
                        "document_id": str(document.id),
                        "kb_id": knowledge_base_id,
                        "chunk_index": i
                    }

                    # Add vector to store
                    vector_id = self.vector_store.add_vector(embedding, metadata)
                    vector_ids.append(vector_id)

                except Exception as e:
                    print(f"Error adding chunk {i} to vector store: {e}")
                    continue

            if not vector_ids:
                raise ValueError("Failed to add any vectors to KB")

            # Mark document as processed
            document.mark_as_processed()
            await self.document_repository.update(document)

            return {
                "success": True,
                "document_id": str(document.id),
                "kb_id": knowledge_base_id,
                "total_chunks": len(chunks),
                "vectors_added": len(vector_ids),
                "vector_ids": vector_ids
            }

        except Exception as e:
            # Mark document as failed
            document.mark_as_failed(str(e))
            await self.document_repository.update(document)

            return {
                "success": False,
                "document_id": str(document.id),
                "error": str(e)
            }

    async def add_multiple_documents_to_kb(
        self,
        documents_data: List[Dict[str, Any]],
        knowledge_base_id: str
    ) -> List[Dict[str, Any]]:
        """
        Add multiple documents to KB in parallel.

        Args:
            documents_data: List of dicts with 'document' and 'chunks' keys
            knowledge_base_id: ID of the target knowledge base

        Returns:
            List of sync results for each document
        """
        tasks = []

        for doc_data in documents_data:
            document = doc_data["document"]
            chunks = doc_data["chunks"]

            task = self.add_document_to_kb(document, chunks, knowledge_base_id)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "success": False,
                    "document_id": str(documents_data[i]["document"].id),
                    "error": str(result)
                })
            else:
                formatted_results.append(result)

        return formatted_results

    async def remove_document_from_kb(
        self,
        document_id: str,
        knowledge_base_id: str
    ) -> Dict[str, Any]:
        """
        Remove document chunks from Knowledge Base.

        Note: This requires the vector store to support deletion by metadata filter.

        Args:
            document_id: ID of the document to remove
            knowledge_base_id: ID of the knowledge base

        Returns:
            Dictionary with removal results
        """
        try:
            # Query vectors by document_id metadata
            # Note: This assumes vector store supports querying by metadata
            # You may need to implement this based on your vector store

            print(f"Removing document {document_id} from KB {knowledge_base_id}")

            # Update document status
            document = await self.document_repository.find_by_id(document_id)
            if document:
                document.processing_status = None
                document.knowledge_base_id = None
                await self.document_repository.update(document)

            return {
                "success": True,
                "document_id": document_id,
                "kb_id": knowledge_base_id,
                "message": "Document removed from KB"
            }

        except Exception as e:
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e)
            }

    async def get_kb_statistics(self, knowledge_base_id: str) -> Dict[str, Any]:
        """
        Get statistics about a Knowledge Base.

        Args:
            knowledge_base_id: ID of the knowledge base

        Returns:
            Dictionary with KB statistics
        """
        try:
            # Query documents for this KB
            documents = await self.document_repository.find_by_knowledge_base(knowledge_base_id)

            processed_docs = [d for d in documents if d.processing_status == "completed"]
            failed_docs = [d for d in documents if d.processing_status == "error"]
            pending_docs = [d for d in documents if d.processing_status in ["pending", "syncing", None]]

            return {
                "kb_id": knowledge_base_id,
                "total_documents": len(documents),
                "processed_documents": len(processed_docs),
                "failed_documents": len(failed_docs),
                "pending_documents": len(pending_docs),
                "success_rate": len(processed_docs) / len(documents) if documents else 0.0
            }

        except Exception as e:
            return {
                "kb_id": knowledge_base_id,
                "error": str(e)
            }

    async def sync_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synchronously sync documents to vector store (for GitLab sync).

        Args:
            documents: List of documents with 'content' and 'metadata' keys

        Returns:
            Dictionary with sync results
        """
        try:
           
            # Extract texts and metadata
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]

            # Get knowledge_base_id from first document's metadata
            knowledge_base_id = metadatas[0].get("knowledge_base_id") if metadatas else "default"
            persist_directory = f"data/chromadb/{knowledge_base_id}"
            vector_store = VectorStoreFactory.create(config={"persist_directory": persist_directory})
    
            # Create embeddings asynchronously
            embeddings = await self.embedding_service.create_embeddings(texts)

            # Add vectors to vector store
            vector_ids = []
            for i, (text, metadata, embedding) in enumerate(zip(texts, metadatas, embeddings)):
                try:
                    # Add text to metadata
                    full_metadata = {
                        **metadata,
                        "text": text,
                        "chunk_index": i
                    }

                    # Add vector to store
                    vector_id = vector_store.add_vector(embedding, full_metadata)
                    vector_ids.append(vector_id)

                except Exception as e:
                    print(f"Error adding vector {i} to store: {e}")
                    continue

            return {
                "success": True,
                "kb_id": knowledge_base_id,
                "total_documents": len(documents),
                "vectors_added": len(vector_ids)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_kb_id_for_domain(self, domain: str, kb_config: Dict[str, str]) -> str:
        """
        Get Knowledge Base ID for a given domain.

        Args:
            domain: Domain name (e.g., 'healthcare', 'finance', 'general')
            kb_config: Configuration mapping domains to KB IDs

        Returns:
            Knowledge Base ID

        Raises:
            ValueError: If domain is not configured
        """
        kb_id = kb_config.get(domain.lower())

        if not kb_id:
            # Fallback to general KB if available
            kb_id = kb_config.get("general")

        if not kb_id:
            raise ValueError(f"No Knowledge Base configured for domain: {domain}")

        return kb_id

    async def reprocess_document(
        self,
        document_id: str,
        chunks: List[TextChunk],
        knowledge_base_id: str
    ) -> Dict[str, Any]:
        """
        Reprocess a document (remove old chunks and add new ones).

        Args:
            document_id: ID of the document
            chunks: New list of text chunks
            knowledge_base_id: ID of the knowledge base

        Returns:
            Dictionary with reprocessing results
        """
        # First remove old chunks
        removal_result = await self.remove_document_from_kb(document_id, knowledge_base_id)

        if not removal_result["success"]:
            return {
                "success": False,
                "document_id": document_id,
                "error": f"Failed to remove old chunks: {removal_result['error']}"
            }

        # Get document
        document = await self.document_repository.find_by_id(document_id)
        if not document:
            return {
                "success": False,
                "document_id": document_id,
                "error": "Document not found"
            }

        # Add new chunks
        return await self.add_document_to_kb(document, chunks, knowledge_base_id)
