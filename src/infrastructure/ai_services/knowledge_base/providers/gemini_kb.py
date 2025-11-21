"""
Google Gemini Knowledge Base Service (RAG based).
"""

from typing import List, Dict, Any
from shared.interfaces.services.ai_services.knowledge_base_service import IKnowledgeBaseService
from infrastructure.ai_services.gemini_client import GeminiClient


class GeminiKnowledgeBaseService(IKnowledgeBaseService):
    """
    KnowledgeBase service using:
    - Gemini for embeddings
    - Vector store (passed externally) for retrieval
    """

    def __init__(self, gemini_client: GeminiClient, vector_store):
        """
        Args:
            gemini_client: shared Gemini client
            vector_store: your vector database (Chroma, FAISS, PGVector...)
                           must support similarity_search(query_embed, top_k)
        """
        self.gemini_client = gemini_client
        self.vector_store = vector_store

    # ----------------------------------------------------------------------
    # RETRIEVE CONTEXTS (RAG search)
    # ----------------------------------------------------------------------
    async def retrieve_contexts(
        self,
        query: str,
        knowledge_base_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve contexts using:
        - Gemini embeddings
        - Vector store similarity search
        """

        # 1) embed query
        query_embedding = self.gemini_client.embed(query)

        # 2) search vector DB
        search_results = self.vector_store.similarity_search_by_vector(
            query_embedding,
            top_k=top_k,
            namespace=knowledge_base_id
        )

        contexts = []

        for item in search_results:
            contexts.append({
                "text": item.metadata.get("text", item.page_content),
                "source": item.metadata.get("source", ""),
                "score": item.metadata.get("score", item.score if hasattr(item, "score") else 0.0),
                "metadata": item.metadata
            })

        return contexts