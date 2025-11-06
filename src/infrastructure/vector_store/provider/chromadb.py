from ..base import BaseVectorStore
import chromadb
from chromadb.config import Settings
from typing import List, Any

class ChromaDBVectorStore(BaseVectorStore):
    def __init__(self, persist_directory: str = ".chromadb"):
        self.client = chromadb.Client(Settings(persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection("vectors")

    def add_vector(self, vector: List[float], metadata: dict) -> str:
        import uuid
        vector_id = str(uuid.uuid4())
        self.collection.add(
            ids=[vector_id],
            embeddings=[vector],
            metadatas=[metadata]
        )
        return vector_id

    def query(self, vector: List[float], top_k: int = 5) -> List[Any]:
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k
        )
        return results["ids"]
