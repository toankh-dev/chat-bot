import os
import logging
from typing import Dict, Any, Type

from app.embeddings.base import EmbeddingProvider
from app.embeddings.gemini_client import GeminiEmbeddingProvider
from app.embeddings.voyage_client import VoyageEmbeddingProvider

class EmbeddingProviderFactory:
    """Factory để tạo đối tượng embedding provider dựa trên tên provider."""
    _PROVIDER_MAP: Dict[str, Dict[str, Any]] = {
        "gemini": {
            "cls": GeminiEmbeddingProvider,
            "env": {
                "api_key": "LLM_API_KEY",
                "model":   "EMBED_MODEL"
            },
            "defaults": {
                "model": "gemini-embedding-001"
            }
        },
        "voyage": {
            "cls": VoyageEmbeddingProvider,
            "env": {
                "api_key": "EMBED_API_KEY",
                "model":   "EMBED_MODEL"
            },
            "defaults": {
                "model": "voyage-2"
            }
        }
    }

    @classmethod
    def create(cls, provider_name: str, **override_kwargs) -> EmbeddingProvider:
        provider_name = provider_name.lower()
        info = cls._PROVIDER_MAP.get(provider_name)
        if not info:
            raise ValueError(f"Unsupported embedding provider: {provider_name}")

        provider_cls: Type[EmbeddingProvider] = info["cls"]
        init_kwargs: Dict[str, Any] = {}

        for param, env_var in info["env"].items():
            if param in override_kwargs:
                init_kwargs[param] = override_kwargs[param]
            else:
                val = os.getenv(env_var)
                if val is None and "defaults" in info and param in info["defaults"]:
                    val = info["defaults"][param]
                if val is None:
                    raise ValueError(f"Missing required parameter '{param}' for provider '{provider_name}'. Please set environment variable '{env_var}' or pass override.")
                init_kwargs[param] = val

        for k, v in override_kwargs.items():
            init_kwargs[k] = v

        logging.getLogger(__name__).info(
            f"EmbeddingProviderFactory: creating provider '{provider_name}' with class {provider_cls.__name__} and kwargs {init_kwargs}"
        )

        return provider_cls(**init_kwargs)