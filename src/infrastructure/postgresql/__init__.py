"""
PostgreSQL infrastructure components.

Clean architecture implementation for database access.
"""

# Connection management
from .connection import db_manager, get_db_session, Base

# Models
from .models import (
    User, Chatbot, Conversation, Message, DocumentModel, 
    Group, UserGroup, UserChatbot, GroupChatbot
)

# Repositories  
from .repositories import (
    UserRepositoryImpl,
    ChatbotRepositoryImpl,
    ConversationRepositoryImpl,
    MessageRepositoryImpl,
    DocumentRepositoryImpl,
    EmbeddingIndexRepositoryImpl,
    GroupRepositoryImpl,
    GroupChatbotRepositoryImpl,
    IngestionJobRepositoryImpl,
    UserGroupRepositoryImpl,
    UserChatbotRepositoryImpl
)

# Mappers
from .mappers import (
    UserMapper,
    ChatbotMapper, 
    ConversationMapper,
    MessageMapper,
    DocumentMapper,
    GroupMapper,
    UserGroupMapper,
    UserChatbotMapper,
    GroupChatbotMapper
)

__all__ = [
    # Connection
    "db_manager", "get_db_session", "Base",
    
    # Models
    "User", "Chatbot", "Conversation", "Message", "DocumentModel",
    "Group", "UserGroup", "UserChatbot", "GroupChatbot",
    
    # Repositories
    "UserRepositoryImpl", "ChatbotRepositoryImpl", 
    "ConversationRepositoryImpl", "MessageRepositoryImpl",
    "DocumentRepositoryImpl", "EmbeddingIndexRepositoryImpl", 
    "GroupRepositoryImpl", "GroupChatbotRepositoryImpl",
    "IngestionJobRepositoryImpl", "UserGroupRepositoryImpl",
    "UserChatbotRepositoryImpl",
    
    # Mappers
    "UserMapper", "ChatbotMapper", "ConversationMapper",
    "MessageMapper", "DocumentMapper", "GroupMapper",
    "UserGroupMapper", "UserChatbotMapper", "GroupChatbotMapper"
]
