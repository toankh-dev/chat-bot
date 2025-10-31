"""
ChromaDB Client for vector storage and retrieval
"""

import logging
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

# Import embedding providers
from embeddings import VoyageEmbeddingProvider, GeminiEmbeddingProvider

logger = logging.getLogger(__name__)


class VectorStoreClient:
    """
    Client for interacting with ChromaDB vector store
    """
    _EMBEDDING_PROVIDER_MAP = {
        "gemini": {
            "cls": GeminiEmbeddingProvider,
            "init_kwargs": {
                "api_key": os.getenv("  "),
                "model": os.getenv("EMBED_MODEL", "gemini-embedding-001"),
            },
        },
        'voyage': {
            "cls": VoyageEmbeddingProvider,
            "init_kwargs": {
                "api_key": os.getenv("EMBED_API_KEY"),
                "model": os.getenv("EMBED_MODEL", "voyage-2"),
            },
        },
    }

    def __init__(
        self,
        host: str = "chromadb",
        port: int = 8000,
        collection_name: str = "chatbot_knowledge",
        embedding_provider: str = None,
    ):
        """
        Initialize ChromaDB client

        Args:
            host: ChromaDB host
            port: ChromaDB port
            collection_name: Collection name
            embedding_provider: Embedding provider ('gemini' or 'voyage')
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name

        # Determine embedding provider
        provider_name = embedding_provider or os.getenv("EMBEDDING_PROVIDER", "gemini")
        provider_info = self._EMBEDDING_PROVIDER_MAP.get(provider_name)
        
        print("provider_info:: ", provider_info)
        
        if provider_info is None:
            raise ValueError(f"Unsupported embedding provider: {provider_name}")

        # Initialize embedding provider
        provider_cls = provider_info["cls"]
        self.embedding_provider = provider_cls(**provider_info.get("init_kwargs", {}))

        self.client = None

        self.logger = logging.getLogger(__name__)

    def _get_collection(self):
        """
        Get collection dynamically (not cached) to handle collection recreation

        Returns:
            ChromaDB collection object
        """
        if self.client is None:
            raise RuntimeError("ChromaDB client not initialized. Call initialize() first.")

        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Knowledge base for chatbot"}
        )

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

            # Get or create collection (don't cache it)
            collection = self._get_collection()

            # Get collection info
            count = collection.count()
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
            collection = self._get_collection()

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
                collection.add(
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

            # Get collection dynamically
            collection = self._get_collection()

            # Generate query embedding
            query_embeddings = await self.embed_texts([query])

            # Search
            results = collection.query(
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
            # Get collection dynamically
            collection = self._get_collection()

            # Generate query embedding (sync version)
            query_embeddings = self.embedding_provider.embed_texts_sync([query])

            # Search
            results = collection.query(
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
