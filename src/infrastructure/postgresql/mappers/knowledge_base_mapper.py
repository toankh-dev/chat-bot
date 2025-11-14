"""
KnowledgeBase mapper between domain entity and SQLAlchemy model.
"""

from typing import Optional

from domain.entities.knowledge_base import KnowledgeBaseEntity
from infrastructure.postgresql.models.knowledge_base_model import KnowledgeBaseModel


class KnowledgeBaseMapper:
    """
    Mapper for KnowledgeBase entity <-> model conversion.
    """

    @staticmethod
    def to_entity(model: KnowledgeBaseModel) -> KnowledgeBaseEntity:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: KnowledgeBase SQLAlchemy model

        Returns:
            KnowledgeBaseEntity domain entity
        """
        return KnowledgeBaseEntity(
            id=model.id,
            chatbot_id=model.chatbot_id,
            name=model.name,
            description=model.description,
            vector_store_type=model.vector_store_type,
            vector_store_collection=model.vector_store_collection,
            vector_store_config=model.vector_store_config,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: KnowledgeBaseEntity,
        existing_model: Optional[KnowledgeBaseModel] = None
    ) -> KnowledgeBaseModel:
        """
        Convert domain entity to SQLAlchemy model.

        Args:
            entity: KnowledgeBase domain entity
            existing_model: Existing model to update (optional)

        Returns:
            KnowledgeBaseModel SQLAlchemy model
        """
        if existing_model:
            # Update existing model
            existing_model.chatbot_id = entity.chatbot_id
            existing_model.name = entity.name
            existing_model.description = entity.description
            existing_model.vector_store_type = entity.vector_store_type
            existing_model.vector_store_collection = entity.vector_store_collection
            existing_model.vector_store_config = entity.vector_store_config
            existing_model.is_active = entity.is_active
            return existing_model
        else:
            # Create new model
            model_data = {
                "chatbot_id": entity.chatbot_id,
                "name": entity.name,
                "description": entity.description,
                "vector_store_type": entity.vector_store_type,
                "vector_store_collection": entity.vector_store_collection,
                "vector_store_config": entity.vector_store_config,
                "is_active": entity.is_active,
            }

            if entity.id is not None:
                model_data["id"] = entity.id

            return KnowledgeBaseModel(**model_data)
