"""seed_predefined_ai_models

Revision ID: f4106c6097a8
Revises: b9b1294169c5
Create Date: 2025-11-11 03:07:58.627190+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f4106c6097a8"
down_revision = "b9b1294169c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed predefined AI models."""
    connection = op.get_bind()
    
    # Predefined AI models from major providers
    predefined_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro"
    ]
    
    # Insert predefined models (skip if already exists)
    for model_name in predefined_models:
        connection.execute(
            sa.text("""
                INSERT INTO ai_models (name) 
                VALUES (:name) 
                ON CONFLICT (name) DO NOTHING
            """),
            {"name": model_name}
        )


def downgrade() -> None:
    """Remove predefined AI models (optional - can be left empty to keep data)."""
    # Optionally remove predefined models, but typically we leave them
    # as they might be referenced by chatbots
    pass
