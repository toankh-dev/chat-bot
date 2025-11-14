"""add_knowledge_base_tables

Revision ID: 590e52f36ab4
Revises: ab5508a7223c
Create Date: 2025-11-11 04:46:09.787993+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "590e52f36ab4"
down_revision = "ab5508a7223c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""

    # 1. Create knowledge_bases table
    op.create_table(
        'knowledge_bases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chatbot_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('vector_store_type', sa.String(50), nullable=False, server_default='chromadb'),
        sa.Column('vector_store_collection', sa.String(255), nullable=True),
        sa.Column('vector_store_config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chatbot_id'], ['chatbots.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_knowledge_bases_chatbot_id', 'knowledge_bases', ['chatbot_id'])

    # 2. Create knowledge_base_sources table (polymorphic relationship)
    op.create_table(
        'knowledge_base_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),  # 'repository', 'document', 'api'
        sa.Column('source_id', sa.String(255), nullable=False),  # ID of repository/document/etc
        sa.Column('config', sa.JSON(), nullable=True),  # include/exclude patterns, filters
        sa.Column('auto_sync', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sync_status', sa.String(50), nullable=True),  # pending, syncing, completed, failed
        sa.Column('last_synced_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_kb_sources_kb_id', 'knowledge_base_sources', ['knowledge_base_id'])
    op.create_index('ix_kb_sources_type_id', 'knowledge_base_sources', ['source_type', 'source_id'])

    # 3. Add chatbot_id to repositories (optional FK for easier queries)
    op.add_column('repositories', sa.Column('chatbot_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_repositories_chatbot', 'repositories', 'chatbots', ['chatbot_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_repositories_chatbot_id', 'repositories', ['chatbot_id'])

    # 4. Add repository_id to documents (link uploaded docs to repos if applicable)
    op.add_column('documents', sa.Column('repository_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_documents_repository', 'documents', 'repositories', ['repository_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade database schema."""

    # Drop in reverse order
    op.drop_constraint('fk_documents_repository', 'documents', type_='foreignkey')
    op.drop_column('documents', 'repository_id')

    op.drop_index('ix_repositories_chatbot_id', 'repositories')
    op.drop_constraint('fk_repositories_chatbot', 'repositories', type_='foreignkey')
    op.drop_column('repositories', 'chatbot_id')

    op.drop_index('ix_kb_sources_type_id', 'knowledge_base_sources')
    op.drop_index('ix_kb_sources_kb_id', 'knowledge_base_sources')
    op.drop_table('knowledge_base_sources')

    op.drop_index('ix_knowledge_bases_chatbot_id', 'knowledge_bases')
    op.drop_table('knowledge_bases')
