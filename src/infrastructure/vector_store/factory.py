
import json
from typing import Optional, Dict, Type, List
from .providers.chromadb import ChromaDBVectorStore
from .providers.s3_vector import S3VectorStore
from .base import BaseVectorStore
from core.config import settings
from shared.interfaces.services.ai_services.vector_store_factory import IVectorStoreFactory

class VectorStoreFactory(IVectorStoreFactory):
    """
    Factory for creating vector store instances through abstract interface.
    Returns BaseVectorStore interface instead of concrete implementations.
    """
    _providers: Dict[str, Type[BaseVectorStore]] = {
        'chromadb': ChromaDBVectorStore,
        's3': S3VectorStore,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseVectorStore]):
        """Register a new vector store provider."""
        cls._providers[name] = provider_cls

    @staticmethod
    def _extract_domain_from_collection(collection_name: str) -> str:
        """
        Extract domain from collection name.

        Examples:
            kb_chatbot_9_default -> chatbot
            kb_gitlab_123_repo -> gitlab
            custom_collection -> custom
        """
        if collection_name.startswith('kb_'):
            parts = collection_name.split('_')
            if len(parts) >= 2:
                return parts[1]  # Return the domain part (chatbot, gitlab, etc.)
        return 'default'

    @staticmethod
    def _extract_prefix_from_collection(collection_name: str) -> str:
        """
        Extract S3 prefix from collection name.

        Examples:
            kb_chatbot_9_default -> chatbot_9_default
            kb_gitlab_123_repo -> gitlab_123_repo
            custom_collection -> custom_collection
        """
        if collection_name.startswith('kb_'):
            return collection_name[3:]  # Remove 'kb_' prefix
        return collection_name

    @classmethod
    def create(cls, config: Optional[dict] = None, **kwargs) -> BaseVectorStore:
        """
        Factory method to create a vector store provider through interface.
        Returns BaseVectorStore interface for polymorphic usage.

        Args:
            config: dict config for provider
                For ChromaDB:
                    - collection_name (required): Unique collection name (e.g., kb_{kb_id})
                    - persist_directory (optional): Storage directory (default: .chromadb)

        Returns:
            BaseVectorStore: Abstract interface implementation

        USE CASES:
            - UC-2.1, UC-2.2: Different collection_names → isolated vector stores
            - UC-4.3: KB deletion → delete collection by name
        """
        provider = settings.VECTOR_STORE_PROVIDER
        if provider not in cls._providers:
            raise ValueError(f"Unknown vector store provider: {provider}. Available: {list(cls._providers.keys())}")

        provider_cls = cls._providers[provider]
        config = config or {}
        config.update(kwargs)

        # Create instance with provider-specific configuration
        try:
            collection_name = config.get('collection_name')

            if provider == 'chromadb':
                # ============================================================
                # CRITICAL FIX: Pass collection_name to ChromaDB (Phase 1.3)
                # ============================================================
                # Required for collection-per-KB isolation
                # Format: kb_{knowledge_base_id}
                # ============================================================

                if not collection_name:
                    raise ValueError(
                        "collection_name is required for chromadb provider. "
                        "Expected format: kb_{knowledge_base_id}"
                    )

                # Auto-generate persist_directory from collection_name if not provided
                persist_directory = config.get('persist_directory')
                if not persist_directory:
                    persist_directory = f'.chromadb/{collection_name}'

                return provider_cls(
                    collection_name=collection_name,
                    persist_directory=persist_directory
                )

            elif provider == 's3':
                # ============================================================
                # S3 Provider: Auto-extract domain/prefix from collection_name
                # ============================================================
                # If domain/prefix not explicitly provided, extract from collection_name
                # Format: kb_{domain}_{id}_{name} -> domain={domain}, prefix={domain}_{id}_{name}
                # ============================================================

                bucket = config.get('bucket_name', settings.S3_BUCKET_EMBEDDINGS)

                # Allow explicit domain/prefix, otherwise auto-extract from collection_name
                domain = config.get('domain')
                prefix = config.get('prefix')

                if not domain or not prefix:
                    if not collection_name:
                        raise ValueError(
                            "Either (domain + prefix) or collection_name is required for s3 provider"
                        )
                    # Auto-extract from collection_name
                    if not domain:
                        domain = cls._extract_domain_from_collection(collection_name)
                    if not prefix:
                        prefix = cls._extract_prefix_from_collection(collection_name)

                return provider_cls(bucket_name=bucket, domain=domain, prefix=prefix)

            else:
                # Allow custom provider to handle config
                return provider_cls(**config)
        except Exception as e:
            raise RuntimeError(f"Failed to create {provider} vector store: {e}")

    @classmethod
    def create_domain_specific(cls, domain: str, **config) -> BaseVectorStore:
        """
        Create domain-specific vector store instance.
        
        Args:
            domain: domain name (healthcare, education, etc.)
            **config: additional configuration
            
        Returns:
            BaseVectorStore: Domain-specific vector store
        """
        provider = settings.VECTOR_STORE_PROVIDER
        if provider == 's3':
            config['domain'] = domain
        elif provider == 'chromadb':
            # Use domain-specific directory for ChromaDB
            base_dir = config.get('persist_directory')
            if not base_dir:
                raise ValueError("persist_directory is required for chromadb provider")
            config['persist_directory'] = f"{base_dir}/{domain}"
        
        return cls.create(config=config)

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available vector store providers."""
        return list(cls._providers.keys())
