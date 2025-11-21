"""
Base tool class for KASS agents - wraps existing services as LangChain tools.
"""

from langchain_core.tools import BaseTool


class KASSBaseTool(BaseTool):
    """
    Base tool for KASS agents - wrap existing services.

    Inherits from LangChain BaseTool to integrate with LangChain agents.
    Provides async execution interface for all tools.
    """

    def _run(self, **kwargs) -> str:
        """
        Sync version - not used in KASS system.

        All tools use async execution via _arun method.

        """
        raise NotImplementedError("KASS tools use async execution only. Use _arun instead.")

    async def _arun(self, **kwargs) -> str:
        """
        Async execution - must be implemented in subclasses.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            str: Tool execution result as string for LLM

        Raises:
            NotImplementedError: If not implemented in subclass
        """
        raise NotImplementedError("Subclasses must implement _arun method")
