"""merge_migration_heads

Revision ID: 2ca38bfde116
Revises: 582d29a30554, 590e52f36ab4
Create Date: 2025-11-14 02:49:48.400827+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2ca38bfde116"
down_revision = ("582d29a30554", "590e52f36ab4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
