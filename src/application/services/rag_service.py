from shared.interfaces.services.ai_services.rag_service import IRAGService
from shared.interfaces.services.ai_services.knowledge_base_service import IKnowledgeBaseService
from shared.interfaces.services.ai_services.llm_service import ILLMService
from typing import List, Dict, Any

class RAGService(IRAGService):
    """
    RAG (Retrieval-Augmented Generation) Service.
    Combines knowledge base retrieval with LLM generation.
    """

    def __init__(
        self,
        knowledge_base_service: IKnowledgeBaseService,
        llm_provider: ILLMService,
    ):
        self.knowledge_base_service = knowledge_base_service
        self.llm_provider = llm_provider

    async def retrieve_and_generate(
        self, query: str, domain: str = "general", top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Full RAG workflow: retrieve contexts and generate response.
        """
        contexts = await self.retrieve_contexts(query, domain, top_k)

        if not contexts:
            return {
                "response": "No relevant information found.", 
                "contexts": [], 
                "query": query,
                "llm_provider": self.llm_provider.get_provider_name()
            }

        context_text = self._build_context_text(contexts)
        response = await self.llm_provider.generate_response(
            prompt=query,
            context=context_text,
            max_tokens=1000,
            temperature=0.7
        )

        return {
            "response": response,
            "contexts": contexts,
            "query": query,
            "context_count": len(contexts),
            "llm_provider": self.llm_provider.get_provider_name()
        }

    async def generate_response(
        self,
        prompt: str,
        context: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response using LLM provider (with optional context).
        Can be used for both RAG and direct LLM calls.
        """
        return await self.llm_provider.generate_response(
            prompt=prompt,
            context=context,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
    
    async def generate_streaming_response(
        self,
        prompt: str,
        context: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Generate streaming response using LLM provider.
        """
        async for chunk in self.llm_provider.generate_streaming_response(
            prompt=prompt,
            context=context,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        ):
            yield chunk

    async def retrieve_contexts(
        self, query: str, domain: str = "general", top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant contexts from knowledge base."""
        knowledge_base_id = await self.knowledge_base_service.get_knowledge_base_by_domain(domain)
        return await self.knowledge_base_service.retrieve_contexts(query, knowledge_base_id, top_k)

    def get_provider_name(self) -> str:
        """Get current LLM provider name."""
        return self.llm_provider.get_provider_name()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information."""
        return self.llm_provider.get_model_info()

    def _build_context_text(self, contexts: List[Dict[str, Any]]) -> str:
        """Build context text from retrieved contexts."""
        return "\n".join(
            [f"Context {i+1}: {ctx.get('text', '')}" for i, ctx in enumerate(contexts)]
        )
