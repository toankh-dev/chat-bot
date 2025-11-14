"""remove_provider_api_fields_from_chatbots

Revision ID: ab5508a7223c
Revises: 8c83eb26dc5d
Create Date: 2025-11-10 11:01:44.920470+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "ab5508a7223c"
down_revision = "8c83eb26dc5d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Check if columns exist before dropping them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('chatbots')]
    
    # Remove provider column from chatbots table if it exists
    if 'provider' in columns:
        op.drop_column("chatbots", "provider")
    
    # Remove api_key_encrypted column from chatbots table if it exists  
    if 'api_key_encrypted' in columns:
        op.drop_column("chatbots", "api_key_encrypted")
    
    # Remove api_base_url column from chatbots table if it exists
    if 'api_base_url' in columns:
        op.drop_column("chatbots", "api_base_url")


def downgrade() -> None:
    """Downgrade database schema."""
    # Check if columns exist before adding them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('chatbots')]
    
    # Add back api_base_url column (nullable) if it doesn't exist
    if 'api_base_url' not in columns:
        op.add_column(
            "chatbots", 
            sa.Column(
                "api_base_url", 
                sa.String(500), 
                nullable=True,
                comment="Custom API endpoint for Azure/custom deployments"
            )
        )
    
    # Add back api_key_encrypted column as nullable first if it doesn't exist
    if 'api_key_encrypted' not in columns:
        op.add_column(
            "chatbots",
            sa.Column(
                "api_key_encrypted", 
                sa.Text(), 
                nullable=True, 
                comment="Encrypted API credentials"
            )
        )
        
        # Update existing records with default values
        op.execute("UPDATE chatbots SET api_key_encrypted = '' WHERE api_key_encrypted IS NULL")
        
        # Now alter columns to be NOT NULL
        op.alter_column("chatbots", "api_key_encrypted", nullable=False)
    
    # Add back provider column as nullable first if it doesn't exist
    if 'provider' not in columns:
        op.add_column(
            "chatbots",
            sa.Column(
                "provider", 
                sa.String(50), 
                nullable=True, 
                comment="openai, anthropic, google"
            )
        )
        
        # Update provider column and then make it NOT NULL
        op.execute("UPDATE chatbots SET provider = 'openai' WHERE provider IS NULL")
        op.alter_column("chatbots", "provider", nullable=False)
