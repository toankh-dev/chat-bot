"""
Amazon OpenSearch Serverless Client
Vector search and document storage
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

from .config import get_settings

logger = logging.getLogger(__name__)


class OpenSearchVectorClient:
    """Client for Amazon OpenSearch Serverless vector search"""

    def __init__(
        self,
        collection_endpoint: str = None,
        collection_id: str = None,
        index_name: str = "knowledge_base",
        region: str = None
    ):
        """
        Initialize OpenSearch client with environment-aware configuration.

        Args:
            collection_endpoint: OpenSearch collection endpoint (optional, uses settings default)
            collection_id: Collection ID (optional, uses settings default)
            index_name: Index name for vectors (default: knowledge_base)
            region: AWS region (optional, uses settings default)
        """
        self.settings = get_settings()
        self.collection_endpoint = collection_endpoint or self.settings.opensearch_endpoint
        self.collection_id = collection_id or self.settings.opensearch_collection_id
        self.index_name = index_name or self.settings.opensearch_index
        self.region = region or self.settings.aws_region

        if not self.collection_endpoint:
            raise ValueError("OpenSearch collection endpoint is required")

        # Remove protocol from endpoint if present
        host = self.collection_endpoint.replace('https://', '').replace('http://', '')

        # Configure based on environment (LocalStack vs AWS)
        if self.settings.is_local:
            # LocalStack: Simple HTTP connection without auth
            self.client = OpenSearch(
                hosts=[{'host': host.split(':')[0], 'port': int(host.split(':')[1]) if ':' in host else 9200}],
                http_auth=None,
                use_ssl=False,
                verify_certs=False,
                connection_class=RequestsHttpConnection,
                timeout=30
            )
            logger.info(f"Initialized OpenSearch client for LocalStack at {self.collection_endpoint}")
        else:
            # AWS: Use AWSV4 signing
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, self.region, 'aoss')  # aoss = Amazon OpenSearch Serverless

            self.client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=30
            )
            logger.info(f"Initialized OpenSearch client for AWS collection: {self.collection_id}")

        logger.info(f"Index: {self.index_name} (environment: {self.settings.environment.value})")

    def create_index(
        self,
        dimension: int = 1024,
        engine: str = "nmslib",
        method: str = "hnsw",
        ef_construction: int = 512,
        m: int = 16
    ) -> bool:
        """
        Create k-NN vector index

        Args:
            dimension: Vector dimension (1024 for Titan, 1536 for Cohere)
            engine: Vector engine (nmslib, faiss, lucene)
            method: k-NN method (hnsw for HNSW algorithm)
            ef_construction: HNSW parameter for index construction
            m: HNSW parameter for number of connections

        Returns:
            True if created successfully
        """
        try:
            # Check if index exists
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index {self.index_name} already exists")
                return True

            # Define index mapping
            index_body = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 512
                    }
                },
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": dimension,
                            "method": {
                                "name": method,
                                "engine": engine,
                                "parameters": {
                                    "ef_construction": ef_construction,
                                    "m": m
                                }
                            }
                        },
                        "text": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "metadata": {
                            "properties": {
                                "source": {"type": "keyword"},
                                "doc_id": {"type": "keyword"},
                                "chunk_id": {"type": "keyword"},
                                "timestamp": {"type": "date"},
                                "file_name": {"type": "keyword"},
                                "file_type": {"type": "keyword"},
                                "category": {"type": "keyword"}
                            }
                        },
                        "created_at": {"type": "date"}
                    }
                }
            }

            # Create index
            response = self.client.indices.create(
                index=self.index_name,
                body=index_body
            )

            logger.info(f"Created index {self.index_name}")
            logger.info(f"Response: {response}")
            return True

        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False

    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Index documents with embeddings

        Args:
            documents: List of documents with 'embedding', 'text', and 'metadata'
            batch_size: Batch size for bulk indexing

        Returns:
            Indexing statistics
        """
        try:
            total_docs = len(documents)
            indexed = 0
            errors = []

            logger.info(f"Indexing {total_docs} documents to {self.index_name}")

            # Process in batches
            for i in range(0, total_docs, batch_size):
                batch = documents[i:i + batch_size]
                bulk_body = []

                for doc in batch:
                    # Index operation
                    bulk_body.append({
                        "index": {
                            "_index": self.index_name,
                            "_id": doc.get("id", None)
                        }
                    })

                    # Document body
                    doc_body = {
                        "embedding": doc["embedding"],
                        "text": doc["text"],
                        "metadata": doc.get("metadata", {}),
                        "created_at": doc.get("created_at")
                    }
                    bulk_body.append(doc_body)

                # Bulk index
                response = self.client.bulk(body=bulk_body)

                # Check for errors
                if response.get("errors"):
                    for item in response.get("items", []):
                        if "error" in item.get("index", {}):
                            errors.append(item["index"]["error"])
                else:
                    indexed += len(batch)

                logger.info(f"Indexed batch {i // batch_size + 1}: {indexed}/{total_docs}")

            return {
                "total": total_docs,
                "indexed": indexed,
                "errors": len(errors),
                "error_details": errors[:10]  # First 10 errors
            }

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            raise

    def search(
        self,
        query_vector: List[float],
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search

        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            filter: Metadata filter (optional)
            min_score: Minimum similarity score

        Returns:
            List of search results with text, metadata, and score
        """
        try:
            # Build k-NN query
            query_body = {
                "size": k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": k
                        }
                    }
                },
                "_source": ["text", "metadata", "created_at"],
                "min_score": min_score
            }

            # Add filter if provided
            if filter:
                query_body["query"] = {
                    "bool": {
                        "must": [
                            {"knn": {"embedding": {"vector": query_vector, "k": k}}}
                        ],
                        "filter": self._build_filter(filter)
                    }
                }

            logger.debug(f"Searching with k={k}, min_score={min_score}")

            # Execute search
            response = self.client.search(
                index=self.index_name,
                body=query_body
            )

            # Format results
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "text": hit["_source"]["text"],
                    "metadata": hit["_source"].get("metadata", {}),
                    "created_at": hit["_source"].get("created_at")
                })

            logger.info(f"Found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def hybrid_search(
        self,
        query_vector: List[float],
        query_text: str,
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and text search

        Args:
            query_vector: Query embedding
            query_text: Query text
            k: Number of results
            filter: Metadata filter
            vector_weight: Weight for vector search (0.0 to 1.0)

        Returns:
            Combined search results
        """
        try:
            query_body = {
                "size": k,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_vector,
                                        "k": k,
                                        "boost": vector_weight
                                    }
                                }
                            },
                            {
                                "match": {
                                    "text": {
                                        "query": query_text,
                                        "boost": 1.0 - vector_weight
                                    }
                                }
                            }
                        ]
                    }
                },
                "_source": ["text", "metadata", "created_at"]
            }

            # Add filter
            if filter:
                query_body["query"]["bool"]["filter"] = self._build_filter(filter)

            # Execute search
            response = self.client.search(
                index=self.index_name,
                body=query_body
            )

            # Format results
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "text": hit["_source"]["text"],
                    "metadata": hit["_source"].get("metadata", {}),
                    "created_at": hit["_source"].get("created_at")
                })

            logger.info(f"Hybrid search found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    def delete_documents(
        self,
        doc_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Delete documents by IDs

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            Deletion statistics
        """
        try:
            bulk_body = []
            for doc_id in doc_ids:
                bulk_body.append({
                    "delete": {
                        "_index": self.index_name,
                        "_id": doc_id
                    }
                })

            response = self.client.bulk(body=bulk_body)

            deleted = sum(1 for item in response.get("items", [])
                         if item.get("delete", {}).get("result") == "deleted")

            logger.info(f"Deleted {deleted}/{len(doc_ids)} documents")

            return {
                "total": len(doc_ids),
                "deleted": deleted,
                "errors": response.get("errors", False)
            }

        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

    def _build_filter(self, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build OpenSearch filter from metadata dict

        Args:
            filter: Filter dictionary

        Returns:
            OpenSearch filter clauses
        """
        filters = []

        for key, value in filter.items():
            if isinstance(value, list):
                # Terms filter for multiple values
                filters.append({
                    "terms": {f"metadata.{key}": value}
                })
            else:
                # Term filter for single value
                filters.append({
                    "term": {f"metadata.{key}": value}
                })

        return filters

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.client.indices.stats(index=self.index_name)
            doc_count = stats["indices"][self.index_name]["primaries"]["docs"]["count"]
            size_bytes = stats["indices"][self.index_name]["primaries"]["store"]["size_in_bytes"]

            return {
                "index_name": self.index_name,
                "document_count": doc_count,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2)
            }

        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}

    def health_check(self) -> bool:
        """Check if OpenSearch is healthy"""
        try:
            response = self.client.cluster.health()
            status = response.get("status")
            logger.info(f"OpenSearch cluster status: {status}")
            return status in ["green", "yellow"]

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
