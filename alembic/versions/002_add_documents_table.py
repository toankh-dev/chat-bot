"""Add documents table

Revision ID: 002_add_documents_table
Revises: 001_initial_schema
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_documents_table'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('s3_key', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('upload_status', sa.String(), nullable=False),
        sa.Column('processing_status', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_documents_domain', 'documents', ['domain'])
    op.create_index('idx_documents_upload_status', 'documents', ['upload_status'])
    op.create_index('idx_documents_uploaded_at', 'documents', ['uploaded_at'])


def downgrade():
    op.drop_index('idx_documents_uploaded_at', table_name='documents')
    op.drop_index('idx_documents_upload_status', table_name='documents')
    op.drop_index('idx_documents_domain', table_name='documents')
    op.drop_index('idx_documents_user_id', table_name='documents')
    op.drop_table('documents')