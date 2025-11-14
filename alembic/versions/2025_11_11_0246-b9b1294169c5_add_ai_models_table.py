"""add_ai_models_table

Revision ID: b9b1294169c5
Revises: e6f493a16494
Create Date: 2025-11-11 02:46:20.885820+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b9b1294169c5"
down_revision = "e6f493a16494"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create ai_models table
    op.create_table(
        "ai_models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, comment="Model name (e.g., gpt-4o, claude-3-5-sonnet)"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Add model_id column to chatbots table (nullable initially)
    op.add_column(
        "chatbots",
        sa.Column("model_id", sa.Integer(), nullable=True, comment="Foreign key to ai_models table")
    )

    # Create foreign key constraint
    op.create_foreign_key(
        "fk_chatbots_model_id",
        "chatbots",
        "ai_models",
        ["model_id"],
        ["id"],
        ondelete="RESTRICT"
    )

    # Populate ai_models table with unique model names from chatbots
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT DISTINCT model FROM chatbots WHERE model IS NOT NULL"))
    unique_models = [row[0] for row in result]

    # Insert unique models into ai_models table
    for model_name in unique_models:
        # Check if model already exists before inserting
        check_result = connection.execute(
            sa.text("SELECT id FROM ai_models WHERE name = :name"),
            {"name": model_name}
        )
        if not check_result.fetchone():
            connection.execute(
                sa.text("INSERT INTO ai_models (name) VALUES (:name)"),
                {"name": model_name}
            )

    # Update chatbots.model_id based on matching ai_models.name
    connection.execute(
        sa.text("""
            UPDATE chatbots 
            SET model_id = ai_models.id 
            FROM ai_models 
            WHERE chatbots.model = ai_models.name
        """)
    )

    # Make model_id NOT NULL after populating
    op.alter_column("chatbots", "model_id", nullable=False)

    # Remove provider and model columns from chatbots table (data now in ai_models)
    # Check if columns exist before dropping (in case they were removed by another migration)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    chatbots_columns = [col['name'] for col in inspector.get_columns('chatbots')]

    if 'provider' in chatbots_columns:
        op.drop_column("chatbots", "provider")
    if 'model' in chatbots_columns:
        op.drop_column("chatbots", "model")


def downgrade() -> None:
    """Downgrade database schema."""
    # Re-add provider and model columns (restore original structure)
    op.add_column(
        "chatbots",
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="anthropic", comment="openai, anthropic, google")
    )
    op.add_column(
        "chatbots",
        sa.Column("model", sa.String(length=100), nullable=False, server_default="claude-3-5-sonnet", comment="gpt-4o, claude-3-5-sonnet, gemini-pro")
    )
    
    # Restore model names from ai_models before dropping
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE chatbots 
            SET model = ai_models.name 
            FROM ai_models 
            WHERE chatbots.model_id = ai_models.id
        """)
    )
    
    # Drop foreign key constraint
    op.drop_constraint("fk_chatbots_model_id", "chatbots", type_="foreignkey")
    
    # Remove model_id column from chatbots
    op.drop_column("chatbots", "model_id")
    
    # Drop ai_models table
    op.drop_table("ai_models")
