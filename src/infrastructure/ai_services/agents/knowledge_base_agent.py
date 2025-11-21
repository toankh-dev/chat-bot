"""
Knowledge Base specialized agent - expert in searching internal knowledge.
"""

from typing import Any, Dict

from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from infrastructure.ai_services.tools.knowledge_base_tool import KnowledgeBaseSearchTool
from shared.interfaces.services.ai_services.vector_store_service import IVectorStore
from .base_agent import KASSBaseAgent
from core.logger import logger


class KnowledgeBaseAgent(KASSBaseAgent):
    """
    Specialized agent for knowledge base retrieval operations.

    Expert in:
    - Semantic search from vectorstore retriever
    - Retrieving relevant documents
    - Answering questions from indexed content
    - Providing internal/company knowledge
    """

    def __init__(
        self,
        retriever: IVectorStore,
        embedding_service,
        runtime_config: Dict[str, Any] = None,
    ):
        """
        Initialize Knowledge Base agent.

        Args:
            retriever: Vectorstore retriever instance (NOT RAGService)
            runtime_config: Optional runtime configuration dictionary
        """

        # Create retrieval tool (decoupled from RAGService)
        tools = [
            KnowledgeBaseSearchTool(retriever=retriever, embedding_service=embedding_service)
        ]

        super().__init__(
            name="Knowledge Base Specialist",
            description=(
                "Expert in searching internal knowledge base and company documentation. "
                "Uses semantic search over the vector database to provide accurate "
                "and context-aware answers from indexed materials."
            ),
            tools=tools,
            runtime_config=runtime_config,
        )

        logger.info("Knowledge Base Agent initialized with retriever-based KB search")
