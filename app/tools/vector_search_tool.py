"""
Vector Search Tool for searching the knowledge base
"""

import logging
from typing import Any, List, Dict

logger = logging.getLogger(__name__)


class VectorSearchTool:
    """
    Tool for searching the vector store / knowledge base
    """

    def __init__(self, vector_store: Any):
        """
        Initialize the vector search tool

        Args:
            vector_store: VectorStoreClient instance
        """
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)

    def run(self, query: str) -> str:
        """
        Search the knowledge base

        Args:
            query: Search query string

        Returns:
            Formatted search results as string
        """

        try:
            self.logger.info(f"Searching knowledge base for: {query[:100]}...")

            # Perform search
            results = self.vector_store.search_sync(query, limit=5)

            if not results:
                return "No relevant information found in the knowledge base."

            # Format results
            formatted_results = []
            formatted_results.append(f"Found {len(results)} relevant documents:\n")

            for i, result in enumerate(results, 1):
                doc = result.get("document", {})
                metadata = result.get("metadata", {})
                score = result.get("score", 0)

                source = metadata.get("source", "unknown")
                doc_type = metadata.get("type", "unknown")
                doc_id = metadata.get("id", "unknown")

                # Get text preview
                text = doc.get("text", "")
                preview = text[:200] + "..." if len(text) > 200 else text

                formatted_results.append(
                    f"\n{i}. [{source.upper()}] {doc_type} (ID: {doc_id})\n"
                    f"   Relevance: {score:.2f}\n"
                    f"   {preview}\n"
                )

            result_text = "".join(formatted_results)

            self.logger.info(f"Search completed: {len(results)} results")

            return result_text

        except Exception as e:
            self.logger.error(f"Error in vector search: {e}")
            return f"Error searching knowledge base: {str(e)}"

    async def arun(self, query: str) -> str:
        """
        Async version of run

        Args:
            query: Search query string

        Returns:
            Formatted search results
        """

        try:
            self.logger.info(f"Async searching for: {query[:100]}...")

            # Perform async search
            results = await self.vector_store.search(query, limit=5)

            if not results:
                return "No relevant information found in the knowledge base."

            # Format results (same as sync version)
            formatted_results = []
            formatted_results.append(f"Found {len(results)} relevant documents:\n")

            for i, result in enumerate(results, 1):
                doc = result.get("document", {})
                metadata = result.get("metadata", {})
                score = result.get("score", 0)

                source = metadata.get("source", "unknown")
                doc_type = metadata.get("type", "unknown")
                doc_id = metadata.get("id", "unknown")

                text = doc.get("text", "")
                preview = text[:200] + "..." if len(text) > 200 else text

                formatted_results.append(
                    f"\n{i}. [{source.upper()}] {doc_type} (ID: {doc_id})\n"
                    f"   Relevance: {score:.2f}\n"
                    f"   {preview}\n"
                )

            return "".join(formatted_results)

        except Exception as e:
            self.logger.error(f"Error in async vector search: {e}")
            return f"Error searching knowledge base: {str(e)}"
