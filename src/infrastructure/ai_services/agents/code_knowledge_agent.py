"""
Code Knowledge specialized agent - expert in code analysis and software engineering.
"""

from typing import Any, Dict

from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from infrastructure.ai_services.tools.knowledge_base_tool import KnowledgeBaseSearchTool
from shared.interfaces.services.ai_services.vector_store_service import IVectorStore
from .base_agent import KASSBaseAgent
from core.logger import logger


class CodeKnowledgeAgent(KASSBaseAgent):
    """
    Specialized agent for code knowledge base retrieval and analysis.

    Expert in:
    - Code analysis and understanding (all programming languages)
    - Comprehensive enumeration of classes, methods, and components
    - Semantic search from vectorstore for code and documentation
    - Answering technical questions with precise code references
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
            name="Code Knowledge Specialist",
            description=(
                "Expert in code analysis, software engineering, and technical documentation. "
                "Uses semantic search over the vector database to provide comprehensive "
                "code insights, enumerate all components, and answer technical questions "
                "with precise file references."
            ),
            tools=tools,
            runtime_config=runtime_config,
        )

        logger.info("Code Knowledge Agent initialized with retriever-based code search")

    def _create_system_message(self) -> str:
        """
        Enhanced system message for code-focused knowledge base agent.

        Combines agent's default instructions with custom system prompt from database.
        """
        tools_description = "\n".join(
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        )

        # Get custom system prompt from runtime config (from database)
        custom_prompt = ""
        if self.runtime_config and "system_prompt" in self.runtime_config:
            custom_system_prompt = self.runtime_config.get("system_prompt")
            if custom_system_prompt:
                custom_prompt = f"\n## Custom Instructions\n\n{custom_system_prompt}\n"

        return f"""You are {self.name}, an expert AI assistant specialized in code analysis and software engineering.

            ## CRITICAL: Complete Enumeration

            When listing items (scenarios, use cases, methods, components):
            - **List EVERY item found** - no exceptions
            - **ONE class = ONE item, ONE function = ONE item**  
            - **DO NOT group, summarize, or consolidate**
            - **Include file paths and line numbers**

            ## Code Format

            - Use code blocks with language identifiers
            - Add file path as comment at top

            ## Citations

            - Cite references (Reference 1, 2, etc.)
            - If info missing, state clearly
            {custom_prompt}
            ## Available Tools

            {tools_description}

            Think step-by-step.
            """
