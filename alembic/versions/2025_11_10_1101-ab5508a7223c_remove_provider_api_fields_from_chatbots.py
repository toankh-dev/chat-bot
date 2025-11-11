"""remove_provider_api_fields_from_chatbots

Revision ID: ab5508a7223c
Revises: 8c83eb26dc5d
Create Date: 2025-11-10 11:01:44.920470+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ab5508a7223c"
down_revision = "8c83eb26dc5d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Remove provider column from chatbots table
    op.drop_column("chatbots", "provider")
    
    # Remove api_key_encrypted column from chatbots table  
    op.drop_column("chatbots", "api_key_encrypted")
    
    # Remove api_base_url column from chatbots table
    op.drop_column("chatbots", "api_base_url")


def downgrade() -> None:
    """Downgrade database schema."""
    # Add back api_base_url column
    op.add_column(
        "chatbots", 
        sa.Column(
            "api_base_url", 
            sa.String(500), 
            comment="Custom API endpoint for Azure/custom deployments"
        )
    )
    
    # Add back api_key_encrypted column
    op.add_column(
        "chatbots",
        sa.Column(
            "api_key_encrypted", 
            sa.Text(), 
            nullable=False, 
            comment="Encrypted API credentials"
        )
    )
    
    # Add back provider column
    op.add_column(
        "chatbots",
        sa.Column(
            "provider", 
            sa.String(50), 
            nullable=False, 
            comment="openai, anthropic, google"
        )
    )
