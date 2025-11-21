"""
Base agent class using LangGraph ReAct pattern (fixed version for 2024+ SDKs).
"""

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict, Any, AsyncGenerator
from core.logger import logger
from core.config import settings


class KASSBaseAgent:
    """
    Base agent using LangGraph ReAct (Reasoning + Acting).
    """

    def __init__(
        self,
        name: str,
        description: str,
        tools: List,
        runtime_config: Dict[str, Any] = None,
    ):
        self.name = name
        self.description = description
        self.tools = tools

        self.llm_model_name = runtime_config.get("model_name")
        self.max_iterations = runtime_config.get("max_iterations") or 5
        self.temperature = runtime_config.get("temperature") or 0.7

        logger.info(f"Initializing agent: {name} with {len(tools)} tools")

        try:
            # Google GenAI LLM (new API)
            self.llm = ChatGoogleGenerativeAI(
                streaming=True,
                api_key=settings.GEMINI_API_KEY,
                model=self.llm_model_name,
                temperature=self.temperature,
            )

            # ReAct agent (LangGraph)
            self.executor = create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=self._create_system_message()
            )

            logger.info(f"Agent {name} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize agent {name}: {e}", exc_info=True)
            raise

    def _create_system_message(self) -> str:
        """
        System message for ReAct agent.
        """
        tools_description = "\n".join(f"- {tool.name}: {tool.description}" for tool in self.tools)

        return (
            f"You are {self.name}, a specialized AI agent.\n"
            f"Role: {self.description}\n\n"
            f"Available tools:\n{tools_description}\n\n"
            f"Use tools when needed. Think step-by-step."
        )

    # -------------------------------------------------------
    # EXECUTE
    # -------------------------------------------------------
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        try:
            logger.info(f"Agent {self.name} executing task: {task}")

            result = await self.executor.ainvoke({"messages": [("user", task)]}, **kwargs)

            messages = result.get("messages", [])
            final = messages[-1] if messages else None

            # GoogleGenAI chunk fix
            if hasattr(final, "content"):
                output = final.content
            elif isinstance(final, dict) and "content" in final:
                output = final["content"]
            else:
                output = str(final)

            return {
                "output": output,
                "intermediate_steps": result.get("intermediate_steps", []),
                "agent_name": self.name,
            }

        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            return {"output": f"Error: {e}", "error": True, "agent_name": self.name}

    # -------------------------------------------------------
    # STREAM EVENTS
    # -------------------------------------------------------
    async def stream_events(self, task: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            logger.info(f"Agent {self.name} streaming task: {task}")

            async for event in self.executor.astream_events(
                {"messages": [("user", task)]},
                version="v2",
            ):
                transformed = self._transform_event(event)
                if transformed:
                    yield transformed

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield {"type": "error", "data": {"error": str(e), "agent_name": self.name}}

    # -------------------------------------------------------
    # EVENT TRANSFORM
    # -------------------------------------------------------
    def _transform_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("event")

        # --- TOOL START
        if event_type == "on_tool_start":
            return {
                "type": "tool_start",
                "data": {
                    "tool": event.get("name"),
                    "args": event.get("data", {}).get("input"),
                    "agent_name": self.name,
                },
            }

        # --- TOOL END
        if event_type == "on_tool_end":
            return {
                "type": "tool_end",
                "data": {
                    "tool": event.get("name"),
                    "result": event.get("data", {}).get("output"),
                    "agent_name": self.name,
                },
            }

        # --- STREAMING TOKENS (Google GenAI format)
        if event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")

            if not chunk:
                return None

            # Google returns: chunk.parts = [{"text": "..."}]
            parts = getattr(chunk, "parts", None)
            if not parts:
                return None

            text = "".join(p.get("text", "") for p in parts if "text" in p)
            if text:
                return {"type": "token", "data": {"content": text, "agent_name": self.name}}

        # --- AGENT ACTION
        if event_type == "on_agent_action":
            return {
                "type": "agent_action",
                "data": {"action": str(event.get("data")), "agent_name": self.name},
            }

        # --- AGENT FINISH
        if event_type == "on_agent_finish":
            return {
                "type": "agent_finish",
                "data": {
                    "output": event.get("data", {}).get("output"),
                    "agent_name": self.name,
                },
            }

        return None
