"""
Knowledge Base search tool - uses retriever directly (no RAGService).
"""

from typing import Any, Dict, Tuple
from shared.interfaces.services.ai_services.vector_store_service import IVectorStore
from .base_tool import KASSBaseTool
from pydantic import Field
from core.logger import logger


class QueryComplexity:
    """Query complexity levels for adaptive retrieval."""
    NARROW = "narrow"
    MEDIUM = "medium"
    BROAD = "broad"
    VERY_BROAD = "very_broad"


class KnowledgeBaseSearchTool(KASSBaseTool):
    """
    Tool for searching internal knowledge base via retriever.

    This tool does semantic search on the vectorstore using retriever
    provided by the application layer.
    """

    name: str = "search_knowledge_base"
    description: str = """
    Search internal knowledge base for relevant information.

    Use this tool when the user asks questions that require company/domain knowledge
    or internal documentation.

    Required Args:
        query (str): Search query or question
    """

    embedding_service: Any = Field(exclude=True)
    retriever: IVectorStore = Field(exclude=True)
    class Config:
        arbitrary_types_allowed = True

    async def _arun(
        self,
        query: str,
        top_k: int = 5,
    ) -> str:
        """
        Perform semantic search using the retriever.

        Args:
            query: Search query
            top_k: Number of documents to return

        Returns:
            str: Formatted result text
        """
        try:
            # Embed the query message with query-optimized task type
            query_embedding = await self.embedding_service.create_single_embedding(
                query,
                task_type="retrieval_query"
            )

            # Call retriever
            contexts = self.retriever.query(query_embedding, top_k=top_k)

            result = []

            for item in contexts:
                formatted = {
                    "id": item.get("context_id"),
                    "text": item.get("text", ""),
                    "score": item.get("retrieval_score"),
                    "source": item.get("source"),
                    "metadata": item.get("metadata", {}),
                }
                result.append(formatted)

            return result

        except Exception as e:
            error_msg = f"Knowledge base search error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
