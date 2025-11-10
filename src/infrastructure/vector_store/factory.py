
import json
from typing import Optional, Dict, Type, List
from .providers.chromadb import ChromaDBVectorStore
from .providers.s3_vector import S3VectorStore
from .base import BaseVectorStore
from core.config import settings

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
    def create(cls, config: Optional[dict] = None, **kwargs) -> BaseVectorStore:
        """
        Factory method to create a vector store provider through interface.
        Returns BaseVectorStore interface for polymorphic usage.
        
        Args:
            config: dict config for provider
            
        Returns:
            BaseVectorStore: Abstract interface implementation
        """
        provider = settings.VECTOR_STORE_PROVIDER
        if provider not in cls._providers:
            raise ValueError(f"Unknown vector store provider: {provider}. Available: {list(cls._providers.keys())}")
        
        provider_cls = cls._providers[provider]
        config = config or {}
        config.update(kwargs)

        # Create instance with provider-specific configuration
        try:
            if provider == 'chromadb':
                persist_directory = config.get('persist_directory', settings.CHROMADB_PERSIST_DIRECTORY)
                if not persist_directory:
                    raise ValueError("persist_directory is required for chromadb provider")
                return provider_cls(persist_directory=persist_directory)
            elif provider == 's3':
                bucket = config.get('bucket_name', settings.S3_BUCKET_EMBEDDINGS)
                domain = config.get('domain')
                if not domain:
                    raise ValueError("domain is required for s3 provider")
                prefix = config.get('prefix')
                if not prefix:
                    raise ValueError("prefix is required for s3 provider") 
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
