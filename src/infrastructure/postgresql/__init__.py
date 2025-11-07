"""
PostgreSQL infrastructure components.

Clean architecture implementation for database access.
"""

# Connection management
from .connection import db_manager, get_db_session, Base

# Models
from .models import (
    User, Chatbot, Conversation, Message, DocumentModel
)

# Repositories  
from .repositories import (
    UserRepositoryImpl,
    ChatbotRepositoryImpl,
    ConversationRepositoryImpl,
    MessageRepositoryImpl,
    DocumentRepositoryImpl,
    EmbeddingIndexRepositoryImpl,
    IngestionJobRepositoryImpl
)

# Mappers
from .mappers import (
    UserMapper,
    ChatbotMapper, 
    ConversationMapper,
    MessageMapper,
    DocumentMapper
)

__all__ = [
    # Connection
    "db_manager", "get_db_session", "Base",
    
    # Models
    "User", "Chatbot", "Conversation", "Message", "DocumentModel",
    
    # Repositories
    "UserRepositoryImpl", "ChatbotRepositoryImpl", 
    "ConversationRepositoryImpl", "MessageRepositoryImpl",
    "DocumentRepositoryImpl", "EmbeddingIndexRepositoryImpl", 
    "IngestionJobRepositoryImpl",
    
    # Mappers
    "UserMapper", "ChatbotMapper", "ConversationMapper",
    "MessageMapper", "DocumentMapper"
]
