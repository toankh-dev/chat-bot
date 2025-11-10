"""Add knowledge_base_id to documents table

Revision ID: 003_add_kb_id
Revises: f49482a711ee
Create Date: 2025-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_kb_id'
down_revision = 'f49482a711ee'
branch_labels = None
depends_on = None


def upgrade():
    # Add knowledge_base_id column to documents table
    op.add_column('documents', sa.Column('knowledge_base_id', sa.String(), nullable=True))

    # Create index for better query performance
    op.create_index('idx_documents_knowledge_base_id', 'documents', ['knowledge_base_id'])


def downgrade():
    # Remove index and column
    op.drop_index('idx_documents_knowledge_base_id', table_name='documents')
    op.drop_column('documents', 'knowledge_base_id')
