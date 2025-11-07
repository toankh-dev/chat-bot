"""
Dependency injection container.

Provides dependencies for controllers and use cases following Clean Architecture.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.postgresql.connection import get_db_session
from infrastructure.auth.jwt_handler import JWTHandler
from core.config import settings

# Vector Store & RAG dependencies
from infrastructure.vector_store.factory import VectorStoreFactory
from application.services.vector_store_service import VectorStoreService
from infrastructure.ai_services.providers.bedrock import BedrockClient
from infrastructure.ai_services.services.knowledge_base import BedrockKnowledgeBaseService
from application.services.rag_service import RAGService
from shared.interfaces.services.ai_services.knowledge_base_service import IKnowledgeBaseService
from shared.interfaces.services.ai_services.rag_service import IRAGService



# Repository Interfaces
from shared.interfaces.repositories.user_repository import UserRepository
from shared.interfaces.repositories.chatbot_repository import ChatbotRepository
from shared.interfaces.repositories.conversation_repository import ConversationRepository
from shared.interfaces.repositories.message_repository import MessageRepository
from shared.interfaces.repositories.group_repository import GroupRepository
from shared.interfaces.repositories.user_group_repository import UserGroupRepository
from shared.interfaces.repositories.group_chatbot_repository import GroupChatbotRepository
from shared.interfaces.repositories.user_chatbot_repository import UserChatbotRepository

# Repository Implementations
from infrastructure.postgresql.repositories import (
    UserRepositoryImpl,
    ChatbotRepositoryImpl,
    ConversationRepositoryImpl,
    MessageRepositoryImpl,
    GroupRepositoryImpl,
    UserGroupRepositoryImpl,
    GroupChatbotRepositoryImpl,
    UserChatbotRepositoryImpl
)

# Services
from application.services.auth_service import AuthService
from application.services.user_service import UserService
from application.services.chatbot_service import ChatbotService
from application.services.conversation_service import ConversationService
from application.services.auth_service import AuthService
from application.services.user_service import UserService
from application.services.group_service import GroupService
from application.services.chatbot_service import ChatbotService
from application.services.conversation_service import ConversationService

# Use Cases
from usecases.auth_use_cases import LoginUseCase, RegisterUseCase
from src.usecases.user_use_cases import (
    GetCurrentUserUseCase,
    ListUsersUseCase,
    GetUserUseCase,
    CreateUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase
)
from usecases.chatbot_use_cases import (
    ListChatbotsUseCase,
    GetChatbotUseCase,
    CreateChatbotUseCase,
    UpdateChatbotUseCase,
    DeleteChatbotUseCase
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
from usecases.conversation_use_cases import (
    ListConversationsUseCase,
    GetConversationUseCase,
    CreateConversationUseCase,
    CreateMessageUseCase,
    DeleteConversationUseCase
)


# Infrastructure dependencies
def get_jwt_handler() -> JWTHandler:
    """Get JWT handler instance."""
    return JWTHandler()


# Repository dependencies (return interfaces, not implementations)
def get_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> UserRepository:
    """Get user repository instance."""
    return UserRepositoryImpl(session)


def get_chatbot_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ChatbotRepository:
    """Get chatbot repository instance."""
    return ChatbotRepositoryImpl(session)


def get_conversation_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ConversationRepository:
    """Get conversation repository instance."""
    return ConversationRepositoryImpl(session)


def get_message_repository(
    session: AsyncSession = Depends(get_db_session)
) -> MessageRepository:
    """Get message repository instance."""
    return MessageRepositoryImpl(session)


def get_group_repository(
    session: AsyncSession = Depends(get_db_session)
) -> GroupRepository:
    """Get group repository instance."""
    return GroupRepositoryImpl(session)


def get_user_group_repository(
    session: AsyncSession = Depends(get_db_session)
) -> UserGroupRepository:
    """Get user-group repository instance."""
    return UserGroupRepositoryImpl(session)


def get_group_chatbot_repository(
    session: AsyncSession = Depends(get_db_session)
) -> GroupChatbotRepository:
    """Get group-chatbot repository instance."""
    return GroupChatbotRepositoryImpl(session)


def get_user_chatbot_repository(
    session: AsyncSession = Depends(get_db_session)
) -> UserChatbotRepository:
    """Get user-chatbot repository instance."""
    return UserChatbotRepositoryImpl(session)


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
) -> UserService:
    """Get user service instance."""
    return UserService(user_repository, user_group_repository, group_repository)


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


def get_group_service(
    group_repository: GroupRepository = Depends(get_group_repository),
    user_group_repository: UserGroupRepository = Depends(get_user_group_repository)
) -> GroupService:
    """Get group service instance."""
    return GroupService(group_repository, user_group_repository)


# Auth use cases
def get_login_use_case(
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginUseCase:
    """Get login use case instance."""
    return LoginUseCase(auth_service)


def get_register_use_case(
    auth_service: AuthService = Depends(get_auth_service)
) -> RegisterUseCase:
    """Get register use case instance."""
    return RegisterUseCase(auth_service)


# User use cases
def get_current_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> GetCurrentUserUseCase:
    """Get current user use case instance."""
    return GetCurrentUserUseCase(user_service)


def get_list_users_use_case(
    user_service: UserService = Depends(get_user_service)
) -> ListUsersUseCase:
    """Get list users use case instance."""
    return ListUsersUseCase(user_service)


def get_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> GetUserUseCase:
    """Get user use case instance."""
    return GetUserUseCase(user_service)


def get_create_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> CreateUserUseCase:
    """Get create user use case instance."""
    return CreateUserUseCase(user_service)


def get_update_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> UpdateUserUseCase:
    """Get update user use case instance."""
    return UpdateUserUseCase(user_service)


def get_delete_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> DeleteUserUseCase:
    """Get delete user use case instance."""
    return DeleteUserUseCase(user_service)


# Group use cases
def get_list_groups_use_case(
    group_service: GroupService = Depends(get_group_service)
) -> ListGroupsUseCase:
    """Get list groups use case instance."""
    return ListGroupsUseCase(group_service)


def get_group_use_case(
    group_service: GroupService = Depends(get_group_service)
) -> GetGroupUseCase:
    """Get group use case instance."""
    return GetGroupUseCase(group_service)


def get_create_group_use_case(
    group_service: GroupService = Depends(get_group_service)
) -> CreateGroupUseCase:
    """Get create group use case instance."""
    return CreateGroupUseCase(group_service)


def get_update_group_use_case(
    group_service: GroupService = Depends(get_group_service)
) -> UpdateGroupUseCase:
    """Get update group use case instance."""
    return UpdateGroupUseCase(group_service)


def get_delete_group_use_case(
    group_service: GroupService = Depends(get_group_service)
) -> DeleteGroupUseCase:
    """Get delete group use case instance."""
    return DeleteGroupUseCase(group_service)


# Chatbot use cases
def get_list_chatbots_use_case(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
) -> ListChatbotsUseCase:
    """Get list chatbots use case instance."""
    return ListChatbotsUseCase(chatbot_service)


def get_chatbot_use_case(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
) -> GetChatbotUseCase:
    """Get chatbot use case instance."""
    return GetChatbotUseCase(chatbot_service)


def get_create_chatbot_use_case(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
) -> CreateChatbotUseCase:
    """Get create chatbot use case instance."""
    return CreateChatbotUseCase(chatbot_service)


def get_update_chatbot_use_case(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
) -> UpdateChatbotUseCase:
    """Get update chatbot use case instance."""
    return UpdateChatbotUseCase(chatbot_service)


def get_delete_chatbot_use_case(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
) -> DeleteChatbotUseCase:
    """Get delete chatbot use case instance."""
    return DeleteChatbotUseCase(chatbot_service)


# Conversation use cases
def get_list_conversations_use_case(
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> ListConversationsUseCase:
    """Get list conversations use case instance."""
    return ListConversationsUseCase(conversation_service)


def get_conversation_use_case(
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> GetConversationUseCase:
    """Get conversation use case instance."""
    return GetConversationUseCase(conversation_service)


def get_create_conversation_use_case(
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> CreateConversationUseCase:
    """Get create conversation use case instance."""
    return CreateConversationUseCase(conversation_service)


def get_create_message_use_case(
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> CreateMessageUseCase:
    """Get create message use case instance."""
    return CreateMessageUseCase(conversation_service)


def get_delete_conversation_use_case(
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> DeleteConversationUseCase:
    """Get delete conversation use case instance."""
    return DeleteConversationUseCase(conversation_service)


def get_bedrock_client() -> BedrockClient:
    """Get Bedrock client instance."""
    return BedrockClient()

def get_vector_store_service() -> VectorStoreService:
    """Get vector store service instance."""
    vector_store_instance = VectorStoreFactory.create()
    return VectorStoreService(vector_store_instance)

def get_knowledge_base_service(
    bedrock_client: BedrockClient = Depends(get_bedrock_client)
) -> IKnowledgeBaseService:
    """Get Knowledge Base service instance."""
    return BedrockKnowledgeBaseService(bedrock_client)


def get_rag_service(
    knowledge_base_service: IKnowledgeBaseService = Depends(get_knowledge_base_service)
) -> IRAGService:
    """Get RAG service instance with direct LLM provider."""
    from infrastructure.ai_services.factory import LLMFactory
    llm_provider = LLMFactory.create()  # Direct provider
    return RAGService(knowledge_base_service, llm_provider)

# Document services and repositories
from shared.interfaces.repositories.document_repository import DocumentRepository
from infrastructure.postgresql.repositories import DocumentRepositoryImpl
from shared.interfaces.services.storage.file_storage_service import IFileStorageService
from infrastructure.s3.s3_file_storage_service import S3FileStorageService
from shared.interfaces.services.upload.document_upload_service import IDocumentUploadService
from application.services.document_upload_service import DocumentUploadService

def get_document_repository(
    session: AsyncSession = Depends(get_db_session)
) -> DocumentRepository:
    """Get document repository instance."""
    return DocumentRepositoryImpl(session)

def get_file_storage_service() -> IFileStorageService:
    """Get file storage service instance."""
    return S3FileStorageService()

def get_document_upload_service(
    file_storage: IFileStorageService = Depends(get_file_storage_service),
    document_repository: DocumentRepository = Depends(get_document_repository)
) -> IDocumentUploadService:
    """Get document upload service instance."""
    return DocumentUploadService(file_storage, document_repository)

# Document use cases
def get_upload_document_use_case(
    upload_service: IDocumentUploadService = Depends(get_document_upload_service)
):
    """Get upload document use case."""
    from usecases.document_use_cases import UploadDocumentUseCase
    return UploadDocumentUseCase(upload_service)

def get_delete_document_use_case(
    upload_service: IDocumentUploadService = Depends(get_document_upload_service)
):
    """Get delete document use case."""
    from usecases.document_use_cases import DeleteDocumentUseCase
    return DeleteDocumentUseCase(upload_service)

def get_list_user_documents_use_case(
    document_repository: DocumentRepository = Depends(get_document_repository)
):
    """Get list user documents use case."""
    from usecases.document_use_cases import ListUserDocumentsUseCase
    return ListUserDocumentsUseCase(document_repository)

# RAG Use Cases
def get_chat_with_documents_use_case(
    rag_service: IRAGService = Depends(get_rag_service)
):
    """Get chat with documents use case."""
    from usecases.rag_use_cases import ChatWithDocumentsUseCase
    return ChatWithDocumentsUseCase(rag_service)

def get_semantic_search_use_case(
    rag_service: IRAGService = Depends(get_rag_service)
):
    """Get semantic search use case."""
    from usecases.rag_use_cases import SemanticSearchUseCase
    return SemanticSearchUseCase(rag_service)

def get_retrieve_contexts_use_case(
    rag_service: IRAGService = Depends(get_rag_service)
):
    """Get retrieve contexts use case."""
    from usecases.rag_use_cases import RetrieveContextsUseCase
    return RetrieveContextsUseCase(rag_service)
