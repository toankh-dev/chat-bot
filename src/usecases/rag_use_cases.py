from shared.interfaces.services.ai_services.rag_service import IRAGService
from typing import Dict, Any, List

class RetrieveContextsUseCase:
    def __init__(self, rag_service: IRAGService):
        self.rag_service = rag_service
    
    async def execute(self, query: str, domain: str = "general", top_k: int = 5) -> List[Dict[str, Any]]:
        return await self.rag_service.retrieve_contexts(query, domain, top_k)

class ChatWithDocumentsUseCase:
    def __init__(self, rag_service: IRAGService):
        self.rag_service = rag_service
    
    async def execute(self, query: str, domain: str = "general", context_limit: int = 5) -> Dict[str, Any]:
        return await self.rag_service.retrieve_and_generate(query, domain, context_limit)

class SemanticSearchUseCase:
    def __init__(self, rag_service: IRAGService):
        self.rag_service = rag_service
    
    async def execute(self, search_query: str, domain: str = "general", result_limit: int = 10) -> Dict[str, Any]:
        contexts = await self.rag_service.retrieve_contexts(search_query, domain, result_limit)
        
        return {
            "query": search_query,
            "results": contexts,
            "total_found": len(contexts),
            "domain": domain
        }