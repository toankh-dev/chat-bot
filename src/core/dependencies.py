"""
Dependency injection container.

Provides dependencies for controllers and use cases following Clean Architecture.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.postgresql.pg_client import get_db_session
from src.infrastructure.auth.jwt_handler import JWTHandler
from src.core.config import settings

# Repositories
from src.infrastructure.postgresql.user_repository_impl import UserRepositoryImpl
from src.infrastructure.postgresql.group_repository_impl import GroupRepositoryImpl
from src.infrastructure.postgresql.user_group_repository_impl import UserGroupRepositoryImpl
from src.infrastructure.postgresql.chatbot_repository_impl import ChatbotRepositoryImpl
from src.infrastructure.postgresql.group_chatbot_repository_impl import GroupChatbotRepositoryImpl
from src.infrastructure.postgresql.user_chatbot_repository_impl import UserChatbotRepositoryImpl
from src.infrastructure.postgresql.conversation_repository_impl import (
    ConversationRepositoryImpl,
    MessageRepositoryImpl
)

# Services
from src.application.services.auth_service import AuthService
from src.application.services.user_service import UserService
from src.application.services.group_service import GroupService
from src.application.services.chatbot_service import ChatbotService
from src.application.services.conversation_service import ConversationService

# Use Cases
from src.usecases.auth_use_cases import LoginUseCase, RegisterUseCase
from src.usecases.user_use_cases import (
    GetCurrentUserUseCase,
    ListUsersUseCase,
    GetUserUseCase,
    CreateUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase
)
from src.usecases.group_use_cases import (
    ListGroupsUseCase,
    GetGroupUseCase,
    CreateGroupUseCase,
    UpdateGroupUseCase,
    DeleteGroupUseCase
)
from src.usecases.chatbot_use_cases import (
    ListChatbotsUseCase,
    GetChatbotUseCase,
    CreateChatbotUseCase,
    UpdateChatbotUseCase,
    DeleteChatbotUseCase
)
from src.usecases.conversation_use_cases import (
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


# Repository dependencies
def get_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> UserRepositoryImpl:
    """Get user repository instance."""
    return UserRepositoryImpl(session)


def get_chatbot_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ChatbotRepositoryImpl:
    """Get chatbot repository instance."""
    return ChatbotRepositoryImpl(session)


def get_conversation_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ConversationRepositoryImpl:
    """Get conversation repository instance."""
    return ConversationRepositoryImpl(session)


def get_message_repository(
    session: AsyncSession = Depends(get_db_session)
) -> MessageRepositoryImpl:
    """Get message repository instance."""
    return MessageRepositoryImpl(session)


def get_group_repository(
    session: AsyncSession = Depends(get_db_session)
) -> GroupRepositoryImpl:
    """Get group repository instance."""
    return GroupRepositoryImpl(session)


def get_user_group_repository(
    session: AsyncSession = Depends(get_db_session)
) -> UserGroupRepositoryImpl:
    """Get user-group repository instance."""
    return UserGroupRepositoryImpl(session)


def get_group_chatbot_repository(
    session: AsyncSession = Depends(get_db_session)
) -> GroupChatbotRepositoryImpl:
    """Get group-chatbot repository instance."""
    return GroupChatbotRepositoryImpl(session)


def get_user_chatbot_repository(
    session: AsyncSession = Depends(get_db_session)
) -> UserChatbotRepositoryImpl:
    """Get user-chatbot repository instance."""
    return UserChatbotRepositoryImpl(session)


# Service dependencies
def get_auth_service(
    user_repository: UserRepositoryImpl = Depends(get_user_repository),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> AuthService:
    """Get auth service instance."""
    return AuthService(user_repository, jwt_handler)


def get_user_service(
    user_repository: UserRepositoryImpl = Depends(get_user_repository),
    user_group_repository: UserGroupRepositoryImpl = Depends(get_user_group_repository),
    group_repository: GroupRepositoryImpl = Depends(get_group_repository)
) -> UserService:
    """Get user service instance."""
    return UserService(user_repository, user_group_repository, group_repository)


def get_chatbot_service(
    chatbot_repository: ChatbotRepositoryImpl = Depends(get_chatbot_repository),
    group_chatbot_repository: GroupChatbotRepositoryImpl = Depends(get_group_chatbot_repository),
    user_chatbot_repository: UserChatbotRepositoryImpl = Depends(get_user_chatbot_repository),
    group_repository: GroupRepositoryImpl = Depends(get_group_repository),
    user_repository: UserRepositoryImpl = Depends(get_user_repository)
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
    conversation_repository: ConversationRepositoryImpl = Depends(get_conversation_repository),
    message_repository: MessageRepositoryImpl = Depends(get_message_repository)
) -> ConversationService:
    """Get conversation service instance."""
    return ConversationService(conversation_repository, message_repository)


def get_group_service(
    group_repository: GroupRepositoryImpl = Depends(get_group_repository),
    user_group_repository: UserGroupRepositoryImpl = Depends(get_user_group_repository)
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
