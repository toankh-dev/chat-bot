"""make_user_groups_added_by_not_null

Revision ID: 75b73c34eefd
Revises: 001
Create Date: 2025-11-06 13:57:11.369828+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "75b73c34eefd"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Make user_groups.added_by NOT NULL
    # This is safe because all existing records have valid added_by values
    op.alter_column(
        "user_groups",
        "added_by",
        existing_type=sa.Integer(),
        nullable=False,
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Revert user_groups.added_by to nullable
    op.alter_column(
        "user_groups",
        "added_by",
        existing_type=sa.Integer(),
        nullable=True,
        existing_nullable=False,
    )
