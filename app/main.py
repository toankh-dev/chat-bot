"""
Main FastAPI Application for Multi-Agent Chatbot
Integrates LangChain agents with HuggingFace models
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import httpx

# Import our modules
from agents.orchestrator import create_orchestrator_agent
from vector_store.chromadb_client import VectorStoreClient
from database.conversation_store import ConversationStore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8000")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8000")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "chromadb")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))

# Global instances
vector_store: Optional[VectorStoreClient] = None
conversation_store: Optional[ConversationStore] = None
orchestrator_agent: Optional[Any] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown"""
    global vector_store, conversation_store, orchestrator_agent

    logger.info("🚀 Starting Multi-Agent Chatbot...")

    try:
        # Initialize Vector Store
        logger.info("📚 Connecting to ChromaDB...")
        vector_store = VectorStoreClient(
            host=CHROMADB_HOST,
            port=CHROMADB_PORT,
            embedding_service_url=EMBEDDING_SERVICE_URL
        )
        await vector_store.initialize()
        logger.info("✅ ChromaDB connected")

        # Initialize Conversation Store
        logger.info("💾 Connecting to database...")
        conversation_store = ConversationStore()
        await conversation_store.initialize()
        logger.info("✅ Database connected")

        # Initialize Orchestrator Agent
        logger.info("🤖 Creating orchestrator agent...")
        orchestrator_agent = create_orchestrator_agent(
            llm_service_url=LLM_SERVICE_URL,
            vector_store=vector_store
        )
        logger.info("✅ Orchestrator agent ready")

        logger.info("🎉 All services initialized successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

    yield

    # Cleanup
    logger.info("🛑 Shutting down services...")
    if vector_store:
        await vector_store.close()
    if conversation_store:
        await conversation_store.close()
    logger.info("👋 Goodbye!")


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Chatbot",
    description="AI-powered chatbot with multi-agent orchestration",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message", min_length=1)
    conversation_id: Optional[str] = Field(None, description="Conversation ID (auto-generated if not provided)")
    user_id: Optional[str] = Field("anonymous", description="User ID")
    stream: Optional[bool] = Field(False, description="Stream response")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the open bugs in GitLab?",
                "conversation_id": "conv-123",
                "user_id": "user-456"
            }
        }


class ChatResponse(BaseModel):
    """Chat response model"""
    conversation_id: str
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    processing_time: float
    model: str = "orchestrator-agent"

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-123",
                "answer": "There are 3 open bugs...",
                "sources": [{"source": "gitlab", "id": "issue-123"}],
                "processing_time": 2.5
            }
        }


class ConversationHistory(BaseModel):
    """Conversation history model"""
    conversation_id: str
    user_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: Dict[str, str]
    version: str


# Dependency injection
async def get_vector_store() -> VectorStoreClient:
    """Get vector store instance"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    return vector_store


async def get_conversation_store() -> ConversationStore:
    """Get conversation store instance"""
    if conversation_store is None:
        raise HTTPException(status_code=503, detail="Conversation store not initialized")
    return conversation_store


async def get_orchestrator() -> Any:
    """Get orchestrator agent instance"""
    if orchestrator_agent is None:
        raise HTTPException(status_code=503, detail="Orchestrator agent not initialized")
    return orchestrator_agent


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Multi-Agent Chatbot",
        "version": "2.0.0",
        "description": "Local setup with HuggingFace models",
        "endpoints": {
            "chat": "POST /chat",
            "conversations": "GET /conversations/{user_id}",
            "health": "GET /health"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""

    # Check services
    services = {
        "vector_store": "unknown",
        "conversation_store": "unknown",
        "orchestrator": "unknown",
        "embedding_service": "unknown",
        "llm_service": "unknown"
    }

    # Check vector store
    if vector_store is not None:
        try:
            await vector_store.health_check()
            services["vector_store"] = "healthy"
        except Exception as e:
            services["vector_store"] = f"unhealthy: {str(e)}"

    # Check conversation store
    if conversation_store is not None:
        try:
            await conversation_store.health_check()
            services["conversation_store"] = "healthy"
        except Exception as e:
            services["conversation_store"] = f"unhealthy: {str(e)}"

    # Check orchestrator
    if orchestrator_agent is not None:
        services["orchestrator"] = "healthy"

    # Check embedding service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{EMBEDDING_SERVICE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                services["embedding_service"] = "healthy"
            else:
                services["embedding_service"] = f"unhealthy: status {response.status_code}"
    except Exception as e:
        services["embedding_service"] = f"unhealthy: {str(e)}"

    # Check LLM service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LLM_SERVICE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                services["llm_service"] = "healthy"
            else:
                services["llm_service"] = f"unhealthy: status {response.status_code}"
    except Exception as e:
        services["llm_service"] = f"unhealthy: {str(e)}"

    # Overall status
    all_healthy = all(s == "healthy" for s in services.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        services=services,
        version="2.0.0"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent = Depends(get_orchestrator),
    conv_store = Depends(get_conversation_store)
):
    """
    Main chat endpoint

    Process user message through orchestrator agent and return response
    """
    import time
    start_time = time.time()

    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or f"conv-{uuid.uuid4().hex[:12]}"

        logger.info(f"Processing chat request: {conversation_id}")
        logger.info(f"User: {request.user_id}")
        logger.info(f"Message: {request.message[:100]}...")

        # Get conversation history
        history = await conv_store.get_conversation(conversation_id)

        # Build context from history
        context_messages = []
        if history:
            for msg in history[-5:]:  # Last 5 messages for context
                context_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })

        # Add current message
        context_messages.append({
            "role": "user",
            "content": request.message
        })

        # Run agent
        logger.info("🤖 Running orchestrator agent...")
        result = await agent.arun(
            input=request.message,
            conversation_id=conversation_id,
            history=context_messages
        )

        # Extract answer and sources
        if isinstance(result, dict):
            answer = result.get("output", str(result))
            sources = result.get("sources", [])
        else:
            answer = str(result)
            sources = []

        processing_time = time.time() - start_time

        logger.info(f"✅ Response generated in {processing_time:.2f}s")
        logger.info(f"Answer preview: {answer[:100]}...")

        # Save to conversation history
        await conv_store.add_message(
            conversation_id=conversation_id,
            user_id=request.user_id,
            role="user",
            content=request.message
        )

        await conv_store.add_message(
            conversation_id=conversation_id,
            user_id=request.user_id,
            role="assistant",
            content=answer
        )

        return ChatResponse(
            conversation_id=conversation_id,
            answer=answer,
            sources=sources,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"❌ Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.get("/conversations/{user_id}")
async def get_conversations(
    user_id: str,
    limit: int = 10,
    conv_store = Depends(get_conversation_store)
):
    """Get conversation history for a user"""
    try:
        conversations = await conv_store.get_user_conversations(user_id, limit=limit)
        return {
            "user_id": user_id,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    conv_store = Depends(get_conversation_store)
):
    """Get specific conversation by ID"""
    try:
        messages = await conv_store.get_conversation(conversation_id)
        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "count": len(messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conv_store = Depends(get_conversation_store)
):
    """Delete a conversation"""
    try:
        await conv_store.delete_conversation(conversation_id)
        return {"message": "Conversation deleted", "conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_knowledge_base(
    query: str,
    limit: int = 10,
    vector_store = Depends(get_vector_store)
):
    """Search the knowledge base"""
    try:
        results = await vector_store.search(query, limit=limit)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=os.getenv("RELOAD_ON_CHANGE", "true").lower() == "true"
    )
