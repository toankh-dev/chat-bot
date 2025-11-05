"""Initial database schema with seed data

Revision ID: 001
Revises:
Create Date: 2024-11-05 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Boolean, Text, Numeric
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    """Create all tables matching init.sql schema."""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=True,
                  comment='Admin can create users, chatbots, and groups'),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False,
                  comment='Encrypted password (bcrypt)'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True,
                  comment='active, disabled, suspended'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_groups table
    op.create_table(
        'user_groups',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('added_by', sa.Integer(), nullable=True,
                  comment='Admin who added this user to the group'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('user_id', 'group_id')
    )

    # Create chatbots table
    op.create_table(
        'chatbots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False,
                  comment='openai, anthropic, google'),
        sa.Column('model', sa.String(length=100), nullable=False,
                  comment='gpt-4o, claude-3-5-sonnet, gemini-pro'),
        sa.Column('temperature', sa.Numeric(precision=3, scale=2), server_default='0.7',
                  nullable=True, comment='0.0-2.0, controls randomness'),
        sa.Column('max_tokens', sa.Integer(), server_default='2048', nullable=True,
                  comment='Maximum response length'),
        sa.Column('top_p', sa.Numeric(precision=3, scale=2), server_default='1.0', nullable=True,
                  comment='0.0-1.0, nucleus sampling'),
        sa.Column('system_prompt', sa.Text(), nullable=True,
                  comment='Instructions defining bot personality and behavior'),
        sa.Column('welcome_message', sa.Text(), nullable=True,
                  comment='First message sent to users'),
        sa.Column('fallback_message', sa.Text(), nullable=True,
                  comment='Response when API fails'),
        sa.Column('max_conversation_length', sa.Integer(), server_default='50', nullable=True,
                  comment='Messages to remember in context'),
        sa.Column('enable_function_calling', sa.Boolean(), server_default='true', nullable=True,
                  comment='Allow AI to use available tools'),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False,
                  comment='Encrypted API credentials'),
        sa.Column('api_base_url', sa.String(length=500), nullable=True,
                  comment='Custom API endpoint for Azure/custom deployments'),
        sa.Column('created_by', sa.Integer(), nullable=False,
                  comment='Admin who created this chatbot'),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True,
                  comment='active, disabled, archived'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create group_chatbots table
    op.create_table(
        'group_chatbots',
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('chatbot_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True,
                  comment='Admin who assigned this chatbot to the group'),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True,
                  comment='active, revoked'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chatbot_id'], ['chatbots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('group_id', 'chatbot_id')
    )

    # Create user_chatbots table
    op.create_table(
        'user_chatbots',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chatbot_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True,
                  comment='Admin who assigned this chatbot to the user'),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True,
                  comment='active, revoked'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chatbot_id'], ['chatbots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('user_id', 'chatbot_id')
    )

    # Create tools table
    op.create_table(
        'tools',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False,
                  comment='Hard-coded tool identifier'),
        sa.Column('description', sa.Text(), nullable=True,
                  comment='Description of what this tool does'),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True,
                  comment='active, disabled'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create chatbot_tools table
    op.create_table(
        'chatbot_tools',
        sa.Column('chatbot_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.ForeignKeyConstraint(['chatbot_id'], ['chatbots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chatbot_id', 'tool_id')
    )

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chatbot_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True,
                  comment='Conversation title, auto-generated or user-defined'),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True,
                  comment='active, archived, deleted'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True,
                  comment='Whether this conversation is currently active for the user'),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True,
                  comment='Updated with each new message'),
        sa.Column('last_accessed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True, comment='Updated when user accesses the conversation'),
        sa.Column('message_count', sa.Integer(), server_default='0', nullable=True,
                  comment='Total messages in conversation'),
        sa.ForeignKeyConstraint(['chatbot_id'], ['chatbots.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False,
                  comment='user, assistant, system, tool'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True,
                  comment='Additional data: tokens, tool calls, timing'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on messages
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])

    # Create message_feedback table
    op.create_table(
        'message_feedback',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False,
                  comment='The assistant message being rated'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_positive', sa.Boolean(), nullable=False,
                  comment='true = good, false = not good'),
        sa.Column('is_reviewed', sa.Boolean(), server_default='false', nullable=True,
                  comment='Whether admin has reviewed this feedback'),
        sa.Column('note', sa.Text(), nullable=True,
                  comment='Optional comment about the feedback'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Seed data
    _seed_data()


def _seed_data():
    """Seed database with initial data."""

    users_table = table('users',
        column('id', Integer),
        column('is_admin', Boolean),
        column('email', String),
        column('password_hash', String),
        column('name', String),
        column('status', String),
    )

    groups_table = table('groups',
        column('id', Integer),
        column('name', String),
    )

    user_groups_table = table('user_groups',
        column('user_id', Integer),
        column('group_id', Integer),
        column('added_by', Integer),
    )

    tools_table = table('tools',
        column('id', Integer),
        column('name', String),
        column('description', Text),
        column('status', String),
    )

    chatbots_table = table('chatbots',
        column('id', Integer),
        column('name', String),
        column('description', Text),
        column('provider', String),
        column('model', String),
        column('temperature', Numeric),
        column('max_tokens', Integer),
        column('top_p', Numeric),
        column('system_prompt', Text),
        column('welcome_message', Text),
        column('fallback_message', Text),
        column('max_conversation_length', Integer),
        column('enable_function_calling', Boolean),
        column('api_key_encrypted', Text),
        column('api_base_url', String),
        column('created_by', Integer),
        column('status', String),
    )

    chatbot_tools_table = table('chatbot_tools',
        column('chatbot_id', Integer),
        column('tool_id', Integer),
    )

    group_chatbots_table = table('group_chatbots',
        column('group_id', Integer),
        column('chatbot_id', Integer),
        column('assigned_by', Integer),
        column('status', String),
    )

    user_chatbots_table = table('user_chatbots',
        column('user_id', Integer),
        column('chatbot_id', Integer),
        column('assigned_by', Integer),
        column('status', String),
    )

    conversations_table = table('conversations',
        column('id', Integer),
        column('chatbot_id', Integer),
        column('user_id', Integer),
        column('title', String),
        column('status', String),
        column('is_active', Boolean),
        column('message_count', Integer),
    )

    messages_table = table('messages',
        column('id', Integer),
        column('conversation_id', Integer),
        column('role', String),
        column('content', Text),
        column('metadata', postgresql.JSON),
    )

    message_feedback_table = table('message_feedback',
        column('id', Integer),
        column('message_id', Integer),
        column('user_id', Integer),
        column('is_positive', Boolean),
        column('is_reviewed', Boolean),
        column('note', Text),
    )

    op.bulk_insert(users_table, [
        {'id': 1, 'is_admin': True, 'email': 'admin@example.com',
         'password_hash': pwd_context.hash('Admin@123'), 'name': 'System Administrator', 'status': 'active'},
        {'id': 2, 'is_admin': False, 'email': 'john.doe@example.com',
         'password_hash': pwd_context.hash('User@123'), 'name': 'John Doe', 'status': 'active'},
        {'id': 3, 'is_admin': False, 'email': 'jane.smith@example.com',
         'password_hash': pwd_context.hash('User@123'), 'name': 'Jane Smith', 'status': 'active'},
        {'id': 4, 'is_admin': False, 'email': 'bob.wilson@example.com',
         'password_hash': pwd_context.hash('User@123'), 'name': 'Bob Wilson', 'status': 'active'},
    ])

    op.bulk_insert(groups_table, [
        {'id': 1, 'name': 'Engineering Team'},
        {'id': 2, 'name': 'Marketing Team'},
        {'id': 3, 'name': 'Customer Support'},
    ])

    op.bulk_insert(user_groups_table, [
        {'user_id': 2, 'group_id': 1, 'added_by': 1},
        {'user_id': 3, 'group_id': 2, 'added_by': 1},
        {'user_id': 4, 'group_id': 3, 'added_by': 1},
    ])

    op.bulk_insert(tools_table, [
        {'id': 1, 'name': 'web_search', 'description': 'Search the web for current information', 'status': 'active'},
        {'id': 2, 'name': 'code_executor', 'description': 'Execute Python code safely', 'status': 'active'},
        {'id': 3, 'name': 'image_generator', 'description': 'Generate AI images', 'status': 'active'},
        {'id': 4, 'name': 'document_analyzer', 'description': 'Analyze documents', 'status': 'active'},
        {'id': 5, 'name': 'data_visualizer', 'description': 'Create visualizations', 'status': 'disabled'},
    ])

    op.bulk_insert(chatbots_table, [
        {
            'id': 1, 'name': 'General Assistant', 'description': 'A helpful AI assistant',
            'provider': 'anthropic', 'model': 'claude-3-5-sonnet-20240620',
            'temperature': 0.7, 'max_tokens': 4096, 'top_p': 1.0,
            'system_prompt': 'You are a helpful, friendly AI assistant.',
            'welcome_message': 'Hello! How can I help you today?',
            'fallback_message': 'Sorry, having trouble connecting. Please try again.',
            'max_conversation_length': 50, 'enable_function_calling': True,
            'api_key_encrypted': 'encrypted_key', 'api_base_url': None,
            'created_by': 1, 'status': 'active',
        },
        {
            'id': 2, 'name': 'Code Helper', 'description': 'Programming assistant',
            'provider': 'openai', 'model': 'gpt-4o',
            'temperature': 0.3, 'max_tokens': 8000, 'top_p': 0.95,
            'system_prompt': 'You are an expert programming assistant.',
            'welcome_message': 'Hi! I\'m your coding assistant.',
            'fallback_message': 'Technical difficulties. Please wait.',
            'max_conversation_length': 100, 'enable_function_calling': True,
            'api_key_encrypted': 'encrypted_key', 'api_base_url': None,
            'created_by': 1, 'status': 'active',
        },
        {
            'id': 3, 'name': 'Customer Support Bot', 'description': 'Customer service assistant',
            'provider': 'google', 'model': 'gemini-pro',
            'temperature': 0.5, 'max_tokens': 2048, 'top_p': 1.0,
            'system_prompt': 'You are a professional customer support representative.',
            'welcome_message': 'Welcome! How may I assist you?',
            'fallback_message': 'Apologies for the inconvenience.',
            'max_conversation_length': 30, 'enable_function_calling': False,
            'api_key_encrypted': 'encrypted_key', 'api_base_url': None,
            'created_by': 1, 'status': 'active',
        },
    ])

    op.bulk_insert(chatbot_tools_table, [
        {'chatbot_id': 1, 'tool_id': 1},
        {'chatbot_id': 1, 'tool_id': 4},
        {'chatbot_id': 2, 'tool_id': 2},
        {'chatbot_id': 2, 'tool_id': 1},
    ])

    op.bulk_insert(group_chatbots_table, [
        {'group_id': 1, 'chatbot_id': 2, 'assigned_by': 1, 'status': 'active'},
        {'group_id': 2, 'chatbot_id': 1, 'assigned_by': 1, 'status': 'active'},
        {'group_id': 3, 'chatbot_id': 3, 'assigned_by': 1, 'status': 'active'},
    ])

    op.bulk_insert(user_chatbots_table, [
        {'user_id': 2, 'chatbot_id': 1, 'assigned_by': 1, 'status': 'active'},
        {'user_id': 3, 'chatbot_id': 1, 'assigned_by': 1, 'status': 'active'},
    ])

    op.bulk_insert(conversations_table, [
        {'id': 1, 'chatbot_id': 1, 'user_id': 2, 'title': 'Python Best Practices',
         'status': 'active', 'is_active': True, 'message_count': 5},
        {'id': 2, 'chatbot_id': 2, 'user_id': 2, 'title': 'JavaScript Async/Await',
         'status': 'archived', 'is_active': False, 'message_count': 8},
        {'id': 3, 'chatbot_id': 1, 'user_id': 3, 'title': 'Marketing Campaign Ideas',
         'status': 'active', 'is_active': True, 'message_count': 3},
    ])

    op.bulk_insert(messages_table, [
        {'id': 1, 'conversation_id': 1, 'role': 'user',
         'content': 'What are some Python best practices?', 'metadata': None},
        {'id': 2, 'conversation_id': 1, 'role': 'assistant',
         'content': 'Here are essential Python best practices:\n1. Follow PEP 8\n2. Use meaningful names\n3. Write docstrings',
         'metadata': {'tokens': 85, 'model': 'claude-3-5-sonnet'}},
        {'id': 3, 'conversation_id': 1, 'role': 'user',
         'content': 'Tell me more about type hints', 'metadata': None},
        {'id': 4, 'conversation_id': 3, 'role': 'user',
         'content': 'I need spring marketing ideas', 'metadata': None},
        {'id': 5, 'conversation_id': 3, 'role': 'assistant',
         'content': 'Spring campaign ideas:\n1. Spring Renewal Sale\n2. Fresh Start Challenge',
         'metadata': {'tokens': 62, 'model': 'claude-3-5-sonnet'}},
    ])

    op.bulk_insert(message_feedback_table, [
        {'id': 1, 'message_id': 2, 'user_id': 2, 'is_positive': True,
         'is_reviewed': False, 'note': 'Very helpful answer!'},
        {'id': 2, 'message_id': 5, 'user_id': 3, 'is_positive': True,
         'is_reviewed': False, 'note': None},
    ])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('message_feedback')
    op.drop_index('idx_messages_conversation_id', table_name='messages')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('chatbot_tools')
    op.drop_table('tools')
    op.drop_table('user_chatbots')
    op.drop_table('group_chatbots')
    op.drop_table('chatbots')
    op.drop_table('user_groups')
    op.drop_table('groups')
    op.drop_table('users')
