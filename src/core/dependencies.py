"""
Dependency injection container.

Provides dependencies for controllers and use cases following Clean Architecture.
"""

# Standard library imports
from typing import Generator, Callable

# Third-party imports
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Core dependencies
from core.config import settings
from infrastructure.postgresql.connection import get_db_session, get_sync_db_session
from infrastructure.auth.jwt_handler import JWTHandler

# Repository Interfaces
from shared.interfaces.repositories.user_repository import UserRepository
from shared.interfaces.repositories.chatbot_repository import ChatbotRepository
from shared.interfaces.repositories.conversation_repository import ConversationRepository
from shared.interfaces.repositories.message_repository import MessageRepository
from shared.interfaces.repositories.group_repository import GroupRepository
from shared.interfaces.repositories.user_group_repository import UserGroupRepository
from shared.interfaces.repositories.group_chatbot_repository import GroupChatbotRepository
from shared.interfaces.repositories.user_chatbot_repository import UserChatbotRepository
from shared.interfaces.repositories.document_repository import DocumentRepository
from shared.interfaces.repositories.connector_repository import IConnectorRepository
from shared.interfaces.repositories.user_connection_repository import IUserConnectionRepository

# Service Interfaces
from shared.interfaces.services.ai_services.knowledge_base_service import IKnowledgeBaseService
from shared.interfaces.services.ai_services.rag_service import IRAGService
from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from shared.interfaces.services.storage.file_storage_service import IFileStorageService
from shared.interfaces.services.upload.document_upload_service import IDocumentUploadService
from shared.interfaces.services.security.encryption_service import IEncryptionService
from shared.interfaces.services.external.gitlab_service import IGitLabService
from shared.interfaces.repositories.ai_model_repository import AiModelRepository

# Repository Implementations
from infrastructure.postgresql.repositories import (
    UserRepositoryImpl,
    ChatbotRepositoryImpl,
    ConversationRepositoryImpl,
    MessageRepositoryImpl,
    GroupRepositoryImpl,
    UserGroupRepositoryImpl,
    GroupChatbotRepositoryImpl,
    UserChatbotRepositoryImpl,
    DocumentRepositoryImpl,
    AiModelRepositoryImpl
)
from infrastructure.postgresql.repositories.connector_repository import ConnectorRepository
from infrastructure.postgresql.repositories.user_connection_repository import UserConnectionRepository
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository

# Service Implementations
# Services
from application.services.auth_service import AuthService
from application.services.user_service import UserService
from application.services.chatbot_service import ChatbotService
from application.services.conversation_service import ConversationService
from application.services.vector_store_service import VectorStoreService
from application.services.rag_service import RAGService
from application.services.document_upload_service import DocumentUploadService
from application.services.document_processing_service import DocumentProcessingService
from application.services.document_chunking_service import DocumentChunkingService
from application.services.gitlab_sync_service import GitLabSyncService
from application.services.kb_sync_service import KBSyncService
from application.services.connector_service import ConnectorService

# Infrastructure Services
from infrastructure.vector_store.factory import VectorStoreFactory
from infrastructure.ai_services.bedrock_client import BedrockClient, get_bedrock_client as _create_bedrock_client
from infrastructure.ai_services.knowledge_base.bedrock_kb import BedrockKnowledgeBaseService
from infrastructure.ai_services.embeddings.factory import EmbeddingFactory
from infrastructure.ai_services.llm.factory import LLMFactory
from infrastructure.s3.s3_file_storage_service import S3FileStorageService
from infrastructure.security.encryption_service import EncryptionService
from infrastructure.external.gitlab_service import GitLabService
from application.services.ai_model_service import AiModelService

# Use Cases
from src.application.services.group_service import GroupService
from usecases.auth_use_cases import LoginUseCase, RegisterUseCase
from usecases.user_use_cases import (
    GetCurrentUserUseCase,
    ListUsersUseCase,
    GetUserUseCase,
    CreateUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    UpdateOwnProfileUseCase,
    ChangePasswordUseCase
)
from usecases.group_use_cases import (
    ListGroupsUseCase,
    GetGroupUseCase,
    CreateGroupUseCase,
    UpdateGroupUseCase,
    DeleteGroupUseCase
)
from usecases.chatbot_use_cases import (
    ListChatbotsUseCase,
    GetChatbotUseCase,
    CreateChatbotUseCase,
    UpdateChatbotUseCase,
    DeleteChatbotUseCase
)
from usecases.ai_model_use_cases import (
    ListAiModelsUseCase,
    GetAiModelUseCase,
    CreateAiModelUseCase,
    UpdateAiModelUseCase,
    DeleteAiModelUseCase
)
from usecases.conversation_use_cases import (
    ListConversationsUseCase,
    GetConversationUseCase,
    CreateConversationUseCase,
    CreateMessageUseCase,
    DeleteConversationUseCase
)
from usecases.document_use_cases import (
    UploadDocumentUseCase,
    DeleteDocumentUseCase,
    ListUserDocumentsUseCase,
    ProcessDocumentUseCase,
    GetDocumentStatusUseCase
)
from usecases.rag_use_cases import (
    ChatWithDocumentsUseCase,
    SemanticSearchUseCase,
    RetrieveContextsUseCase
)
from usecases.connector_use_cases import (
    ListConnectorsUseCase,
    GetConnectorUseCase,
    SetupGitLabConnectorUseCase,
    UpdateConnectorCredentialsUseCase,
    DeleteConnectorUseCase
)
from usecases.gitlab_use_cases import (
    TestGitLabConnectionUseCase,
    FetchGitLabRepositoriesUseCase,
    SyncRepositoryUseCase
)

# Schemas
from schemas.user_schema import UserResponse

# Domain Entities
from domain.entities.user import UserEntity

# Security
security = HTTPBearer()


# ============================================================================
# DATABASE DEPENDENCIES
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """Get synchronous database session for connector management."""
    yield from get_sync_db_session()


# ============================================================================
# INFRASTRUCTURE DEPENDENCIES
# ============================================================================

def get_jwt_handler() -> JWTHandler:
    """Get JWT handler instance."""
    return JWTHandler()


def get_bedrock_client() -> BedrockClient:
    """Get Bedrock client instance."""
    return _create_bedrock_client()


def get_vector_store_service() -> VectorStoreService:
    """Get vector store service instance."""
    vector_store_instance = VectorStoreFactory.create()
    return VectorStoreService(vector_store_instance)


def get_file_storage_service() -> IFileStorageService:
    """Get file storage service instance."""
    return S3FileStorageService()


def get_encryption_service() -> IEncryptionService:
    """Get encryption service instance."""
    return EncryptionService()


def get_gitlab_service_factory() -> Callable[[str, str], IGitLabService]:
    """Get GitLab service factory function."""
    def factory(gitlab_url: str, private_token: str) -> IGitLabService:
        return GitLabService(gitlab_url, private_token)
    return factory


# ============================================================================
# REPOSITORY DEPENDENCIES
# ============================================================================

def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Get user repository instance."""
    return UserRepositoryImpl(session)


def get_chatbot_repository(session: AsyncSession = Depends(get_db_session)) -> ChatbotRepository:
    """Get chatbot repository instance."""
    return ChatbotRepositoryImpl(session)


def get_conversation_repository(session: AsyncSession = Depends(get_db_session)) -> ConversationRepository:
    """Get conversation repository instance."""
    return ConversationRepositoryImpl(session)


def get_message_repository(session: AsyncSession = Depends(get_db_session)) -> MessageRepository:
    """Get message repository instance."""
    return MessageRepositoryImpl(session)


def get_group_repository(session: AsyncSession = Depends(get_db_session)) -> GroupRepository:
    """Get group repository instance."""
    return GroupRepositoryImpl(session)


def get_user_group_repository(session: AsyncSession = Depends(get_db_session)) -> UserGroupRepository:
    """Get user-group repository instance."""
    return UserGroupRepositoryImpl(session)


def get_group_chatbot_repository(session: AsyncSession = Depends(get_db_session)) -> GroupChatbotRepository:
    """Get group-chatbot repository instance."""
    return GroupChatbotRepositoryImpl(session)


def get_user_chatbot_repository(session: AsyncSession = Depends(get_db_session)) -> UserChatbotRepository:
    """Get user-chatbot repository instance."""
    return UserChatbotRepositoryImpl(session)


def get_document_repository(session: AsyncSession = Depends(get_db_session)) -> DocumentRepository:
    """Get document repository instance."""
    return DocumentRepositoryImpl(session)


def get_connector_repository(db_session: Session = Depends(get_db)) -> IConnectorRepository:
    """Get connector repository instance."""
    return ConnectorRepository(db_session)


def get_user_connection_repository(db_session: Session = Depends(get_db)) -> IUserConnectionRepository:
    """Get user connection repository instance."""
    return UserConnectionRepository(db_session)

def get_ai_model_repository(
    session: AsyncSession = Depends(get_db_session)
) -> AiModelRepository:
    """Get AI model repository instance."""
    return AiModelRepositoryImpl(session)


# ============================================================================
# AI SERVICE DEPENDENCIES
# ============================================================================

def get_knowledge_base_service(bedrock_client: BedrockClient = Depends(get_bedrock_client)) -> IKnowledgeBaseService:
    """Get Knowledge Base service instance."""
    return BedrockKnowledgeBaseService(bedrock_client)


def get_embedding_service() -> IEmbeddingService:
    """Get embedding service instance based on LLM_PROVIDER."""
    provider = getattr(settings, "LLM_PROVIDER", "gemini")
    model_id = getattr(settings, "EMBEDDING_MODEL", None)
    return EmbeddingFactory.create(model_id=model_id)


def get_rag_service(knowledge_base_service: IKnowledgeBaseService = Depends(get_knowledge_base_service)) -> IRAGService:
    """Get RAG service instance with direct LLM provider."""
    llm_provider = LLMFactory.create()
    return RAGService(knowledge_base_service, llm_provider)


# ============================================================================
# APPLICATION SERVICE DEPENDENCIES
# ============================================================================

# Service dependencies (use interfaces)
def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> AuthService:
    """Get auth service instance."""
    return AuthService(user_repository, jwt_handler)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    group_repository: GroupRepository = Depends(get_group_repository),
    user_group_repository: UserGroupRepository = Depends(get_user_group_repository),
    group_chatbot_repository: GroupChatbotRepository = Depends(get_group_chatbot_repository),
    user_chatbot_repository: UserChatbotRepository = Depends(get_user_chatbot_repository),
) -> UserService:
    """Get user service instance."""
    return UserService(
        user_repository,
        user_group_repository,
        group_repository,
        group_chatbot_repository,
        user_chatbot_repository
    )


def get_group_service(
    group_repository: GroupRepository = Depends(get_group_repository),
    user_group_repository: UserGroupRepository = Depends(get_user_group_repository)
) -> GroupService:
    """Get group service instance."""
    return GroupService(group_repository, user_group_repository)


def get_chatbot_service(
    chatbot_repository: ChatbotRepository = Depends(get_chatbot_repository),
    group_chatbot_repository: GroupChatbotRepository = Depends(get_group_chatbot_repository),
    user_chatbot_repository: UserChatbotRepository = Depends(get_user_chatbot_repository),
    group_repository: GroupRepository = Depends(get_group_repository),
    user_repository: UserRepository = Depends(get_user_repository)
) -> ChatbotService:
    """Get chatbot service instance."""
    return ChatbotService(
        chatbot_repository,
        group_chatbot_repository,
        user_chatbot_repository,
        group_repository,
        user_repository
    )


def get_conversation_service(
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    message_repository: MessageRepository = Depends(get_message_repository)
) -> ConversationService:
    """Get conversation service instance."""
    return ConversationService(conversation_repository, message_repository)


def get_document_upload_service(
    file_storage: IFileStorageService = Depends(get_file_storage_service),
    document_repository: DocumentRepository = Depends(get_document_repository)
) -> IDocumentUploadService:
    """Get document upload service instance."""
    return DocumentUploadService(file_storage, document_repository)


def get_document_processing_service() -> DocumentProcessingService:
    """Get document processing service instance."""
    return DocumentProcessingService()


def get_document_chunking_service() -> DocumentChunkingService:
    """Get document chunking service instance."""
    chunk_size = int(getattr(settings, "CHUNK_SIZE", 1000))
    chunk_overlap = int(getattr(settings, "CHUNK_OVERLAP", 200))
    max_chunks = int(getattr(settings, "MAX_CHUNKS_PER_DOCUMENT", 500))
    return DocumentChunkingService(chunk_size, chunk_overlap, max_chunks)


def get_kb_sync_service(
    embedding_service: IEmbeddingService = Depends(get_embedding_service),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
    document_repository: DocumentRepository = Depends(get_document_repository)
) -> KBSyncService:
    """Get KB sync service instance."""
    return KBSyncService(
        embedding_service,
        vector_store_service.vector_store,
        document_repository
    )

def get_gitlab_sync_service(
    kb_sync_service: KBSyncService = Depends(get_kb_sync_service)
) -> GitLabSyncService:
    """Get GitLab sync service instance."""
    return GitLabSyncService(kb_sync_service=kb_sync_service)


def get_connector_service(
    connector_repository: IConnectorRepository = Depends(get_connector_repository),
    user_connection_repository: IUserConnectionRepository = Depends(get_user_connection_repository),
    encryption_service: IEncryptionService = Depends(get_encryption_service),
    gitlab_service_factory: Callable[[str, str], IGitLabService] = Depends(get_gitlab_service_factory)
) -> ConnectorService:
    """Get connector service instance with proper dependencies."""
    return ConnectorService(
        connector_repository=connector_repository,
        user_connection_repository=user_connection_repository,
        encryption_service=encryption_service,
        gitlab_service_factory=gitlab_service_factory
    )

def get_ai_model_service(
    ai_model_repository: AiModelRepository = Depends(get_ai_model_repository)
) -> AiModelService:
    """Get AI model service instance."""
    return AiModelService(ai_model_repository)

# ============================================================================
# AUTH USE CASE DEPENDENCIES
# ============================================================================

# Auth use cases
def get_login_use_case(
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginUseCase:
    """Get login use case instance."""
    return LoginUseCase(auth_service)


def get_register_use_case(auth_service: AuthService = Depends(get_auth_service)) -> RegisterUseCase:
    """Get register use case instance."""
    return RegisterUseCase(auth_service)


# ============================================================================
# USER USE CASE DEPENDENCIES
# ============================================================================

def get_current_user_use_case(user_service: UserService = Depends(get_user_service)) -> GetCurrentUserUseCase:
    """Get current user use case instance."""
    return GetCurrentUserUseCase(user_service)


def get_list_users_use_case(user_service: UserService = Depends(get_user_service)) -> ListUsersUseCase:
    """Get list users use case instance."""
    return ListUsersUseCase(user_service)


def get_user_use_case(user_service: UserService = Depends(get_user_service)) -> GetUserUseCase:
    """Get user use case instance."""
    return GetUserUseCase(user_service)


def get_create_user_use_case(user_service: UserService = Depends(get_user_service)) -> CreateUserUseCase:
    """Get create user use case instance."""
    return CreateUserUseCase(user_service)


def get_update_user_use_case(user_service: UserService = Depends(get_user_service)) -> UpdateUserUseCase:
    """Get update user use case instance."""
    return UpdateUserUseCase(user_service)


def get_delete_user_use_case(user_service: UserService = Depends(get_user_service)) -> DeleteUserUseCase:
    """Get delete user use case instance."""
    return DeleteUserUseCase(user_service)


# ============================================================================
# GROUP USE CASE DEPENDENCIES
# ============================================================================

def get_update_own_profile_use_case(
    user_service: UserService = Depends(get_user_service)
) -> UpdateOwnProfileUseCase:
    """Get update own profile use case instance."""
    return UpdateOwnProfileUseCase(user_service)


def get_change_password_use_case(
    user_service: UserService = Depends(get_user_service)
) -> ChangePasswordUseCase:
    """Get change password use case instance."""
    return ChangePasswordUseCase(user_service)


# Group use cases
def get_list_groups_use_case(
    group_service: GroupService = Depends(get_group_service)
) -> ListGroupsUseCase:
    """Get list groups use case instance."""
    return ListGroupsUseCase(group_service)


def get_group_use_case(group_service: GroupService = Depends(get_group_service)) -> GetGroupUseCase:
    """Get group use case instance."""
    return GetGroupUseCase(group_service)


def get_create_group_use_case(group_service: GroupService = Depends(get_group_service)) -> CreateGroupUseCase:
    """Get create group use case instance."""
    return CreateGroupUseCase(group_service)


def get_update_group_use_case(group_service: GroupService = Depends(get_group_service)) -> UpdateGroupUseCase:
    """Get update group use case instance."""
    return UpdateGroupUseCase(group_service)


def get_delete_group_use_case(group_service: GroupService = Depends(get_group_service)) -> DeleteGroupUseCase:
    """Get delete group use case instance."""
    return DeleteGroupUseCase(group_service)


# ============================================================================
# CHATBOT USE CASE DEPENDENCIES
# ============================================================================

# AI Model use cases
def get_list_ai_models_use_case(
    ai_model_service: AiModelService = Depends(get_ai_model_service)
) -> ListAiModelsUseCase:
    """Get list AI models use case instance."""
    return ListAiModelsUseCase(ai_model_service)


def get_ai_model_use_case(
    ai_model_service: AiModelService = Depends(get_ai_model_service)
) -> GetAiModelUseCase:
    """Get AI model use case instance."""
    return GetAiModelUseCase(ai_model_service)


def get_create_ai_model_use_case(
    ai_model_service: AiModelService = Depends(get_ai_model_service)
) -> CreateAiModelUseCase:
    """Get create AI model use case instance."""
    return CreateAiModelUseCase(ai_model_service)


def get_update_ai_model_use_case(
    ai_model_service: AiModelService = Depends(get_ai_model_service)
) -> UpdateAiModelUseCase:
    """Get update AI model use case instance."""
    return UpdateAiModelUseCase(ai_model_service)


def get_delete_ai_model_use_case(
    ai_model_service: AiModelService = Depends(get_ai_model_service)
) -> DeleteAiModelUseCase:
    """Get delete AI model use case instance."""
    return DeleteAiModelUseCase(ai_model_service)


# Chatbot use cases
def get_list_chatbots_use_case(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
) -> ListChatbotsUseCase:
    """Get list chatbots use case instance."""
    return ListChatbotsUseCase(chatbot_service)


def get_chatbot_use_case(chatbot_service: ChatbotService = Depends(get_chatbot_service)) -> GetChatbotUseCase:
    """Get chatbot use case instance."""
    return GetChatbotUseCase(chatbot_service)


def get_create_chatbot_use_case(chatbot_service: ChatbotService = Depends(get_chatbot_service)) -> CreateChatbotUseCase:
    """Get create chatbot use case instance."""
    return CreateChatbotUseCase(chatbot_service)


def get_update_chatbot_use_case(chatbot_service: ChatbotService = Depends(get_chatbot_service)) -> UpdateChatbotUseCase:
    """Get update chatbot use case instance."""
    return UpdateChatbotUseCase(chatbot_service)


def get_delete_chatbot_use_case(chatbot_service: ChatbotService = Depends(get_chatbot_service)) -> DeleteChatbotUseCase:
    """Get delete chatbot use case instance."""
    return DeleteChatbotUseCase(chatbot_service)


# ============================================================================
# CONVERSATION USE CASE DEPENDENCIES
# ============================================================================

def get_list_conversations_use_case(conversation_service: ConversationService = Depends(get_conversation_service)) -> ListConversationsUseCase:
    """Get list conversations use case instance."""
    return ListConversationsUseCase(conversation_service)


def get_conversation_use_case(conversation_service: ConversationService = Depends(get_conversation_service)) -> GetConversationUseCase:
    """Get conversation use case instance."""
    return GetConversationUseCase(conversation_service)


def get_create_conversation_use_case(conversation_service: ConversationService = Depends(get_conversation_service)) -> CreateConversationUseCase:
    """Get create conversation use case instance."""
    return CreateConversationUseCase(conversation_service)


def get_create_message_use_case(
    conversation_service: ConversationService = Depends(get_conversation_service),
    rag_service: IRAGService = Depends(get_rag_service),
    chatbot_repository: ChatbotRepository = Depends(get_chatbot_repository)
) -> CreateMessageUseCase:
    """Get create message use case instance with RAG integration."""
    return CreateMessageUseCase(
        conversation_service,
        rag_service,
        chatbot_repository,
        domain="general"  # Default domain, can be made configurable
    )


def get_delete_conversation_use_case(conversation_service: ConversationService = Depends(get_conversation_service)) -> DeleteConversationUseCase:
    """Get delete conversation use case instance."""
    return DeleteConversationUseCase(conversation_service)

# ============================================================================
# DOCUMENT USE CASE DEPENDENCIES
# ============================================================================

def get_upload_document_use_case(upload_service: IDocumentUploadService = Depends(get_document_upload_service)) -> UploadDocumentUseCase:
    """Get upload document use case."""
    return UploadDocumentUseCase(upload_service)


def get_delete_document_use_case(upload_service: IDocumentUploadService = Depends(get_document_upload_service)) -> DeleteDocumentUseCase:
    """Get delete document use case."""
    return DeleteDocumentUseCase(upload_service)


def get_list_user_documents_use_case(document_repository: DocumentRepository = Depends(get_document_repository)) -> ListUserDocumentsUseCase:
    """Get list user documents use case."""
    return ListUserDocumentsUseCase(document_repository)


def get_process_document_use_case(
    document_repository: DocumentRepository = Depends(get_document_repository),
    file_storage_service: IFileStorageService = Depends(get_file_storage_service),
    processing_service: DocumentProcessingService = Depends(get_document_processing_service),
    chunking_service: DocumentChunkingService = Depends(get_document_chunking_service),
    kb_sync_service: KBSyncService = Depends(get_kb_sync_service)
) -> ProcessDocumentUseCase:
    """Get process document use case."""
    # Get KB configuration from settings
    kb_config = {
        "healthcare": getattr(settings, "KNOWLEDGE_BASE_HEALTHCARE_ID", "kb_healthcare"),
        "finance": getattr(settings, "KNOWLEDGE_BASE_FINANCE_ID", "kb_finance"),
        "general": getattr(settings, "KNOWLEDGE_BASE_GENERAL_ID", "kb_general")
    }

    return ProcessDocumentUseCase(
        document_repository,
        file_storage_service,
        processing_service,
        chunking_service,
        kb_sync_service,
        kb_config
    )


def get_document_status_use_case(document_repository: DocumentRepository = Depends(get_document_repository)) -> GetDocumentStatusUseCase:
    """Get document status use case."""
    return GetDocumentStatusUseCase(document_repository)


# ============================================================================
# RAG USE CASE DEPENDENCIES
# ============================================================================

def get_chat_with_documents_use_case(rag_service: IRAGService = Depends(get_rag_service)) -> ChatWithDocumentsUseCase:
    """Get chat with documents use case."""
    return ChatWithDocumentsUseCase(rag_service)


def get_semantic_search_use_case(rag_service: IRAGService = Depends(get_rag_service)) -> SemanticSearchUseCase:
    """Get semantic search use case."""
    return SemanticSearchUseCase(rag_service)


def get_retrieve_contexts_use_case(rag_service: IRAGService = Depends(get_rag_service)) -> RetrieveContextsUseCase:
    """Get retrieve contexts use case."""
    return RetrieveContextsUseCase(rag_service)


# ============================================================================
# CONNECTOR USE CASE DEPENDENCIES
# ============================================================================

def get_list_connectors_use_case(connector_service: ConnectorService = Depends(get_connector_service)) -> ListConnectorsUseCase:
    """Get list connectors use case."""
    return ListConnectorsUseCase(connector_service)


def get_get_connector_use_case(connector_service: ConnectorService = Depends(get_connector_service)) -> GetConnectorUseCase:
    """Get connector use case."""
    return GetConnectorUseCase(connector_service)


def get_setup_gitlab_connector_use_case(connector_service: ConnectorService = Depends(get_connector_service)) -> SetupGitLabConnectorUseCase:
    """Get setup GitLab connector use case."""
    return SetupGitLabConnectorUseCase(connector_service)


def get_update_connector_credentials_use_case(connector_service: ConnectorService = Depends(get_connector_service)) -> UpdateConnectorCredentialsUseCase:
    """Get update connector credentials use case."""
    return UpdateConnectorCredentialsUseCase(connector_service)


def get_delete_connector_use_case(connector_service: ConnectorService = Depends(get_connector_service)) -> DeleteConnectorUseCase:
    """Get delete connector use case."""
    return DeleteConnectorUseCase(connector_service)


# ============================================================================
# GITLAB USE CASE DEPENDENCIES  
# ============================================================================

def get_test_gitlab_connection_use_case(connector_service: ConnectorService = Depends(get_connector_service)) -> TestGitLabConnectionUseCase:
    """Get test GitLab connection use case."""
    return TestGitLabConnectionUseCase(connector_service)


def get_fetch_gitlab_repositories_use_case(connector_service: ConnectorService = Depends(get_connector_service)) -> FetchGitLabRepositoriesUseCase:
    """Get fetch GitLab repositories use case."""
    return FetchGitLabRepositoriesUseCase(connector_service)


def get_sync_repository_use_case(
    connector_service: ConnectorService = Depends(get_connector_service),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service),
    async_session: AsyncSession = Depends(get_db_session),
    sync_session: Session = Depends(get_db)
) -> SyncRepositoryUseCase:
    """Get sync repository use case."""
    repository_repository = RepositoryRepository(sync_session)
    
    return SyncRepositoryUseCase(
        connector_service=connector_service,
        gitlab_sync_service=gitlab_sync_service,
        repository_repository=repository_repository,
        async_session=async_session
    )


# ============================================================================
# AUTHENTICATION & AUTHORIZATION  
# ============================================================================

# Note: Authentication functions are handled directly by middleware.
# Use `get_current_user` for user authentication.
# Use `require_admin` for admin authentication.
# Import them directly from api.middlewares.jwt_middleware as needed.
