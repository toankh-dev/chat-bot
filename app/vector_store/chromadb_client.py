"""
ChromaDB Client for vector storage and retrieval
"""

import logging
import os
from typing import List, Dict, Any, Optional
import httpx
import chromadb
from chromadb.config import Settings

# Import embedding providers
from embeddings import VoyageEmbeddingProvider

logger = logging.getLogger(__name__)


class VectorStoreClient:
    """
    Client for interacting with ChromaDB vector store
    """

    def __init__(
        self,
        host: str = "chromadb",
        port: int = 8000,
        collection_name: str = "chatbot_knowledge",
        embedding_provider: str = None,
        embedding_service_url: str = None,
        voyage_api_key: str = None,
        voyage_model: str = "voyage-2"
    ):
        """
        Initialize ChromaDB client

        Args:
            host: ChromaDB host
            port: ChromaDB port
            collection_name: Collection name
            embedding_provider: Embedding provider ('voyageai' or 'local')
            embedding_service_url: URL of embedding service (for local provider)
            voyage_api_key: VoyageAI API key (for voyageai provider)
            voyage_model: VoyageAI model name
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name

        # Determine embedding provider
        self.embedding_provider_type = embedding_provider or os.getenv("EMBEDDING_PROVIDER", "voyageai")

        # Initialize embedding provider
        self.embedding_provider = VoyageEmbeddingProvider(
            api_key=voyage_api_key or os.getenv("VOYAGE_API_KEY"),
            model=voyage_model or os.getenv("VOYAGE_MODEL", "voyage-2")
        )

        self.client = None
        self.collection = None

        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize ChromaDB connection"""
        try:
            self.logger.info(f"Connecting to ChromaDB at {self.host}:{self.port}")

            # Create client - use simple connection without tenant/database for compatibility
            try:
                # Try the simpler connection method first (works with most versions)
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port
                )
            except Exception as e:
                self.logger.warning(f"First connection attempt failed: {e}. Trying with settings...")
                # Fallback to explicit settings
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    settings=Settings(anonymized_telemetry=False)
                )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Knowledge base for chatbot"}
            )

            # Get collection info
            count = self.collection.count()
            self.logger.info(f"✅ Connected to collection '{self.collection_name}' ({count} documents)")

        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using configured embedding provider

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            return await self.embedding_provider.embed_texts(texts)
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            raise

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Add documents to the vector store

        Args:
            documents: List of documents with 'text' and 'metadata'
            batch_size: Batch size for processing

        Returns:
            Number of documents added
        """
        try:
            self.logger.info(f"Adding {len(documents)} documents to vector store...")

            added_count = 0

            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                # Extract texts and metadata
                texts = [doc["text"] for doc in batch]
                metadatas = [doc.get("metadata", {}) for doc in batch]
                ids = [f"doc_{i + j}" for j in range(len(batch))]

                # Generate embeddings
                embeddings = await self.embed_texts(texts)

                # Add to collection
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )

                added_count += len(batch)
                self.logger.info(f"Added batch {i // batch_size + 1}: {added_count}/{len(documents)}")

            self.logger.info(f"✅ Added {added_count} documents successfully")
            return added_count

        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")
            raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query: Search query
            limit: Maximum number of results
            filter: Metadata filter (optional)

        Returns:
            List of search results with documents and metadata
        """
        try:
            self.logger.info(f"Searching for: {query[:100]}...")

            # Generate query embedding
            query_embeddings = await self.embed_texts([query])

            # Search
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=limit,
                where=filter
            )

            # Format results
            formatted_results = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "document": {
                            "text": results['documents'][0][i]
                        },
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "score": 1.0 - results['distances'][0][i] if results['distances'] else 0.0,
                        "id": results['ids'][0][i] if results['ids'] else None
                    })

            self.logger.info(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            return []

    def search_sync(
        self,
        query: str,
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Synchronous version of search (for non-async tools)
        """
        try:
            # Generate query embedding (sync version)
            query_embeddings = self.embedding_provider.embed_texts_sync([query])

            # Search
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=limit,
                where=filter
            )

            # Format results
            formatted_results = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "document": {
                            "text": results['documents'][0][i]
                        },
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "score": 1.0 - results['distances'][0][i] if results['distances'] else 0.0,
                        "id": results['ids'][0][i] if results['ids'] else None
                    })

            return formatted_results

        except Exception as e:
            self.logger.error(f"Error in sync search: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if ChromaDB is healthy"""
        try:
            if self.client is None:
                return False

            # Try to get heartbeat
            heartbeat = self.client.heartbeat()
            return heartbeat > 0

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def close(self):
        """Close ChromaDB connection"""
        self.logger.info("Closing ChromaDB connection")
        # ChromaDB HttpClient doesn't need explicit close
        self.client = None
        self.collection = None
