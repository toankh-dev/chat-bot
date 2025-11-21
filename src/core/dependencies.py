"""
Dependency injection container.

Provides dependencies for controllers and use cases following Clean Architecture.
"""

# Standard library imports
from typing import Generator, Callable, Optional

# Third-party imports
from fastapi import Depends
from fastapi.security import HTTPBearer
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
from shared.interfaces.repositories.ai_model_repository import AiModelRepository

# Service Interfaces
from shared.interfaces.services.ai_services.knowledge_base_service import IKnowledgeBaseService
from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from shared.interfaces.services.storage.file_storage_service import IFileStorageService
from shared.interfaces.services.upload.document_upload_service import IDocumentUploadService
from shared.interfaces.services.security.encryption_service import IEncryptionService
from shared.interfaces.services.external.gitlab_service import IGitLabService
from shared.interfaces.services.lock.redis_lock_service import IRedisLockService


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
from infrastructure.postgresql.repositories.commit_model_repository import CommitRepository
from infrastructure.postgresql.repositories.sync_queue_repository import SyncQueueRepository
from infrastructure.postgresql.repositories.sync_history_repository import SyncHistoryRepository
from infrastructure.postgresql.repositories.knowledge_base_repository import KnowledgeBaseRepository
from infrastructure.postgresql.repositories.knowledge_base_source_repository import KnowledgeBaseSourceRepository

# Service Implementations
# Services
from application.services.auth_service import AuthService
from application.services.user_service import UserService
from application.services.chatbot_service import ChatbotService
from application.services.conversation_service import ConversationService
from application.services.document_upload_service import DocumentUploadService
from application.services.document_processing_service import DocumentProcessingService
from application.services.document_chunking_service import DocumentChunkingService
from application.services.gitlab_sync_service import GitLabSyncService
from application.services.kb_sync_service import KBSyncService
from application.services.connector_service import ConnectorService
from application.services.code_chunking_service import CodeChunkingService
from application.services.group_service import GroupService
from application.services.agent_service import AgentService
from application.services.rag_service import RAGService

# Infrastructure Services
from infrastructure.vector_store.factory import VectorStoreFactory
from infrastructure.ai_services.bedrock_client import BedrockClient, get_bedrock_client as _create_bedrock_client
from infrastructure.ai_services.embeddings.factory import EmbeddingFactory
from infrastructure.s3.s3_file_storage_service import S3FileStorageService
from infrastructure.security.encryption_service import EncryptionService
from infrastructure.external.gitlab_service import GitLabService
from application.services.ai_model_service import AiModelService
from infrastructure.lock.redis_lock_service import RedisLockService

# Use Cases
from usecases.auth_use_cases import LoginUseCase, RegisterUseCase, RefreshTokenUseCase
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
from usecases.document_use_cases import (
    UploadDocumentUseCase,
    DeleteDocumentUseCase,
    ListUserDocumentsUseCase,
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
    FetchGitLabBranchesUseCase,
    SyncRepositoryUseCase
)

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

def get_vector_store_factory():
    """Get vector store factory instance."""
    return VectorStoreFactory()

def get_embedding_factory():
    """Get vector store factory instance."""
    return EmbeddingFactory()


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

def get_repository_repository(db_session: Session = Depends(get_db)) -> RepositoryRepository:
    """Get repository repository instance (SYNC)."""
    return RepositoryRepository(db_session)

def get_commit_repository(db_session: Session = Depends(get_db_session)) -> CommitRepository:
    """Get commit repository instance (SYNC)."""
    return CommitRepository(db_session)

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


# SYNC Repositories for GitLab operations
def get_sync_queue_repository(db_session: Session = Depends(get_db)) -> SyncQueueRepository:
    """Get sync queue repository instance (SYNC)."""
    return SyncQueueRepository(db_session)


def get_knowledge_base_sync_repository(db_session: AsyncSession = Depends(get_db_session)) -> KnowledgeBaseRepository:
    """Get knowledge base repository instance (uses AsyncSession to share transaction with chatbot_service)."""
    return KnowledgeBaseRepository(db_session)


def get_kb_source_sync_repository(db_session: Session = Depends(get_db)) -> KnowledgeBaseSourceRepository:
    """Get knowledge base source repository instance (SYNC)."""
    return KnowledgeBaseSourceRepository(db_session)


def get_sync_history_repository(db_session: Session = Depends(get_db)) -> SyncHistoryRepository:
    """Get sync history repository instance (SYNC)."""
    return SyncHistoryRepository(db_session)

def get_knowledge_base_repository(db_session: Session = Depends(get_db)) -> KnowledgeBaseRepository:
    """Get sync knowledge base repository instance (SYNC)."""
    return KnowledgeBaseRepository(db_session)

def get_kb_source_repository(db_session: Session = Depends(get_db)) -> KnowledgeBaseSourceRepository:
    """Get sync knowledge base source repository instance (SYNC)."""
    return KnowledgeBaseSourceRepository(db_session)


# ============================================================================
# AI SERVICE DEPENDENCIES
# ============================================================================


def get_embedding_service() -> IEmbeddingService:
    """Get embedding service instance based on LLM_PROVIDER."""
    model_id = getattr(settings, "EMBEDDING_MODEL", None)
    return EmbeddingFactory.create(provider="gemini", config={"model_name": model_id})

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

def get_code_chunking_service() -> CodeChunkingService:
    """Get AI model service instance."""
    return CodeChunkingService()

def get_kb_sync_service(
    embedding_service: IEmbeddingService = Depends(get_embedding_service),
    vector_store_factory = Depends(get_vector_store_factory),
    document_repository: DocumentRepository = Depends(get_document_repository)
) -> KBSyncService:
    """Get KB sync service instance."""
    return KBSyncService(
        embedding_service,
        vector_store_factory,
        document_repository
    )


def get_kb_cleanup_service(
    kb_repo = Depends(get_knowledge_base_repository),
    kb_source_repo = Depends(get_kb_source_repository),
    vector_store_factory = Depends(get_vector_store_factory)
):
    """
    Get KB Cleanup Service instance (Phase 3.5).
    """
    from src.application.services.kb_cleanup_service import KBCleanupService

    return KBCleanupService(
        kb_repo=kb_repo,
        kb_source_repo=kb_source_repo,
        vector_store_factory=vector_store_factory
    )


def get_kb_cleanup_service_sync():
    """
    Get KB Cleanup Service instance with SYNC repositories for SQLAlchemy event listeners.

    This factory creates a cleanup service that can be used in synchronous contexts
    like SQLAlchemy 'before_delete' event handlers.

    Returns:
        KBCleanupService with sync repositories
    """
    from src.application.services.kb_cleanup_service import KBCleanupService
    from infrastructure.postgresql.connection.database import DatabaseManager

    # Get sync session
    db_manager = DatabaseManager()
    sync_session = db_manager.get_sync_session()

    # Create sync repositories
    kb_repo = get_knowledge_base_sync_repository_direct(sync_session)
    kb_source_repo = get_kb_source_repository_direct(sync_session)

    # Get vector store factory (stateless, can be shared)
    vector_factory = VectorStoreFactory()

    return KBCleanupService(
        kb_repo=kb_repo,
        kb_source_repo=kb_source_repo,
        vector_store_factory=vector_factory
    )


def get_knowledge_base_sync_repository_direct(session):
    """Direct factory for sync KB repository (for event listeners)."""
    from infrastructure.postgresql.repositories.knowledge_base_repository import KnowledgeBaseRepository
    return KnowledgeBaseRepository(session)


def get_kb_source_repository_direct(session):
    """Direct factory for sync KB source repository (for event listeners)."""
    from infrastructure.postgresql.repositories.knowledge_base_source_repository import KnowledgeBaseSourceRepository
    return KnowledgeBaseSourceRepository(session)


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

def get_redis_lock_service():
    """
    Get Redis lock service instance (singleton pattern).

    Returns:
        RedisLockService: Distributed lock service using Redis

    Raises:
        redis.exceptions.ConnectionError: If cannot connect to Redis server
    """
    return RedisLockService()

def get_gitlab_sync_service(
    # 9 Repository dependencies (all SYNC)
    repository_repository: RepositoryRepository = Depends(get_repository_repository),
    commit_repository: CommitRepository = Depends(get_commit_repository),
    sync_queue_repository: SyncQueueRepository = Depends(get_sync_queue_repository),
    sync_history_repository: SyncHistoryRepository = Depends(get_sync_history_repository),
    connector_repository: ConnectorRepository = Depends(get_connector_repository),
    user_connection_repository: UserConnectionRepository = Depends(get_user_connection_repository),
    knowledge_base_repository: KnowledgeBaseRepository = Depends(get_knowledge_base_sync_repository),
    kb_source_repository: KnowledgeBaseSourceRepository = Depends(get_kb_source_sync_repository),
    # 4 Service dependencies (added kb_cleanup_service in Phase 3.5)
    code_chunking_service: CodeChunkingService = Depends(get_code_chunking_service),
    kb_sync_service: KBSyncService = Depends(get_kb_sync_service),
    connector_service: ConnectorService = Depends(get_connector_service),
    kb_cleanup_service = Depends(get_kb_cleanup_service),
    redis_lock_service:IRedisLockService = Depends(get_redis_lock_service)
) -> GitLabSyncService:
    """
    Get GitLab sync service instance with all repository and service dependencies.
    """
    return GitLabSyncService(
        repository_repository=repository_repository,
        commit_repository=commit_repository,
        sync_queue_repository=sync_queue_repository,
        sync_history_repository=sync_history_repository,
        connector_repository=connector_repository,
        user_connection_repository=user_connection_repository,
        knowledge_base_repository=knowledge_base_repository,
        kb_source_repository=kb_source_repository,
        kb_sync_service=kb_sync_service,
        code_chunking_service=code_chunking_service,
        connector_service=connector_service,
        kb_cleanup_service=kb_cleanup_service,
        redis_lock_service=redis_lock_service
    )

def get_document_processing_service() -> DocumentProcessingService:
    """Get document processing service instance."""
    return DocumentProcessingService()


def get_document_chunking_service() -> DocumentChunkingService:
    """Get document chunking service instance."""
    chunk_size = int(getattr(settings, "CHUNK_SIZE", 1000))
    chunk_overlap = int(getattr(settings, "CHUNK_OVERLAP", 200))
    max_chunks = int(getattr(settings, "MAX_CHUNKS_PER_DOCUMENT", 500))
    return DocumentChunkingService(chunk_size, chunk_overlap, max_chunks)


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

def get_login_use_case(
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginUseCase:
    """Get login use case instance."""
    return LoginUseCase(auth_service)


def get_register_use_case(auth_service: AuthService = Depends(get_auth_service)) -> RegisterUseCase:
    """Get register use case instance."""
    return RegisterUseCase(auth_service)


def get_refresh_token_use_case(
    auth_service: AuthService = Depends(get_auth_service)
) -> RefreshTokenUseCase:
    """Get refresh token use case instance."""
    return RefreshTokenUseCase(auth_service)


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


def get_create_chatbot_use_case(
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
    knowledge_base_repository: KnowledgeBaseRepository = Depends(get_knowledge_base_sync_repository)
) -> CreateChatbotUseCase:
    """Get create chatbot use case instance."""
    return CreateChatbotUseCase(chatbot_service, knowledge_base_repository)


def get_update_chatbot_use_case(chatbot_service: ChatbotService = Depends(get_chatbot_service)) -> UpdateChatbotUseCase:
    """Get update chatbot use case instance."""
    return UpdateChatbotUseCase(chatbot_service)


def get_delete_chatbot_use_case(chatbot_service: ChatbotService = Depends(get_chatbot_service)) -> DeleteChatbotUseCase:
    """Get delete chatbot use case instance."""
    return DeleteChatbotUseCase(chatbot_service)

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


def get_fetch_gitlab_branches_use_case(connector_service: ConnectorService = Depends(get_connector_service)) -> FetchGitLabBranchesUseCase:
    """Get fetch GitLab branches use case."""
    return FetchGitLabBranchesUseCase(connector_service)


def get_sync_repository_use_case(
    connector_service: ConnectorService = Depends(get_connector_service),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service),
) -> SyncRepositoryUseCase:
    """Get sync repository use case."""
    return SyncRepositoryUseCase(
        connector_service=connector_service,
        gitlab_sync_service=gitlab_sync_service,
    )
