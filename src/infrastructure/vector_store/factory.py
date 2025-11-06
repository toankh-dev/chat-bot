
import os
import json
from typing import Optional, Dict, Type
from .provider.chromadb import ChromaDBVectorStore
from .provider.s3_vector import S3VectorStore
from .base import BaseVectorStore

class VectorStoreFactory:
    _providers: Dict[str, Type[BaseVectorStore]] = {
        'chromadb': ChromaDBVectorStore,
        's3': S3VectorStore,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseVectorStore]):
        cls._providers[name] = provider_cls

    @classmethod
    def create(cls, provider: Optional[str] = None, config: Optional[dict] = None, **kwargs) -> BaseVectorStore:
        """
        Factory method to create a vector store provider.
        - provider: provider name (priority: argument, then ENV VECTOR_STORE_PROVIDER, default 'chromadb')
        - config: dict config for provider (priority: argument, then ENV as JSON, or kwargs)
        """
        provider = provider or os.getenv('VECTOR_STORE_PROVIDER', 'chromadb')
        config = config or {}
        # If config from ENV VECTOR_STORE_CONFIG as JSON
        env_config = os.getenv('VECTOR_STORE_CONFIG')
        if env_config:
            try:
                config.update(json.loads(env_config))
            except Exception:
                pass
        config.update(kwargs)

        if provider not in cls._providers:
            raise ValueError(f"Unknown vector store provider: {provider}")
        provider_cls = cls._providers[provider]

        # Pass config according to provider
        if provider == 'chromadb':
            return provider_cls(persist_directory=config.get('persist_directory', '.chromadb'))
        elif provider == 's3':
            bucket = config.get('bucket_name')
            if not bucket:
                raise ValueError('bucket_name is required for s3 provider')
            prefix = config.get('prefix', 'vectors/')
            return provider_cls(bucket_name=bucket, prefix=prefix)
        else:
            # Allow custom provider to handle config
            return provider_cls(**config)
