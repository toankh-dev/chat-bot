"""
Orchestrator Lambda Function
Main chat handler with LangChain agent orchestration
"""

import json
import logging
import os
import sys
import time
import uuid
from typing import Dict, Any

# Add common directory to path
sys.path.insert(0, '/opt/python')  # Lambda layer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))

from bedrock_client import BedrockClient
from opensearch_client import OpenSearchVectorClient
from dynamodb_client import ConversationStore, CacheStore
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Initialize clients (outside handler for connection reuse)
bedrock_client = None
opensearch_client = None
conversation_store = None
cache_store = None
agent_executor = None


def initialize_clients():
    """Initialize all clients (called once on cold start)"""
    global bedrock_client, opensearch_client, conversation_store, cache_store, agent_executor

    try:
        logger.info("Initializing clients...")

        # Bedrock client
        bedrock_client = BedrockClient(
            region=os.getenv('AWS_REGION'),
            llm_model_id=os.getenv('BEDROCK_MODEL_ID'),
            embed_model_id=os.getenv('BEDROCK_EMBED_MODEL_ID')
        )

        # OpenSearch client
        opensearch_client = OpenSearchVectorClient(
            collection_endpoint=os.getenv('OPENSEARCH_ENDPOINT'),
            collection_id=os.getenv('OPENSEARCH_COLLECTION_ID'),
            index_name='knowledge_base',
            region=os.getenv('AWS_REGION')
        )

        # DynamoDB stores
        conversation_store = ConversationStore(
            table_name=os.getenv('CONVERSATIONS_TABLE')
        )

        # Cache store (optional)
        if os.getenv('ENABLE_CACHING', 'false').lower() == 'true':
            cache_store = CacheStore(
                table_name=os.getenv('CACHE_TABLE', os.getenv('CONVERSATIONS_TABLE'))
            )

        # Create LangChain agent
        agent_executor = create_agent()

        logger.info("✅ All clients initialized successfully")

    except Exception as e:
        logger.error(f"❌ Error initializing clients: {e}", exc_info=True)
        raise


def create_agent() -> AgentExecutor:
    """
    Create LangChain agent with tools

    Returns:
        AgentExecutor instance
    """
    # Define tools
    tools = [
        Tool(
            name="VectorSearch",
            func=vector_search_tool,
            description="""
            Search the knowledge base for relevant information.
            Input: A search query string.
            Returns: Relevant documents and context.
            Use this when the user asks about specific information, documents, or historical data.
            """
        ),
        # Add more tools here as needed
    ]

    # Create prompt
    prompt = PromptTemplate.from_template("""
You are an intelligent AI assistant that helps users with information retrieval and task management.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

When a user asks a question:
1. Determine if you need to use tools or can answer directly
2. If tools are needed, use them to gather information
3. Synthesize the information into a clear, helpful response

For simple greetings or casual conversation, answer directly without using tools.
For information queries, use the VectorSearch tool to find relevant context.

Use the following format:
Question: the input question you must answer
Thought: think about what to do
Action: the action to take (one of [{tool_names}])
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the user's question

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")

    # Create agent (using Bedrock as LLM)
    from langchain.llms.base import LLM
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from typing import Optional, List

    class BedrockLLM(LLM):
        """LangChain wrapper for Bedrock"""

        @property
        def _llm_type(self) -> str:
            return "bedrock"

        def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> str:
            return bedrock_client.invoke_llm(
                prompt=prompt,
                stop_sequences=stop,
                max_tokens=2048,
                temperature=0.7
            )

    llm = BedrockLLM()

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    # Create executor
    executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        max_execution_time=60,
        handle_parsing_errors=True
    )

    return executor


def vector_search_tool(query: str) -> str:
    """
    Tool function for vector search

    Args:
        query: Search query

    Returns:
        Search results as formatted string
    """
    try:
        logger.info(f"Vector search: {query}")

        # Generate query embedding
        embeddings = bedrock_client.generate_embeddings([query])
        query_vector = embeddings[0]

        # Search OpenSearch
        results = opensearch_client.search(
            query_vector=query_vector,
            k=5,
            min_score=0.5
        )

        # Format results
        if not results:
            return "No relevant information found in the knowledge base."

        formatted_results = []
        for i, result in enumerate(results, 1):
            text = result['text'][:500]  # Truncate for context window
            score = result['score']
            source = result.get('metadata', {}).get('source', 'unknown')

            formatted_results.append(
                f"[{i}] (score: {score:.2f}, source: {source})\n{text}\n"
            )

        return "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Error in vector search tool: {e}")
        return f"Error searching knowledge base: {str(e)}"


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for chat requests

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Initialize clients on first invocation
        global bedrock_client
        if bedrock_client is None:
            initialize_clients()

        # Parse event
        if 'body' in event:
            # API Gateway proxy integration
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            # Direct invocation
            body = event

        # Extract parameters
        message = body.get('message')
        conversation_id = body.get('conversation_id') or f"conv-{uuid.uuid4().hex[:12]}"
        user_id = body.get('user_id', 'anonymous')

        if not message:
            return create_response(400, {'error': 'Message is required'})

        logger.info(f"Processing chat request: {conversation_id}")
        logger.info(f"User: {user_id}, Message: {message[:100]}...")

        start_time = time.time()

        # Check cache (if enabled)
        if cache_store:
            import hashlib
            query_hash = hashlib.sha256(message.encode()).hexdigest()
            cached_response = cache_store.get_cached_response(query_hash)

            if cached_response:
                logger.info("✅ Cache hit!")
                processing_time = time.time() - start_time

                return create_response(200, {
                    'conversation_id': conversation_id,
                    'answer': cached_response,
                    'sources': [],
                    'processing_time': processing_time,
                    'cached': True
                })

        # Get conversation history
        history = conversation_store.get_conversation(conversation_id, limit=10)

        # Build context from history
        context = ""
        if history:
            context = "Previous conversation:\n"
            for msg in history[-3:]:  # Last 3 messages
                role = msg['role']
                content = msg['content'][:200]  # Truncate
                context += f"{role.title()}: {content}\n"
            context += "\n"

        # Prepare input for agent
        full_input = f"{context}Current question: {message}"

        # Run agent
        logger.info("🤖 Running agent...")
        result = agent_executor.invoke({'input': full_input})

        # Extract answer
        answer = result.get('output', 'I encountered an error processing your request.')

        processing_time = time.time() - start_time

        logger.info(f"✅ Response generated in {processing_time:.2f}s")
        logger.info(f"Answer: {answer[:100]}...")

        # Save to conversation history
        conversation_store.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role='user',
            content=message
        )

        conversation_store.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role='assistant',
            content=answer
        )

        # Cache response (if enabled)
        if cache_store and not context:  # Only cache if no history (first query)
            import hashlib
            query_hash = hashlib.sha256(message.encode()).hexdigest()
            cache_store.cache_response(
                query_hash=query_hash,
                query=message,
                response=answer,
                ttl_seconds=3600  # 1 hour
            )

        # Return response
        return create_response(200, {
            'conversation_id': conversation_id,
            'answer': answer,
            'sources': [],
            'processing_time': processing_time,
            'cached': False
        })

    except Exception as e:
        logger.error(f"❌ Error in handler: {e}", exc_info=True)
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create API Gateway response

    Args:
        status_code: HTTP status code
        body: Response body

    Returns:
        API Gateway response format
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }


# Health check endpoint
def health_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Health check handler"""
    try:
        # Check if clients are initialized
        if bedrock_client is None:
            return create_response(503, {
                'status': 'unhealthy',
                'message': 'Clients not initialized'
            })

        # Basic health checks
        health_status = {
            'status': 'healthy',
            'version': '2.0.0',
            'checks': {
                'bedrock': 'ok',
                'opensearch': 'ok' if opensearch_client.health_check() else 'degraded',
                'dynamodb': 'ok'
            }
        }

        return create_response(200, health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_response(503, {
            'status': 'unhealthy',
            'error': str(e)
        })
