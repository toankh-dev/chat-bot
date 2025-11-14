"""add unique constraint sync_queue commit file

Revision ID: sync_queue_unique_001
Revises: 590e52f36ab4
Create Date: 2025-11-14 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'sync_queue_unique_001'
down_revision = '582d29a30554'
branch_labels = None
depends_on = None


def upgrade():
    """Add UNIQUE constraint on (commit_id, file_path) to prevent duplicates."""

    # First, remove any existing duplicates
    op.execute("""
        DELETE FROM sync_queue a USING (
            SELECT MIN(id) as id, commit_id, file_path
            FROM sync_queue
            GROUP BY commit_id, file_path
            HAVING COUNT(*) > 1
        ) b
        WHERE a.commit_id = b.commit_id
        AND a.file_path = b.file_path
        AND a.id <> b.id
    """)

    # Add UNIQUE constraint
    op.create_unique_constraint(
        'uq_sync_queue_commit_file',
        'sync_queue',
        ['commit_id', 'file_path']
    )


def downgrade():
    """Remove UNIQUE constraint."""
    op.drop_constraint('uq_sync_queue_commit_file', 'sync_queue', type_='unique')
