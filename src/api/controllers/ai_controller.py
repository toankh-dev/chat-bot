from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from schemas.rag_schema import QueryRequest, ChatResponse, SearchResponse, ContextResponse
from usecases.rag_use_cases import ChatWithDocumentsUseCase, SemanticSearchUseCase, RetrieveContextsUseCase
from core.dependencies import (
    get_chat_with_documents_use_case, 
    get_semantic_search_use_case,
    get_retrieve_contexts_use_case,
    get_rag_service
)
from shared.interfaces.services.ai_services.rag_service import IRAGService
from infrastructure.ai_services.factory import LLMFactory
from core.logger import logger
from pydantic import BaseModel

class LLMTestRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7

class AIController:
    def __init__(self):
        self.router = APIRouter(prefix="/ai", tags=["AI Services"])  # Changed to /ai
        self._setup_routes()
    
    def _setup_routes(self):
        # === LLM Management Endpoints ===
        
        @self.router.get("/providers")
        async def get_available_providers() -> Dict[str, Any]:
            """Get list of available LLM providers and models."""
            try:
                providers = LLMFactory.get_available_providers()
                models = LLMFactory.get_provider_models()
                
                return {
                    "providers": providers,
                    "models": models,
                    "current_provider": "bedrock"  # Default from config
                }
            except Exception as e:
                logger.error(f"Error getting providers: {e}")
                raise HTTPException(status_code=500, detail="Failed to get providers")
        
        @self.router.get("/info")
        async def get_ai_system_info(
            rag_service: IRAGService = Depends(get_rag_service)
        ):
            """Get complete AI system information including RAG and LLM details."""
            try:
                return {
                    "ai_system": "Unified RAG + LLM System",
                    "current_llm_provider": rag_service.get_provider_name(),
                    "model_info": rag_service.get_model_info(),
                    "knowledge_base": "AWS Bedrock Knowledge Base",
                    "vector_store": "S3 + OpenSearch",
                    "available_endpoints": [
                        "/ai/chat - Chat with documents (RAG)",
                        "/ai/generate - Direct LLM generation",
                        "/ai/search - Semantic search",
                        "/ai/contexts - Retrieve contexts only",
                        "/ai/providers - Available LLM providers",
                        "/ai/test - Test LLM with prompt"
                    ]
                }
            except Exception as e:
                logger.error(f"AI system info error: {e}")
                raise HTTPException(status_code=500, detail="Failed to get AI system info")
        
        @self.router.post("/test")
        async def test_llm(
            request: LLMTestRequest,
            rag_service: IRAGService = Depends(get_rag_service)
        ) -> Dict[str, Any]:
            """Test current LLM provider with a sample prompt."""
            try:
                response = await rag_service.generate_response(
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
                
                return {
                    "response": response,
                    "provider": rag_service.get_provider_name(),
                    "model_info": rag_service.get_model_info(),
                    "prompt": request.prompt
                }
                
            except Exception as e:
                logger.error(f"Error testing LLM: {e}")
                raise HTTPException(status_code=500, detail=f"LLM test failed: {str(e)}")
        
        @self.router.post("/generate")
        async def generate_text(
            request: LLMTestRequest,
            rag_service: IRAGService = Depends(get_rag_service)
        ) -> Dict[str, Any]:
            """Generate text using direct LLM (without RAG)."""
            try:
                response = await rag_service.generate_response(
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
                
                return {
                    "generated_text": response,
                    "provider": rag_service.get_provider_name(),
                    "prompt": request.prompt
                }
                
            except Exception as e:
                logger.error(f"Error generating text: {e}")
                raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")
        
        # === RAG Endpoints ===
        
        @self.router.post("/chat", response_model=ChatResponse)
        async def chat_with_documents(
            request: QueryRequest,
            use_case: ChatWithDocumentsUseCase = Depends(get_chat_with_documents_use_case)
        ):
            """Chat with documents using RAG (Retrieval-Augmented Generation)."""
            try:
                result = await use_case.execute(
                    query=request.query,
                    domain=request.domain,
                    context_limit=request.context_limit
                )
                return ChatResponse(**result)
            except Exception as e:
                logger.error(f"Chat error: {e}")
                raise HTTPException(status_code=500, detail="Failed to process chat request")
        
        @self.router.post("/search", response_model=SearchResponse)
        async def semantic_search(
            request: QueryRequest,
            use_case: SemanticSearchUseCase = Depends(get_semantic_search_use_case)
        ):
            """Perform semantic search across document knowledge base."""
            try:
                result = await use_case.execute(
                    search_query=request.query,
                    domain=request.domain,
                    result_limit=request.context_limit
                )
                return SearchResponse(**result)
            except Exception as e:
                logger.error(f"Search error: {e}")
                raise HTTPException(status_code=500, detail="Failed to process search request")
        
        @self.router.post("/contexts", response_model=ContextResponse)
        async def retrieve_contexts(
            request: QueryRequest,
            use_case: RetrieveContextsUseCase = Depends(get_retrieve_contexts_use_case)
        ):
            """Retrieve relevant document contexts without generating response."""
            try:
                contexts = await use_case.execute(
                    query=request.query,
                    domain=request.domain,
                    top_k=request.context_limit
                )
                return ContextResponse(
                    contexts=contexts,
                    query=request.query,
                    domain=request.domain
                )
            except Exception as e:
                logger.error(f"Context retrieval error: {e}")
                raise HTTPException(status_code=500, detail="Failed to retrieve contexts")