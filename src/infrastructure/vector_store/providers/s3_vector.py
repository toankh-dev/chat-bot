import io
import json
from typing import List, Any, Dict, Optional
import boto3
import numpy as np
import uuid
from ..base import BaseVectorStore

class S3VectorStore(BaseVectorStore):
    """
    S3 Vector Store for multiple Bedrock Knowledge Bases by domain.
    Supports domain-specific knowledge bases (healthcare, education, etc.)
    """
    def __init__(self, bucket_name: str, domain: str = "general", prefix: str = "knowledge_bases/"):
        self.bucket_name = bucket_name
        self.domain = domain.lower()
        self.prefix = f"{prefix}{self.domain}/"
        self.s3 = boto3.client("s3")

    def add_vector(self, vector: List[float], metadata: dict) -> str:
        """
        Store context data from domain-specific Bedrock Knowledge Base.
        metadata should contain: text, document_id, retrieval_score, domain, etc.
        """
        context_id = str(uuid.uuid4())
        obj = {
            "context_id": context_id,
            "domain": self.domain,
            "text": metadata.get("text", ""),
            "document_id": metadata.get("document_id", ""),
            "retrieval_score": metadata.get("retrieval_score", 0.0),
            "source_location": metadata.get("source_location", ""),
            "knowledge_base_id": metadata.get("knowledge_base_id", ""),
            "created_at": metadata.get("created_at", ""),
            "metadata": metadata
        }
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        key = f"{self.prefix}contexts/{context_id}.json"
        self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=data)
        return context_id

    def query(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Simple retrieval of stored contexts from specific domain.
        For actual RAG retrieval, use domain-specific Bedrock Knowledge Base API.
        """
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name, 
            Prefix=f"{self.prefix}contexts/",
            MaxKeys=top_k
        )
        results = []
        
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                try:
                    file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
                    data = file_obj["Body"].read().decode('utf-8')
                    stored_context = json.loads(data)
                    results.append(stored_context)
                except Exception as e:
                    print(f"Error retrieving context {key}: {e}")
                    continue
        
        return results

    def store_contexts(self, contexts: List[Dict[str, Any]], source_id: str = "") -> List[str]:
        """
        Store multiple contexts (implements BaseVectorStore interface).
        """
        return self.store_bedrock_contexts(contexts, source_id)

    def store_bedrock_contexts(self, contexts: List[Dict[str, Any]], knowledge_base_id: str) -> List[str]:
        """
        Store multiple contexts retrieved from domain-specific Bedrock Knowledge Base.
        """
        context_ids = []
        for context in contexts:
            # Add domain and KB info to context
            context["knowledge_base_id"] = knowledge_base_id
            context["domain"] = self.domain
            context_id = self.add_vector([], context)
            context_ids.append(context_id)
        return context_ids

    def get_context_by_id(self, context_id: str) -> Dict[str, Any]:
        """
        Retrieve specific context by ID from current domain.
        """
        key = f"{self.prefix}contexts/{context_id}.json"
        try:
            file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            data = file_obj["Body"].read().decode('utf-8')
            return json.loads(data)
        except Exception as e:
            print(f"Error retrieving context {context_id}: {e}")
            return {}

    def get_contexts_by_domain(self, domain: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all contexts from a specific domain.
        """
        domain_prefix = f"knowledge_bases/{domain.lower()}/contexts/"
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=domain_prefix,
            MaxKeys=limit
        )
        
        results = []
        if "Contents" in response:
            for obj in response["Contents"]:
                try:
                    file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=obj["Key"])
                    data = file_obj["Body"].read().decode('utf-8')
                    context = json.loads(data)
                    results.append(context)
                except Exception as e:
                    print(f"Error retrieving {obj['Key']}: {e}")
        
        return results

    @classmethod
    def create_domain_store(cls, bucket_name: str, domain: str) -> 'S3VectorStore':
        """
        Factory method to create domain-specific vector store.
        """
        return cls(bucket_name=bucket_name, domain=domain)
