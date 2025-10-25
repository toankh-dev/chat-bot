"""
Orchestrator Agent using LangChain
Coordinates multiple specialized agents to handle user requests
"""

import logging
from typing import Any, Optional, List, Dict
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from tools.report_tool import ReportTool
from tools.summarize_tool import SummarizeTool
from tools.code_review_tool import CodeReviewTool
from tools.vector_search_tool import VectorSearchTool
from llm.custom_llm import CustomLLM

logger = logging.getLogger(__name__)


# Orchestrator prompt template
ORCHESTRATOR_PROMPT = """You are an intelligent orchestrator agent that coordinates multiple specialized agents to help users with project management tasks.

You have access to the following tools:

{tools}

Tool Names: {tool_names}

**Your Responsibilities:**

1. **Analyze** user questions to understand their intent
2. **Plan** the execution strategy:
   - For simple queries: Use VectorSearch to find information
   - For actions: Use appropriate agent (Report, Summarize, or CodeReview)
   - For complex tasks: Coordinate multiple tools sequentially
3. **Execute** the plan by calling tools with proper parameters
4. **Synthesize** results into a clear, helpful response

**Decision Framework:**

- If user asks "What/Where/Show/Find/List" → Use VectorSearch tool
- If user says "Create/Update/Post/Send" → Use Report tool
- If user wants "Summarize/Analyze" Slack → Use Summarize tool
- If user wants code review → Use CodeReview tool
- If task requires multiple steps → Execute sequentially, passing context between steps

**Guidelines:**

- Always provide clear, concise answers
- Cite sources when referencing data
- Ask for clarification if the request is ambiguous
- Explain your reasoning when coordinating multiple tools
- Handle errors gracefully and provide helpful alternatives

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

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""


def create_orchestrator_agent(
    llm_service_url: str,
    vector_store: Any,
    verbose: bool = True
) -> AgentExecutor:
    """
    Create the orchestrator agent with all tools

    Args:
        llm_service_url: URL of the LLM service
        vector_store: Vector store client instance
        verbose: Whether to print agent reasoning

    Returns:
        AgentExecutor instance
    """

    logger.info("Creating orchestrator agent...")

    # Initialize custom LLM
    llm = CustomLLM(service_url=llm_service_url)

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

    return agent_executor


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

            # Extract output and intermediate steps
            output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])

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
            self.logger.info(f"Output length: {len(output)} chars")
            self.logger.info(f"Sources found: {len(sources)}")

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
