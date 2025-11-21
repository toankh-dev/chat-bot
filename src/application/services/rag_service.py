from shared.interfaces.services.ai_services.rag_service import IRAGService
from shared.interfaces.services.ai_services.knowledge_base_service import IKnowledgeBaseService
from shared.interfaces.services.ai_services.llm_service import ILLMService
from typing import List, Dict, Any


class RAGService(IRAGService):
    """
    RAG (Retrieval-Augmented Generation) Service.
    Combines knowledge base retrieval with LLM generation.
    """

    def __init__(self,knowledge_base_service: IKnowledgeBaseService):
        self.knowledge_base_service = knowledge_base_service

    async def retrieve_contexts(
        self, query: str, knowledge_base_id: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant contexts from knowledge base."""
        return await self.knowledge_base_service.retrieve_contexts(query, knowledge_base_id, top_k)
