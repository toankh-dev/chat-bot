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
    # Check if columns exist before dropping (in case they were removed by another migration)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    chatbots_columns = [col['name'] for col in inspector.get_columns('chatbots')]

    if 'api_key_encrypted' in chatbots_columns:
        op.drop_column("chatbots", "api_key_encrypted")
    if 'api_base_url' in chatbots_columns:
        op.drop_column("chatbots", "api_base_url")


def downgrade() -> None:
    """Re-add api_key_encrypted and api_base_url columns."""
    # Add api_key_encrypted column as nullable first
    op.add_column(
        "chatbots",
        sa.Column("api_key_encrypted", sa.Text(), nullable=True, comment="Encrypted API credentials")
    )
    
    # Update all existing records with empty string
    op.execute("UPDATE chatbots SET api_key_encrypted = '' WHERE api_key_encrypted IS NULL")
    
    # Now alter the column to be NOT NULL
    op.alter_column("chatbots", "api_key_encrypted", nullable=False, server_default="")
    
    # Add api_base_url column
    op.add_column(
        "chatbots",
        sa.Column("api_base_url", sa.String(length=500), nullable=True, comment="Custom API endpoint for Azure/custom deployments")
    )
