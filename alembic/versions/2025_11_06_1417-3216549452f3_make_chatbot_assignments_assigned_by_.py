"""make_chatbot_assignments_assigned_by_not_null

Revision ID: 3216549452f3
Revises: 5ba95ea772b3
Create Date: 2025-11-06 14:17:21.524754+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3216549452f3"
down_revision = "5ba95ea772b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Make group_chatbots.assigned_by NOT NULL
    op.alter_column(
        "group_chatbots",
        "assigned_by",
        existing_type=sa.Integer(),
        nullable=False,
        existing_nullable=True,
    )

    # Make user_chatbots.assigned_by NOT NULL
    op.alter_column(
        "user_chatbots",
        "assigned_by",
        existing_type=sa.Integer(),
        nullable=False,
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Revert user_chatbots.assigned_by to nullable
    op.alter_column(
        "user_chatbots",
        "assigned_by",
        existing_type=sa.Integer(),
        nullable=True,
        existing_nullable=False,
    )

    # Revert group_chatbots.assigned_by to nullable
    op.alter_column(
        "group_chatbots",
        "assigned_by",
        existing_type=sa.Integer(),
        nullable=True,
        existing_nullable=False,
    )
