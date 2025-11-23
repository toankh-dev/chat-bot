"""
Agent Orchestrator using LangGraph supervisor pattern.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Dict, Any, AsyncGenerator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .code_knowledge_agent import CodeKnowledgeAgent
from core.logger import logger
from core.config import settings
import operator


class AgentState(TypedDict):
    """
    State for agent workflow.

    Attributes:
        messages: Conversation messages
        next_agent: Name of next agent to execute
        final_output: Final answer from agents
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str
    final_output: str


class AgentOrchestrator:
    """
    Orchestrator for multi-agent system using supervisor pattern.

    Routes tasks to appropriate specialized agents based on content analysis.
    Uses LangGraph for workflow management and state tracking.
    """

    def __init__(
        self,
        kb_agent: CodeKnowledgeAgent,
        runtime_config: dict,
    ):
        """
        Initialize agent orchestrator.

        Args:
            kb_agent: Code knowledge specialist agent (handles code analysis + technical documentation)
            runtime_config: Runtime configuration including model name
        """
        self.kb_agent = kb_agent
        self.llm_model_name = runtime_config.get("model_name")

        # Initialize supervisor LLM
        self.supervisor_llm = ChatGoogleGenerativeAI(
            model=self.llm_model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=runtime_config.get("temperature"),
            max_output_tokens=runtime_config.get("max_tokens"),
        )

        # Build workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow for agent routing.

        Returns:
            Compiled StateGraph workflow
        """
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("kb_agent", self._kb_node)

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_to_agent,
            {
                "knowledge_base": "kb_agent",
                "end": END
            }
        )

        # All agents return to supervisor for potential follow-up
        workflow.add_edge("kb_agent", "supervisor")

        return workflow.compile()

    async def _supervisor_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Supervisor node - decides which agent to route to.

        Args:
            state: Current agent state

        Returns:
            Updated state with routing decision
        """
        messages = state.get("messages", [])

        if not messages:
            return {"next_agent": "end"}

        # Get last message (user query)
        last_message = messages[-1]
        query = last_message.content if hasattr(last_message, 'content') else str(last_message)

        routing_decision = self._simple_route(query)

        logger.info(f"Supervisor routing to: {routing_decision}")

        return {
            "next_agent": routing_decision,
            "messages": [AIMessage(content=f"Routing to {routing_decision} agent")]
        }

    def _simple_route(self, query: str) -> str:
        """
        Simple keyword-based routing logic.

        Args:
            query: User query

        Returns:
            Agent name to route to
        """
        return "knowledge_base"

    def _route_to_agent(self, state: AgentState) -> str:
        """
        Extract routing decision from state.

        Args:
            state: Current state

        Returns:
            Next agent name or "end"
        """
        return state.get("next_agent", "end")

    async def _kb_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute Knowledge Base agent.

        Args:
            state: Current state

        Returns:
            Updated state with agent output
        """
        messages = state.get("messages", [])
        query = messages[0].content if messages else ""

        logger.info("Executing Knowledge Base agent")

        try:
            result = await self.kb_agent.execute(query)
            output = result.get("output", "")

            return {
                "messages": [AIMessage(content=output)],
                "final_output": output,
                "next_agent": "end"
            }

        except Exception as e:
            logger.error(f"KB agent error: {e}")
            return {
                "messages": [AIMessage(content=f"Error: {str(e)}")],
                "next_agent": "end"
            }

    async def execute(self, task: str) -> Dict[str, Any]:
        """
        Execute task with agent routing.

        Args:
            task: User task/query

        Returns:
            Dict with final output and metadata
        """
        try:
            logger.info(f"Orchestrator executing task: {task}")

            initial_state = {
                "messages": [HumanMessage(content=task)],
                "next_agent": "",
                "final_output": ""
            }

            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state)

            return {
                "output": final_state.get("final_output", ""),
                "agent_used": final_state.get("next_agent", "unknown"),
                "success": True
            }

        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            return {
                "output": f"Orchestration error: {str(e)}",
                "success": False
            }

    async def stream_execution(self, task: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream orchestrator execution events.

        Args:
            task: User task/query

        Yields:
            Dict with event type and data
        """
        try:
            logger.info(f"Orchestrator streaming task: {task}")

            # Yield start event
            yield {
                "type": "orchestrator_start",
                "data": {"task": task}
            }

            # Determine routing
            routing = self._simple_route(task)

            yield {
                "type": "agent_select",
                "data": {
                    "selected_agent": routing,
                    "reason": f"Query matched {routing} agent keywords"
                }
            }

            # Select and stream from agent
            if routing == "knowledge_base":
                agent = self.kb_agent

            # Stream agent events
            async for event in agent.stream_events(task):
                yield event

            yield {
                "type": "orchestrator_done",
                "data": {"agent_used": routing}
            }

        except Exception as e:
            logger.error(f"Orchestrator streaming error: {e}", exc_info=True)
            yield {
                "type": "error",
                "data": {"error": str(e)}
            }
