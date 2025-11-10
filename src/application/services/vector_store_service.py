from shared.interfaces.services.ai_services.vector_store_service import IVectorStore
from typing import List, Any

class VectorStoreService:
    def __init__(self, vector_store: IVectorStore):
        self.vector_store = vector_store

    def add_vector(self, vector: List[float], metadata: dict) -> str:
        return self.vector_store.add_vector(vector, metadata)

    def query(self, vector: List[float], top_k: int = 5) -> List[Any]:
        return self.vector_store.query(vector, top_k)
