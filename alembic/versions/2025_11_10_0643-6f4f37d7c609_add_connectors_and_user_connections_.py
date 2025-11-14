"""add_connectors_and_user_connections_tables

Revision ID: 6f4f37d7c609
Revises: e6f493a16494
Create Date: 2025-11-10 06:43:52.852116+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6f4f37d7c609"
down_revision = "e6f493a16494"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create connectors and user_connections tables."""

    # Create Connectors table
    op.create_table(
        "connectors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            comment="Connector name (e.g., GitLab, GitHub, Jira)"
        ),
        sa.Column(
            "provider_type",
            sa.String(length=50),
            nullable=False,
            comment="Provider type (gitlab, github, jira, etc.)"
        ),
        sa.Column(
            "auth_type",
            sa.String(length=20),
            nullable=False,
            comment="Authentication type (oauth2, personal_token, api_key)"
        ),
        sa.Column(
            "client_id",
            sa.Text(),
            nullable=True,
            comment="OAuth2 client ID (encrypted)"
        ),
        sa.Column(
            "client_secret",
            sa.Text(),
            nullable=True,
            comment="OAuth2 client secret (encrypted)"
        ),
        sa.Column(
            "config_schema",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Configuration schema for this connector"
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=True,
            comment="Whether this connector is active"
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_type", name="uq_connectors_provider_type")
    )

    # Create UserConnections table
    op.create_table(
        "user_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
            comment="User who owns this connection"
        ),
        sa.Column(
            "connector_id",
            sa.Integer(),
            nullable=False,
            comment="Connector being used"
        ),
        sa.Column(
            "access_token",
            sa.Text(),
            nullable=True,
            comment="Access token (encrypted)"
        ),
        sa.Column(
            "refresh_token",
            sa.Text(),
            nullable=True,
            comment="Refresh token (encrypted) for OAuth2"
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="Token expiration timestamp"
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Additional metadata (project_id, repository_id, etc.)"
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=True,
            comment="Whether this connection is active"
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["connector_id"],
            ["connectors.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "connector_id", name="uq_user_connections_user_connector")
    )

    # Create indexes for better query performance
    op.create_index(
        "idx_user_connections_user_id",
        "user_connections",
        ["user_id"]
    )
    op.create_index(
        "idx_user_connections_connector_id",
        "user_connections",
        ["connector_id"]
    )
    op.create_index(
        "idx_user_connections_is_active",
        "user_connections",
        ["is_active"]
    )


def downgrade() -> None:
    """Drop connectors and user_connections tables."""

    # Drop indexes
    op.drop_index("idx_user_connections_is_active", table_name="user_connections")
    op.drop_index("idx_user_connections_connector_id", table_name="user_connections")
    op.drop_index("idx_user_connections_user_id", table_name="user_connections")

    # Drop tables in correct dependency order
    op.drop_table("user_connections")
    op.drop_table("connectors")
