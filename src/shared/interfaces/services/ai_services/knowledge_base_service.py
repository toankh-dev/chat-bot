from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IKnowledgeBaseService(ABC):
    @abstractmethod
    async def retrieve_contexts(self, query: str, knowledge_base_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve contexts from Bedrock Knowledge Base."""
        pass
    
    @abstractmethod
    async def get_knowledge_base_by_domain(self, domain: str) -> str:
        """Get Knowledge Base ID for domain."""
        pass