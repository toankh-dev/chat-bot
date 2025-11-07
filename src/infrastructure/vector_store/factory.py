
import os
import json
from typing import Optional, Dict, Type, List
from .providers.chromadb import ChromaDBVectorStore
from .providers.s3_vector import S3VectorStore
from .base import BaseVectorStore

class VectorStoreFactory:
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

    @classmethod
    def create(cls, provider: Optional[str] = None, config: Optional[dict] = None, **kwargs) -> BaseVectorStore:
        """
        Factory method to create a vector store provider through interface.
        Returns BaseVectorStore interface for polymorphic usage.
        
        Args:
            provider: provider name (priority: argument, then ENV VECTOR_STORE_PROVIDER, default 'chromadb')
            config: dict config for provider (priority: argument, then ENV as JSON, or kwargs)
            
        Returns:
            BaseVectorStore: Abstract interface implementation
        """
        provider = provider or os.getenv('VECTOR_STORE_PROVIDER', 'chromadb')
        config = config or {}
        
        # Load config from ENV if available
        env_config = os.getenv('VECTOR_STORE_CONFIG')
        if env_config:
            try:
                config.update(json.loads(env_config))
            except Exception:
                pass
        config.update(kwargs)

        if provider not in cls._providers:
            raise ValueError(f"Unknown vector store provider: {provider}. Available: {list(cls._providers.keys())}")
        
        provider_cls = cls._providers[provider]

        # Create instance with provider-specific configuration
        try:
            if provider == 'chromadb':
                return provider_cls(persist_directory=config.get('persist_directory', '.chromadb'))
            elif provider == 's3':
                bucket = config.get('bucket_name')
                if not bucket:
                    raise ValueError('bucket_name is required for s3 provider')
                domain = config.get('domain', 'general')
                prefix = config.get('prefix', 'knowledge_bases/')
                return provider_cls(bucket_name=bucket, domain=domain, prefix=prefix)
            else:
                # Allow custom provider to handle config
                return provider_cls(**config)
        except Exception as e:
            raise RuntimeError(f"Failed to create {provider} vector store: {e}")

    @classmethod
    def create_domain_specific(cls, provider: str, domain: str, **config) -> BaseVectorStore:
        """
        Create domain-specific vector store instance.
        
        Args:
            provider: vector store provider type
            domain: domain name (healthcare, education, etc.)
            **config: additional configuration
            
        Returns:
            BaseVectorStore: Domain-specific vector store
        """
        if provider == 's3':
            config['domain'] = domain
        elif provider == 'chromadb':
            # Use domain-specific directory for ChromaDB
            base_dir = config.get('persist_directory', '.chromadb')
            config['persist_directory'] = f"{base_dir}/{domain}"
        
        return cls.create(provider=provider, config=config)

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available vector store providers."""
        return list(cls._providers.keys())
