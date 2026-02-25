"""
Unit tests for CreateChatbotUseCase with default knowledge base creation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime

from src.usecases.chatbot_use_cases import CreateChatbotUseCase
from src.schemas.chatbot_schema import ChatbotCreate
from src.domain.entities.chatbot import ChatbotEntity
from src.application.services.chatbot_service import ChatbotService
from src.shared.interfaces.repositories.knowledge_base_repository import IKnowledgeBaseRepository


class TestCreateChatbotUseCase:
    """Tests for CreateChatbotUseCase."""

    @pytest.fixture
    def mock_chatbot_service(self):
        """Create mock chatbot service."""
        service = Mock(spec=ChatbotService)
        return service

    @pytest.fixture
    def mock_kb_repository(self):
        """Create mock knowledge base repository."""
        repository = Mock(spec=IKnowledgeBaseRepository)
        return repository

    @pytest.fixture
    def use_case(self, mock_chatbot_service, mock_kb_repository):
        """Create use case instance with mocks."""
        return CreateChatbotUseCase(
            chatbot_service=mock_chatbot_service,
            knowledge_base_repository=mock_kb_repository
        )

    @pytest.fixture
    def sample_chatbot_request(self):
        """Create sample chatbot creation request."""
        return ChatbotCreate(
            name="Test Chatbot",
            description="Test description",
            model_id=1,
            temperature=Decimal("0.7"),
            max_tokens=2048,
            top_p=Decimal("1.0"),
            system_prompt="You are a helpful assistant",
            welcome_message="Hello!",
            fallback_message="I don't understand",
            max_conversation_length=50,
            enable_function_calling=True,
            group_ids=[1, 2],
            user_ids=[1]
        )

    @pytest.fixture
    def sample_chatbot_entity(self):
        """Create sample chatbot entity."""
        return ChatbotEntity(
            id=1,
            workspace_id=1,
            name="Test Chatbot",
            description="Test description",
            model_id=1,
            temperature=Decimal("0.7"),
            max_tokens=2048,
            system_prompt="You are a helpful assistant",
            tools=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_create_chatbot_creates_default_knowledge_base(
        self,
        use_case,
        mock_chatbot_service,
        mock_kb_repository,
        sample_chatbot_request,
        sample_chatbot_entity
    ):
        """Test that creating a chatbot also creates a default knowledge base."""
        # Arrange
        creator_id = 1
        chatbot_id = 1

        # Mock chatbot service responses
        mock_chatbot_service.create_chatbot = AsyncMock(return_value=sample_chatbot_entity)
        mock_chatbot_service.get_chatbot_by_id = AsyncMock(return_value=sample_chatbot_entity)
        mock_chatbot_service.get_chatbot_model_data = AsyncMock(return_value={
            "model_id": 1,
            "model_name": "Test Model",
            "top_p": Decimal("1.0"),
            "max_conversation_length": 50,
            "enable_function_calling": True,
            "status": "active",
            "created_by": creator_id,
            "welcome_message": "Hello!",
            "fallback_message": "I don't understand"
        })
        mock_chatbot_service.get_chatbot_creator = AsyncMock(return_value=None)

        # Mock knowledge base repository
        mock_kb_repository.create = Mock(return_value=None)

        # Mock get_settings
        with patch('src.usecases.chatbot_use_cases.get_settings') as mock_settings:
            mock_settings.return_value = Mock(VECTOR_STORE_PROVIDER="chromadb")

            # Act
            result = await use_case.execute(sample_chatbot_request, creator_id)

            # Assert
            # Verify chatbot was created
            mock_chatbot_service.create_chatbot.assert_called_once()

            # Verify default knowledge base was created
            mock_kb_repository.create.assert_called_once()
            kb_call_args = mock_kb_repository.create.call_args[0][0]

            assert kb_call_args["chatbot_id"] == chatbot_id
            assert kb_call_args["name"] == "Default Knowledge Base"
            assert kb_call_args["description"] == "Default knowledge base for this chatbot"
            assert kb_call_args["vector_store_type"] == "chromadb"
            assert kb_call_args["vector_store_collection"] == f"kb_chatbot_{chatbot_id}_default"
            assert kb_call_args["is_active"] is True

            # Verify result
            assert result.id == chatbot_id
            assert result.name == "Test Chatbot"

    @pytest.mark.asyncio
    async def test_create_chatbot_continues_if_kb_creation_fails(
        self,
        use_case,
        mock_chatbot_service,
        mock_kb_repository,
        sample_chatbot_request,
        sample_chatbot_entity
    ):
        """Test that chatbot creation continues even if KB creation fails."""
        # Arrange
        creator_id = 1

        # Mock chatbot service responses
        mock_chatbot_service.create_chatbot = AsyncMock(return_value=sample_chatbot_entity)
        mock_chatbot_service.get_chatbot_by_id = AsyncMock(return_value=sample_chatbot_entity)
        mock_chatbot_service.get_chatbot_model_data = AsyncMock(return_value={
            "model_id": 1,
            "model_name": "Test Model",
            "top_p": Decimal("1.0"),
            "max_conversation_length": 50,
            "enable_function_calling": True,
            "status": "active",
            "created_by": creator_id,
            "welcome_message": "Hello!",
            "fallback_message": "I don't understand"
        })
        mock_chatbot_service.get_chatbot_creator = AsyncMock(return_value=None)

        # Mock knowledge base repository to raise exception
        mock_kb_repository.create = Mock(side_effect=Exception("KB creation failed"))

        # Mock get_settings
        with patch('src.usecases.chatbot_use_cases.get_settings') as mock_settings:
            mock_settings.return_value = Mock(VECTOR_STORE_PROVIDER="chromadb")

            # Act - should not raise exception
            result = await use_case.execute(sample_chatbot_request, creator_id)

            # Assert
            # Verify chatbot was still created successfully
            assert result.id == 1
            assert result.name == "Test Chatbot"

            # Verify KB creation was attempted
            mock_kb_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_chatbot_uses_correct_vector_store_provider(
        self,
        use_case,
        mock_chatbot_service,
        mock_kb_repository,
        sample_chatbot_request,
        sample_chatbot_entity
    ):
        """Test that KB is created with correct vector store provider from settings."""
        # Arrange
        creator_id = 1

        # Mock chatbot service responses
        mock_chatbot_service.create_chatbot = AsyncMock(return_value=sample_chatbot_entity)
        mock_chatbot_service.get_chatbot_by_id = AsyncMock(return_value=sample_chatbot_entity)
        mock_chatbot_service.get_chatbot_model_data = AsyncMock(return_value={
            "model_id": 1,
            "model_name": "Test Model",
            "top_p": Decimal("1.0"),
            "max_conversation_length": 50,
            "enable_function_calling": True,
            "status": "active",
            "created_by": creator_id,
            "welcome_message": "Hello!",
            "fallback_message": "I don't understand"
        })
        mock_chatbot_service.get_chatbot_creator = AsyncMock(return_value=None)

        # Mock knowledge base repository
        mock_kb_repository.create = Mock(return_value=None)

        # Mock get_settings with different vector store provider
        with patch('src.usecases.chatbot_use_cases.get_settings') as mock_settings:
            mock_settings.return_value = Mock(VECTOR_STORE_PROVIDER="s3")

            # Act
            await use_case.execute(sample_chatbot_request, creator_id)

            # Assert
            kb_call_args = mock_kb_repository.create.call_args[0][0]
            assert kb_call_args["vector_store_type"] == "s3"
