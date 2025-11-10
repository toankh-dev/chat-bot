"""add_repositories_and_commits_tables

Revision ID: 3ca410960de6
Revises: 6f4f37d7c609
Create Date: 2025-11-10 06:48:52.852116+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3ca410960de6"
down_revision = "6f4f37d7c609"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create repositories and commits tables."""

    # Create Repositories table
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "connection_id",
            sa.Integer(),
            nullable=False,
            comment="User connection that owns this repository"
        ),
        sa.Column(
            "external_id",
            sa.Text(),
            nullable=False,
            comment="Repository ID on external platform (GitLab project ID, GitHub repo ID)"
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
            comment="Repository name"
        ),
        sa.Column(
            "full_name",
            sa.Text(),
            nullable=True,
            comment="Full repository path (e.g., 'user/repo', 'group/subgroup/repo')"
        ),
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=True,
            comment="Repository visibility (public, private, internal)"
        ),
        sa.Column(
            "html_url",
            sa.Text(),
            nullable=True,
            comment="Web URL to repository"
        ),
        sa.Column(
            "default_branch",
            sa.String(length=100),
            nullable=True,
            comment="Default branch name"
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Additional metadata (language, description, stars, etc.)"
        ),
        sa.Column(
            "last_synced_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="Last time this repository was synced"
        ),
        sa.Column(
            "sync_status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=True,
            comment="Sync status (pending, syncing, completed, failed)"
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=True,
            comment="Whether this repository is actively synced"
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
            ["connection_id"],
            ["user_connections.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_repositories_connection_external")
    )

    # Create Commits table
    op.create_table(
        "commits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "repo_id",
            sa.Integer(),
            nullable=False,
            comment="Repository this commit belongs to"
        ),
        sa.Column(
            "external_id",
            sa.Text(),
            nullable=False,
            comment="Commit ID on external platform"
        ),
        sa.Column(
            "sha",
            sa.String(length=40),
            nullable=False,
            comment="Git commit SHA"
        ),
        sa.Column(
            "author_name",
            sa.String(length=255),
            nullable=True,
            comment="Commit author name"
        ),
        sa.Column(
            "author_email",
            sa.String(length=255),
            nullable=True,
            comment="Commit author email"
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=True,
            comment="Commit message"
        ),
        sa.Column(
            "committed_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="When the commit was made"
        ),
        sa.Column(
            "files_changed",
            sa.Integer(),
            nullable=True,
            comment="Number of files changed in this commit"
        ),
        sa.Column(
            "additions",
            sa.Integer(),
            nullable=True,
            comment="Lines added"
        ),
        sa.Column(
            "deletions",
            sa.Integer(),
            nullable=True,
            comment="Lines deleted"
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Additional commit metadata"
        ),
        sa.Column(
            "synced_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="When this commit was synced to KB"
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["repo_id"],
            ["repositories.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id", "sha", name="uq_commits_repo_sha")
    )

    # Create indexes for better query performance
    op.create_index(
        "idx_repositories_connection_id",
        "repositories",
        ["connection_id"]
    )
    op.create_index(
        "idx_repositories_external_id",
        "repositories",
        ["external_id"]
    )
    op.create_index(
        "idx_repositories_sync_status",
        "repositories",
        ["sync_status"]
    )
    op.create_index(
        "idx_repositories_is_active",
        "repositories",
        ["is_active"]
    )
    op.create_index(
        "idx_commits_repo_id",
        "commits",
        ["repo_id"]
    )
    op.create_index(
        "idx_commits_sha",
        "commits",
        ["sha"]
    )
    op.create_index(
        "idx_commits_committed_at",
        "commits",
        ["committed_at"]
    )


def downgrade() -> None:
    """Drop repositories and commits tables."""

    # Drop indexes
    op.drop_index("idx_commits_committed_at", table_name="commits")
    op.drop_index("idx_commits_sha", table_name="commits")
    op.drop_index("idx_commits_repo_id", table_name="commits")
    op.drop_index("idx_repositories_is_active", table_name="repositories")
    op.drop_index("idx_repositories_sync_status", table_name="repositories")
    op.drop_index("idx_repositories_external_id", table_name="repositories")
    op.drop_index("idx_repositories_connection_id", table_name="repositories")

    # Drop tables in correct dependency order
    op.drop_table("commits")
    op.drop_table("repositories")
