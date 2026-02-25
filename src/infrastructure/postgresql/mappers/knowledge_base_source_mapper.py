"""
KnowledgeBaseSource mapper between domain entity and SQLAlchemy model.
"""

from typing import Optional

from domain.entities.knowledge_base_source import KnowledgeBaseSourceEntity
from infrastructure.postgresql.models.knowledge_base_source_model import KnowledgeBaseSourceModel


class KnowledgeBaseSourceMapper:
    """
    Mapper for KnowledgeBaseSource entity <-> model conversion.
    """

    @staticmethod
    def to_entity(model: KnowledgeBaseSourceModel) -> KnowledgeBaseSourceEntity:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: KnowledgeBaseSource SQLAlchemy model

        Returns:
            KnowledgeBaseSourceEntity domain entity
        """
        return KnowledgeBaseSourceEntity(
            id=model.id,
            knowledge_base_id=model.knowledge_base_id,
            source_type=model.source_type,
            source_id=model.source_id,
            config=model.config,
            auto_sync=model.auto_sync,
            sync_status=model.sync_status,
            last_synced_at=model.last_synced_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: KnowledgeBaseSourceEntity,
        existing_model: Optional[KnowledgeBaseSourceModel] = None
    ) -> KnowledgeBaseSourceModel:
        """
        Convert domain entity to SQLAlchemy model.

        Args:
            entity: KnowledgeBaseSource domain entity
            existing_model: Existing model to update (optional)

        Returns:
            KnowledgeBaseSourceModel SQLAlchemy model
        """
        if existing_model:
            # Update existing model
            existing_model.knowledge_base_id = entity.knowledge_base_id
            existing_model.source_type = entity.source_type
            existing_model.source_id = entity.source_id
            existing_model.config = entity.config
            existing_model.auto_sync = entity.auto_sync
            existing_model.sync_status = entity.sync_status
            existing_model.last_synced_at = entity.last_synced_at
            return existing_model
        else:
            # Create new model
            model_data = {
                "knowledge_base_id": entity.knowledge_base_id,
                "source_type": entity.source_type,
                "source_id": entity.source_id,
                "config": entity.config,
                "auto_sync": entity.auto_sync,
                "sync_status": entity.sync_status,
                "last_synced_at": entity.last_synced_at,
            }

            if entity.id is not None:
                model_data["id"] = entity.id

            return KnowledgeBaseSourceModel(**model_data)
