"""
Orchestrator Agent using LangChain
Coordinates multiple specialized agents to handle user requests
"""

import logging
import os
from typing import Any, Optional, List, Dict
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from tools.report_tool import ReportTool
from tools.summarize_tool import SummarizeTool
from tools.code_review_tool import CodeReviewTool
from tools.vector_search_tool import VectorSearchTool
from llm.groq_llm import GroqLLM

logger = logging.getLogger(__name__)


# Orchestrator prompt template
ORCHESTRATOR_PROMPT = """You are an intelligent AI assistant that helps users with project management and information tasks.

You have access to the following tools:

{tools}

Tool Names: {tool_names}

**Your Responsibilities:**

1. **Analyze** user questions to understand their intent
2. **Respond appropriately:**
   - For simple greetings/casual conversation: Answer directly without using tools
   - For information queries: Use VectorSearch to find information
   - For actions: Use appropriate tool (Report, Summarize, or CodeReview)
   - For complex tasks: Coordinate multiple tools sequentially
3. **Synthesize** results into a clear, helpful response

**Decision Framework:**

- For greetings ("hello", "hi", "how are you"): Respond directly with a friendly greeting
- If user asks "What/Where/Show/Find/List" about project data → Use VectorSearch tool
- If user says "Create/Update/Post/Send" → Use Report tool
- If user wants "Summarize/Analyze" → Use Summarize tool
- If user wants code review → Use CodeReview tool

**Guidelines:**

- Be friendly and conversational for simple messages
- Use tools only when necessary to fetch data or perform actions
- Always provide clear, concise answers
- Handle errors gracefully

**Format:**

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

**IMPORTANT:** For simple greetings or casual conversation, skip directly to "Final Answer:" without using any tools.

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""


def create_orchestrator_agent(
    vector_store: Any,
    verbose: bool = True
) -> AgentExecutor:
    """
    Create the orchestrator agent with all tools

    Args:
        vector_store: Vector store client instance
        verbose: Whether to print agent reasoning

    Returns:
        OrchestratorAgent instance
    """

    logger.info("Creating orchestrator agent...")

    # Initialize LLM based on provider
    llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if llm_provider == "groq":
        logger.info("Using Groq API (Fast & Free)")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

        llm = GroqLLM(
            api_key=api_key,
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            max_tokens=int(os.getenv("GROQ_MAX_TOKENS", "1024")),
            temperature=float(os.getenv("GROQ_TEMPERATURE", "0.7"))
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}. Currently only 'groq' is supported.")

    # Initialize tools
    logger.info("Initializing tools...")

    vector_search_tool = VectorSearchTool(vector_store=vector_store)
    report_tool = ReportTool()
    summarize_tool = SummarizeTool()
    code_review_tool = CodeReviewTool()

    # Define tools for LangChain
    tools = [
        Tool(
            name="VectorSearch",
            func=vector_search_tool.run,
            description="""
            Useful for searching the knowledge base to answer questions about:
            - GitLab issues, merge requests, and code
            - Slack discussions and messages
            - Backlog tickets and wikis
            - Historical project data

            Input should be a search query string.
            Returns relevant documents from the knowledge base.

            Example: "open bugs in project X" or "discussions about feature Y"
            """
        ),
        Tool(
            name="Report",
            func=report_tool.run,
            description="""
            Useful for creating reports and managing tickets:
            - Create Backlog tickets/issues
            - Update existing Backlog tickets
            - Post messages to Slack channels
            - Send notifications

            Input should be a JSON string with action and parameters:
            {
                "action": "create_backlog_ticket" | "update_backlog_ticket" | "post_slack_message",
                "parameters": {
                    "project_key": "PROJ",
                    "summary": "Issue title",
                    "description": "Issue description",
                    ...
                }
            }

            Example: {"action": "create_backlog_ticket", "parameters": {"summary": "Fix login bug", ...}}
            """
        ),
        Tool(
            name="Summarize",
            func=summarize_tool.run,
            description="""
            Useful for analyzing Slack conversations:
            - Get messages from Slack channels
            - Summarize discussions
            - Extract action items and decisions
            - Find mentions of specific topics

            Input should be a JSON string with action and parameters:
            {
                "action": "get_messages" | "summarize" | "extract_action_items",
                "parameters": {
                    "channel": "channel-name",
                    "start_date": "2024-01-01",
                    ...
                }
            }

            Example: {"action": "summarize", "parameters": {"channel": "engineering", "days": 7}}
            """
        ),
        Tool(
            name="CodeReview",
            func=code_review_tool.run,
            description="""
            Useful for reviewing GitLab code:
            - Get merge requests and commits
            - Analyze code changes
            - Check coding standards
            - Identify potential issues

            Input should be a JSON string with action and parameters:
            {
                "action": "get_merge_requests" | "analyze_code" | "check_standards",
                "parameters": {
                    "project_id": "123",
                    "mr_id": "456",
                    ...
                }
            }

            Example: {"action": "get_merge_requests", "parameters": {"project_id": "123", "state": "opened"}}
            """
        )
    ]

    logger.info(f"Created {len(tools)} tools")

    # Create prompt
    prompt = PromptTemplate.from_template(ORCHESTRATOR_PROMPT)

    # Create agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    # Create agent executor
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=verbose,
        max_iterations=10,
        max_execution_time=300,  # 5 minutes timeout
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    logger.info("✅ Orchestrator agent created successfully")

    # Wrap in OrchestratorAgent class for better control
    return OrchestratorAgent(agent_executor)


class OrchestratorAgent:
    """
    Wrapper class for orchestrator agent with additional functionality
    """

    def __init__(self, agent_executor: AgentExecutor):
        self.agent_executor = agent_executor
        self.logger = logging.getLogger(__name__)

    async def arun(
        self,
        input: str,
        conversation_id: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent asynchronously

        Args:
            input: User input/question
            conversation_id: Conversation ID for tracking
            history: Conversation history (optional)

        Returns:
            Dict with output and sources
        """

        self.logger.info(f"Running orchestrator for conversation: {conversation_id}")
        self.logger.info(f"Input: {input[:100]}...")

        try:
            # Build context from history
            context = ""
            if history:
                context = "Previous conversation:\n"
                for msg in history[-3:]:  # Last 3 messages
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    context += f"{role.title()}: {content}\n"
                context += "\n"

            # Add context to input
            full_input = f"{context}Current question: {input}"

            # Run agent
            result = await self.agent_executor.ainvoke(
                {"input": full_input},
                return_only_outputs=False
            )

            self.logger.info(f"Raw result from agent: {result}")
            self.logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")

            # Extract output and intermediate steps
            output = result.get("output", "")
            self.logger.info(f"Extracted output: '{output}'")
            intermediate_steps = result.get("intermediate_steps", [])
            self.logger.info(f"Intermediate steps count: {len(intermediate_steps)}")

            # Extract sources from intermediate steps
            sources = []
            for step in intermediate_steps:
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    if hasattr(action, 'tool') and action.tool == "VectorSearch":
                        # Extract sources from vector search results
                        if isinstance(observation, list):
                            sources.extend(observation)

            self.logger.info(f"Agent completed successfully")
            self.logger.info(f"Output: {output}")
            self.logger.info(f"Output type: {type(output)}")
            self.logger.info(f"Output length: {len(str(output))} chars")
            self.logger.info(f"Sources found: {len(sources)}")
            self.logger.info(f"Result dict: {result}")

            return {
                "output": output,
                "sources": sources[:5],  # Top 5 sources
                "intermediate_steps": len(intermediate_steps)
            }

        except Exception as e:
            self.logger.error(f"Error running orchestrator: {e}", exc_info=True)
            return {
                "output": f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question.",
                "sources": [],
                "error": str(e)
            }
