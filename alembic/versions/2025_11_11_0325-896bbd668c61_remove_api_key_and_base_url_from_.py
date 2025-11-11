"""remove_api_key_and_base_url_from_chatbots

Revision ID: 896bbd668c61
Revises: f4106c6097a8
Create Date: 2025-11-11 03:25:42.726017+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "896bbd668c61"
down_revision = "f4106c6097a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove api_key_encrypted and api_base_url columns from chatbots table."""
    op.drop_column("chatbots", "api_key_encrypted")
    op.drop_column("chatbots", "api_base_url")


def downgrade() -> None:
    """Re-add api_key_encrypted and api_base_url columns."""
    op.add_column(
        "chatbots",
        sa.Column("api_key_encrypted", sa.Text(), nullable=False, server_default="", comment="Encrypted API credentials")
    )
    op.add_column(
        "chatbots",
        sa.Column("api_base_url", sa.String(length=500), nullable=True, comment="Custom API endpoint for Azure/custom deployments")
    )
