"""
PostgreSQL infrastructure components.

Clean architecture implementation for database access.
"""

# Connection management
from .connection import db_manager, get_db_session, Base

# Models
from .models import (
    UserModel, ChatbotModel, ConversationModel, MessageModel, DocumentModel, 
    Group, UserGroup, UserChatbotModel, GroupChatbotModel
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
    "UserModel", "ChatbotModel", "ConversationModel", "MessageModel", "DocumentModel",
    "Group", "UserGroup", "UserChatbotModel", "GroupChatbotModel",
    
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
