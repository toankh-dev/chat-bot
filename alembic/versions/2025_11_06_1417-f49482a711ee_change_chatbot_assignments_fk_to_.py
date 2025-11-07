"""change_chatbot_assignments_fk_to_restrict

Revision ID: f49482a711ee
Revises: 3216549452f3
Create Date: 2025-11-06 14:17:40.741816+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f49482a711ee"
down_revision = "3216549452f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Change group_chatbots.assigned_by FK to ON DELETE RESTRICT
    op.drop_constraint(
        "group_chatbots_assigned_by_fkey", "group_chatbots", type_="foreignkey"
    )
    op.create_foreign_key(
        "group_chatbots_assigned_by_fkey",
        "group_chatbots",
        "users",
        ["assigned_by"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Change user_chatbots.assigned_by FK to ON DELETE RESTRICT
    op.drop_constraint(
        "user_chatbots_assigned_by_fkey", "user_chatbots", type_="foreignkey"
    )
    op.create_foreign_key(
        "user_chatbots_assigned_by_fkey",
        "user_chatbots",
        "users",
        ["assigned_by"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Revert user_chatbots.assigned_by FK to ON DELETE SET NULL
    op.drop_constraint(
        "user_chatbots_assigned_by_fkey", "user_chatbots", type_="foreignkey"
    )
    op.create_foreign_key(
        "user_chatbots_assigned_by_fkey",
        "user_chatbots",
        "users",
        ["assigned_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Revert group_chatbots.assigned_by FK to ON DELETE SET NULL
    op.drop_constraint(
        "group_chatbots_assigned_by_fkey", "group_chatbots", type_="foreignkey"
    )
    op.create_foreign_key(
        "group_chatbots_assigned_by_fkey",
        "group_chatbots",
        "users",
        ["assigned_by"],
        ["id"],
        ondelete="SET NULL",
    )
