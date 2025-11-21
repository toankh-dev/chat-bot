"""
Application service for agent orchestration.
"""

from typing import AsyncGenerator, Dict, Any
from infrastructure.ai_services.agents.orchestrator import AgentOrchestrator
from infrastructure.ai_services.agents.knowledge_base_agent import KnowledgeBaseAgent
from core.logger import logger
from core.config import settings


class AgentService:
    """
    Application service for multi-agent system.
    """

    def __init__(
        self,
        retriever,
        embedding_service,
        runtime_config: dict | None = None,
    ):
        self.runtime_config = runtime_config or {}

        # ------------------------------------------------------------
        # Initialize Knowledge Base Agent (NO RAGService)
        # ------------------------------------------------------------
        self.kb_agent = KnowledgeBaseAgent(
            embedding_service=embedding_service,
            retriever=retriever,
            runtime_config=self.runtime_config,
        )

        # ------------------------------------------------------------
        # Initialize Orchestrator
        # ------------------------------------------------------------
        self.orchestrator = AgentOrchestrator(
            kb_agent=self.kb_agent,
            runtime_config=self.runtime_config,
        )

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        try:
            return await self.orchestrator.execute(task)
        except Exception as e:
            logger.error(f"AgentService execution error: {e}", exc_info=True)
            return {
                "output": f"Error executing task: {str(e)}",
                "success": False,
                "error": str(e),
            }

    async def stream_events(self, task: str) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            async for event in self.orchestrator.stream_execution(task):
                yield self._transform_event(event)
        except Exception as e:
            logger.error(f"AgentService streaming error: {e}", exc_info=True)
            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "message": "Failed to stream agent events",
                },
            }

    def _transform_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return event

    def get_available_agents(self) -> Dict[str, str]:
        return {
            "knowledge_base": self.kb_agent.description,
        }

    def is_enabled(self) -> bool:
        return settings.ENABLE_AGENTS
