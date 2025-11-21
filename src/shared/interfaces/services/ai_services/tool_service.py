"""
Tool service interface for agent tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class IToolService(ABC):
    """Interface for agent tools."""

    @abstractmethod
    def get_name(self) -> str:
        """
        Return tool name.

        Returns:
            str: Tool name used by agents
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Return tool description for LLM.

        Returns:
            str: Human-readable description explaining what the tool does
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute tool logic.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Dict[str, Any]: Tool execution result
        """
        pass
