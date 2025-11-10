"""change_user_groups_added_by_to_restrict

Revision ID: 5ba95ea772b3
Revises: 75b73c34eefd
Create Date: 2025-11-06 13:58:18.967927+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5ba95ea772b3"
down_revision = "75b73c34eefd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Drop the existing foreign key constraint with SET NULL
    op.drop_constraint(
        "user_groups_added_by_fkey", "user_groups", type_="foreignkey"
    )

    # Recreate the foreign key with RESTRICT behavior
    # This prevents deletion of admin users who have added users to groups
    op.create_foreign_key(
        "user_groups_added_by_fkey",
        "user_groups",
        "users",
        ["added_by"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop the RESTRICT constraint
    op.drop_constraint(
        "user_groups_added_by_fkey", "user_groups", type_="foreignkey"
    )

    # Recreate with SET NULL behavior
    op.create_foreign_key(
        "user_groups_added_by_fkey",
        "user_groups",
        "users",
        ["added_by"],
        ["id"],
        ondelete="SET NULL",
    )
