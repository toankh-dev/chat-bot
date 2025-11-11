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
        # OpenAI models
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        # Anthropic models
        "claude-3-5-sonnet",
        "claude-3-opus",
        "claude-3-haiku",
        "claude-3-5-haiku",
        # Google models
        "gemini-pro",
        "gemini-ultra",
        "gemini-1.5-pro",
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
