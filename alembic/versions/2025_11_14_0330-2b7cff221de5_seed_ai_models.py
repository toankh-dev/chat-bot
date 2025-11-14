"""seed_ai_models

Revision ID: 2b7cff221de5
Revises: b06a66f9583a
Create Date: 2025-11-14 03:30:14.094496+00:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "2b7cff221de5"
down_revision = "b06a66f9583a"
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
    now = datetime.utcnow()
    for model_name in predefined_models:
        connection.execute(
            sa.text("""
                INSERT INTO ai_models (name, created_at, updated_at)
                VALUES (:name, :created_at, :updated_at)
                ON CONFLICT (name) DO NOTHING
            """),
            {"name": model_name, "created_at": now, "updated_at": now}
        )


def downgrade() -> None:
    """Remove predefined AI models."""
    connection = op.get_bind()

    predefined_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro"
    ]

    for model_name in predefined_models:
        connection.execute(
            sa.text("DELETE FROM ai_models WHERE name = :name"),
            {"name": model_name}
        )
