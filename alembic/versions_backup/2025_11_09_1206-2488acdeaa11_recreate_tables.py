"""Recreate tables

Revision ID: 2488acdeaa11
Revises: 29c55130f553
Create Date: 2025-11-09 12:06:39.822047+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2488acdeaa11"
down_revision = "29c55130f553"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema by dropping and recreating tables in correct order."""
    # Drop tables in order of dependencies
    for table in [
        "message_feedback",
        "messages",
        "chatbot_tools",
        "group_chatbots",
        "user_chatbots",
        "user_groups",
        "conversations",
        "documents",
        "tools",
        "chatbots",
        "groups",
        "users",
    ]:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')

    # Create Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "is_admin",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
            comment="Admin can create users, chatbots, and groups",
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            comment="Encrypted password (bcrypt)",
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=True,
            comment="active, disabled, suspended",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Create Groups table
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Chatbots table
    op.create_table(
        "chatbots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False,
            comment="openai, anthropic, google",
        ),
        sa.Column(
            "model",
            sa.String(length=100),
            nullable=False,
            comment="gpt-4, claude-3-5-sonnet, gemini-pro",
        ),
        sa.Column(
            "temperature",
            sa.Numeric(precision=3, scale=2),
            server_default=sa.text("0.7"),
            nullable=True,
            comment="0.0-2.0, controls randomness",
        ),
        sa.Column(
            "max_tokens",
            sa.Integer(),
            server_default=sa.text("2048"),
            nullable=True,
            comment="Maximum response length",
        ),
        sa.Column(
            "top_p",
            sa.Numeric(precision=3, scale=2),
            server_default=sa.text("1.0"),
            nullable=True,
            comment="0.0-1.0, nucleus sampling",
        ),
        sa.Column(
            "system_prompt",
            sa.Text(),
            nullable=True,
            comment="Instructions defining bot personality and behavior",
        ),
        sa.Column(
            "welcome_message",
            sa.Text(),
            nullable=True,
            comment="First message sent to users",
        ),
        sa.Column(
            "fallback_message",
            sa.Text(),
            nullable=True,
            comment="Response when API fails",
        ),
        sa.Column(
            "max_conversation_length",
            sa.Integer(),
            server_default=sa.text("50"),
            nullable=True,
            comment="Messages to remember in context",
        ),
        sa.Column(
            "enable_function_calling",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=True,
            comment="Allow AI to use available tools",
        ),
        sa.Column(
            "api_key_encrypted",
            sa.Text(),
            nullable=False,
            comment="Encrypted API credentials",
        ),
        sa.Column(
            "api_base_url",
            sa.String(length=500),
            nullable=True,
            comment="Custom API endpoint for Azure/custom deployments",
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            nullable=False,
            comment="Admin who created this chatbot",
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=True,
            comment="active, disabled, archived",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Tools table
    op.create_table(
        "tools",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            comment="Hard-coded tool identifier",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Description of what this tool does",
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=True,
            comment="active, disabled",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create Documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("s3_key", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("upload_status", sa.String(), nullable=False),
        sa.Column("processing_status", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("processed_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("knowledge_base_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes on Documents table
    op.create_index("idx_documents_domain", "documents", ["domain"])
    op.create_index("idx_documents_knowledge_base_id", "documents", ["knowledge_base_id"])
    op.create_index("idx_documents_upload_status", "documents", ["upload_status"])
    op.create_index("idx_documents_uploaded_at", "documents", ["uploaded_at"])
    op.create_index("idx_documents_user_id", "documents", ["user_id"])

    # Create UserGroups table
    op.create_table(
        "user_groups",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column(
            "added_by",
            sa.Integer(),
            nullable=False,
            comment="Admin who added this user to the group",
        ),
        sa.Column(
            "joined_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["added_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "group_id"),
    )

    # Create ChatbotTools table
    op.create_table(
        "chatbot_tools",
        sa.Column("chatbot_id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.Column(
            "added_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["chatbot_id"], ["chatbots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chatbot_id", "tool_id"),
    )

    # Create UserChatbots table
    op.create_table(
        "user_chatbots",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("chatbot_id", sa.Integer(), nullable=False),
        sa.Column(
            "assigned_by",
            sa.Integer(),
            nullable=False,
            comment="Admin who assigned this chatbot to the user",
        ),
        sa.Column(
            "assigned_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=True,
            comment="active, revoked",
        ),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["chatbot_id"], ["chatbots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "chatbot_id"),
    )

    # Create GroupChatbots table
    op.create_table(
        "group_chatbots",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("chatbot_id", sa.Integer(), nullable=False),
        sa.Column(
            "assigned_by",
            sa.Integer(),
            nullable=False,
            comment="Admin who assigned this chatbot to the group",
        ),
        sa.Column(
            "assigned_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=True,
            comment="active, revoked",
        ),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["chatbot_id"], ["chatbots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "chatbot_id"),
    )

    # Create Conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chatbot_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=True,
            comment="Conversation title, auto-generated or user-defined",
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=True,
            comment="active, archived, deleted",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=True,
            comment="Whether this conversation is currently active for the user",
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "last_message_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="Updated with each new message",
        ),
        sa.Column(
            "last_accessed_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
            comment="Updated when user accesses the conversation",
        ),
        sa.Column(
            "message_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True,
            comment="Total messages in conversation",
        ),
        sa.ForeignKeyConstraint(["chatbot_id"], ["chatbots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            comment="user, assistant, system, tool",
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment="Additional data: tokens, tool calls, timing",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on Messages table
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"])

    # Create MessageFeedback table
    op.create_table(
        "message_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "message_id",
            sa.Integer(),
            nullable=False,
            comment="The assistant message being rated",
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "is_positive",
            sa.Boolean(),
            nullable=False,
            comment="true = good, false = not good",
        ),
        sa.Column(
            "is_reviewed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
            comment="Whether admin has reviewed this feedback",
        ),
        sa.Column(
            "note", sa.Text(), nullable=True, comment="Optional comment about the feedback"
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop all tables
    for table in [
        "message_feedback",
        "messages",
        "chatbot_tools",
        "group_chatbots",
        "user_chatbots",
        "user_groups",
        "conversations",
        "documents",
        "tools",
        "chatbots",
        "groups",
        "users",
    ]:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')