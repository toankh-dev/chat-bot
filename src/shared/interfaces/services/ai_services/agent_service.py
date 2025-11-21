"""
Agent service interfaces for multi-agent system.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List


class IAgentService(ABC):
    """Interface for individual agent services."""

    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute agent task and return final result.

        Args:
            task: Task description for the agent
            **kwargs: Additional parameters

        Returns:
            Dict[str, Any]: Final execution result
        """
        pass

    @abstractmethod
    async def stream_events(self, task: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream agent execution events for real-time UI updates.

        Args:
            task: Task description for the agent
            **kwargs: Additional parameters

        Yields:
            Dict[str, Any]: Event dictionaries with type and data
        """
        pass


class IAgentOrchestrator(ABC):
    """Interface for agent orchestrator (supervisor pattern)."""

    @abstractmethod
    async def route_task(self, task: str) -> str:
        """
        Determine which agent should handle the task.

        Args:
            task: Task description

        Returns:
            str: Name of the agent to use
        """
        pass

    @abstractmethod
    async def execute_with_routing(
        self,
        task: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute task with automatic agent routing.

        Args:
            task: Task description
            **kwargs: Additional parameters

        Yields:
            Dict[str, Any]: Execution events from routed agent
        """
        pass
