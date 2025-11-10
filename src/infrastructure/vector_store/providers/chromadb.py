from ..base import BaseVectorStore
import chromadb
from chromadb.config import Settings
from typing import List, Any, Dict
import uuid

class ChromaDBVectorStore(BaseVectorStore):
    def __init__(self, persist_directory: str = ".chromadb"):
        self.client = chromadb.Client(Settings(persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection("vectors")

    def add_vector(self, vector: List[float], metadata: dict) -> str:
        vector_id = str(uuid.uuid4())
        self.collection.add(
            ids=[vector_id],
            embeddings=[vector],
            metadatas=[metadata]
        )
        return vector_id

    def query(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query vectors and return structured results matching interface."""
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k
        )
        
        formatted_results = []
        if results["ids"]:
            for i, vector_id in enumerate(results["ids"][0]):
                context = {
                    "context_id": vector_id,
                    "text": results["metadatas"][0][i].get("text", ""),
                    "source": results["metadatas"][0][i].get("source", ""),
                    "retrieval_score": 1 - results["distances"][0][i] if "distances" in results else 1.0,
                    "metadata": results["metadatas"][0][i]
                }
                formatted_results.append(self.format_context_response(context))
        
        return formatted_results

    def get_context_by_id(self, context_id: str) -> Dict[str, Any]:
        """Retrieve specific context by ID."""
        try:
            results = self.collection.get(ids=[context_id])
            if results["ids"]:
                metadata = results["metadatas"][0] if results["metadatas"] else {}
                return {
                    "context_id": context_id,
                    "text": metadata.get("text", ""),
                    "metadata": metadata
                }
        except Exception as e:
            print(f"Error retrieving context {context_id}: {e}")
        return {}

    def store_contexts(self, contexts: List[Dict[str, Any]], source_id: str = "") -> List[str]:
        """Store multiple contexts (implements BaseVectorStore interface)."""
        context_ids = []
        for context in contexts:
            # Add source_id to metadata
            context["source_id"] = source_id
            # Assuming vector is empty or generated elsewhere
            vector = context.get("vector", [0.0] * 768)  # Default embedding size
            context_id = self.add_vector(vector, context)
            context_ids.append(context_id)
        return context_ids
