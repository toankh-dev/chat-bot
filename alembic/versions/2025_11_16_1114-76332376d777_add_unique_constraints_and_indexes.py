"""add_unique_constraints_and_indexes
Revision ID: 76332376d777
Revises: a2ace207a338
Create Date: 2025-11-16 11:14:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "76332376d777"
down_revision = "a2ace207a338"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade database schema.
    """
    op.create_unique_constraint(
        'uq_repositories_connection_external',
        'repositories',
        ['connection_id', 'external_id']
    )
    op.create_unique_constraint(
        'uq_kb_sources_kb_type_id',
        'knowledge_base_sources',
        ['knowledge_base_id', 'source_type', 'source_id']
    )
    op.create_index(
        'idx_sync_queue_repo_status_priority',
        'sync_queue',
        ['repo_id', 'status', 'priority']
    )
    op.create_index(
        'idx_kb_sources_kb_type_id',
        'knowledge_base_sources',
        ['knowledge_base_id', 'source_type', 'source_id']
    )
    op.create_index(
        'idx_file_change_history_commit_path',
        'file_change_history',
        ['commit_id', 'file_path']
    )
    op.create_index(
        'idx_commits_repo_sha',
        'commits',
        ['repo_id', 'sha']
    )

def downgrade() -> None:
    """
    Downgrade database schema.
    """

    # Drop indexes (reverse order)
    op.drop_index('idx_commits_repo_sha', table_name='commits')
    op.drop_index('idx_file_change_history_commit_path', table_name='file_change_history')
    op.drop_index('idx_kb_sources_kb_type_id', table_name='knowledge_base_sources')
    op.drop_index('idx_sync_queue_repo_status_priority', table_name='sync_queue')

    # Drop constraints
    op.drop_constraint('uq_kb_sources_kb_type_id', 'knowledge_base_sources', type_='unique')
    op.drop_constraint('uq_repositories_connection_external', 'repositories', type_='unique')
