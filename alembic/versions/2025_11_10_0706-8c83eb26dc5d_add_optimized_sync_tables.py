"""add_optimized_sync_tables

Revision ID: 8c83eb26dc5d
Revises: 3ca410960de6
Create Date: 2025-11-10 07:06:36.552166+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8c83eb26dc5d"
down_revision = "3ca410960de6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create optimized sync tracking tables."""

    # 1. Create sync_configs table
    op.create_table(
        "sync_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "repo_id",
            sa.Integer(),
            nullable=False,
            comment="Repository this config belongs to"
        ),
        sa.Column(
            "batch_size",
            sa.Integer(),
            server_default=sa.text("10"),
            nullable=True,
            comment="Files to process per batch"
        ),
        sa.Column(
            "concurrent_batches",
            sa.Integer(),
            server_default=sa.text("2"),
            nullable=True,
            comment="Number of parallel batches"
        ),
        sa.Column(
            "max_api_calls_per_minute",
            sa.Integer(),
            server_default=sa.text("60"),
            nullable=True,
            comment="Rate limiting"
        ),
        sa.Column(
            "max_retries",
            sa.Integer(),
            server_default=sa.text("3"),
            nullable=True,
            comment="Maximum retry attempts"
        ),
        sa.Column(
            "retry_delay_seconds",
            sa.Integer(),
            server_default=sa.text("60"),
            nullable=True,
            comment="Base delay for exponential backoff"
        ),
        sa.Column(
            "include_extensions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="File extensions to include (e.g., [\".py\", \".js\"])"
        ),
        sa.Column(
            "exclude_patterns",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Patterns to exclude (e.g., [\"**/test/**\", \"**/node_modules/**\"])"
        ),
        sa.Column(
            "max_file_size_mb",
            sa.Integer(),
            server_default=sa.text("5"),
            nullable=True,
            comment="Maximum file size to process"
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
            ["repo_id"],
            ["repositories.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id", name="uq_sync_configs_repo")
    )

    # 2. Create enhanced sync_history table
    op.create_table(
        "sync_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "repo_id",
            sa.Integer(),
            nullable=False,
            comment="Repository being synced"
        ),
        sa.Column(
            "sync_type",
            sa.String(length=20),
            nullable=False,
            comment="Type of sync: full, incremental"
        ),
        sa.Column(
            "triggered_by",
            sa.String(length=20),
            nullable=True,
            comment="Trigger source: manual, scheduled"
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
            comment="User who triggered sync"
        ),
        sa.Column(
            "from_commit_sha",
            sa.String(length=40),
            nullable=True,
            comment="Starting commit SHA"
        ),
        sa.Column(
            "to_commit_sha",
            sa.String(length=40),
            nullable=False,
            comment="Ending commit SHA"
        ),
        sa.Column(
            "files_queued",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "files_processed",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "files_succeeded",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "files_failed",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "files_skipped",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "embeddings_created",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "embeddings_deleted",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "batches_total",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "batches_completed",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "parent_sync_id",
            sa.Integer(),
            nullable=True,
            comment="Parent sync if this is a retry"
        ),
        sa.Column(
            "api_calls_made",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "avg_file_process_time_ms",
            sa.Integer(),
            nullable=True
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            comment="Status: running, completed, failed, partial, retrying"
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="Sanitized error message (no sensitive data)"
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(),
            nullable=True
        ),
        sa.Column(
            "duration_seconds",
            sa.Integer(),
            nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["repo_id"],
            ["repositories.id"],
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["parent_sync_id"],
            ["sync_history.id"],
            ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. Create file_change_history table
    op.create_table(
        "file_change_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "repo_id",
            sa.Integer(),
            nullable=False,
            comment="Repository this change belongs to"
        ),
        sa.Column(
            "commit_id",
            sa.Integer(),
            nullable=True,
            comment="Commit that changed this file"
        ),
        sa.Column(
            "sync_history_id",
            sa.Integer(),
            nullable=True,
            comment="Sync session that processed this change"
        ),
        sa.Column(
            "file_path",
            sa.Text(),
            nullable=False,
            comment="Path to file in repository"
        ),
        sa.Column(
            "change_type",
            sa.String(length=20),
            nullable=False,
            comment="Type: added, modified, deleted, renamed"
        ),
        sa.Column(
            "old_path",
            sa.Text(),
            nullable=True,
            comment="Previous path for renamed files"
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
            "file_size_bytes",
            sa.Integer(),
            nullable=True
        ),
        sa.Column(
            "synced_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="When embedding was created"
        ),
        sa.Column(
            "sync_status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=True,
            comment="Status: pending, synced, failed, skipped"
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "last_retry_at",
            sa.TIMESTAMP(),
            nullable=True
        ),
        sa.Column(
            "next_retry_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="When to retry (exponential backoff)"
        ),
        sa.Column(
            "error_type",
            sa.String(length=50),
            nullable=True,
            comment="Error category: api_error, parse_error, timeout, etc."
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="Sanitized error message (no sensitive data)"
        ),
        sa.Column(
            "process_time_ms",
            sa.Integer(),
            nullable=True,
            comment="Time taken to process this file"
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
        sa.ForeignKeyConstraint(
            ["commit_id"],
            ["commits.id"],
            ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["sync_history_id"],
            ["sync_history.id"],
            ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. Create sync_queue table (lightweight queue for pending files)
    op.create_table(
        "sync_queue",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "repo_id",
            sa.Integer(),
            nullable=False,
            comment="Repository"
        ),
        sa.Column(
            "commit_id",
            sa.Integer(),
            nullable=False,
            comment="Commit that changed this file"
        ),
        sa.Column(
            "file_change_history_id",
            sa.Integer(),
            nullable=True,
            comment="Reference to file change history"
        ),
        sa.Column(
            "file_path",
            sa.Text(),
            nullable=False
        ),
        sa.Column(
            "change_type",
            sa.String(length=20),
            nullable=False
        ),
        sa.Column(
            "priority",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True,
            comment="Higher priority processed first"
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=True,
            comment="Status: pending, processing, completed, failed"
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True
        ),
        sa.Column(
            "max_retries",
            sa.Integer(),
            server_default=sa.text("3"),
            nullable=True
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
            comment="Last error message (sanitized)"
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(),
            nullable=True
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(),
            nullable=True
        ),
        sa.Column(
            "next_retry_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="When to retry with exponential backoff"
        ),
        sa.ForeignKeyConstraint(
            ["repo_id"],
            ["repositories.id"],
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["commit_id"],
            ["commits.id"],
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["file_change_history_id"],
            ["file_change_history.id"],
            ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. Create repository_files table (current state of files)
    op.create_table(
        "repository_files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "repo_id",
            sa.Integer(),
            nullable=False,
            comment="Repository"
        ),
        sa.Column(
            "file_path",
            sa.Text(),
            nullable=False,
            comment="Path to file in repository"
        ),
        sa.Column(
            "last_commit_sha",
            sa.String(length=40),
            nullable=True,
            comment="Last commit that changed this file"
        ),
        sa.Column(
            "last_synced_commit_sha",
            sa.String(length=40),
            nullable=True,
            comment="Last commit SHA we synced embeddings for"
        ),
        sa.Column(
            "file_type",
            sa.String(length=50),
            nullable=True,
            comment="File extension (py, js, md, etc.)"
        ),
        sa.Column(
            "file_size_bytes",
            sa.Integer(),
            nullable=True
        ),
        sa.Column(
            "synced_at",
            sa.TIMESTAMP(),
            nullable=True,
            comment="Last successful sync time"
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
            ["repo_id"],
            ["repositories.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id", "file_path", name="uq_repo_files")
    )

    # 6. Create synced_documents table (mapping to vector store)
    op.create_table(
        "synced_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "repo_id",
            sa.Integer(),
            nullable=False,
            comment="Repository"
        ),
        sa.Column(
            "file_path",
            sa.Text(),
            nullable=False,
            comment="File path in repository"
        ),
        sa.Column(
            "commit_sha",
            sa.String(length=40),
            nullable=False,
            comment="Commit SHA when this embedding was created"
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True,
            comment="Chunk position in file (0-based)"
        ),
        sa.Column(
            "vector_store_id",
            sa.Text(),
            nullable=False,
            comment="Document ID in ChromaDB or other vector store"
        ),
        sa.Column(
            "embedding_model",
            sa.String(length=100),
            nullable=True,
            comment="Model used to create embedding"
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
        sa.PrimaryKeyConstraint("id")
    )

    # Create indexes for performance
    op.create_index(
        "idx_sync_history_repo_status",
        "sync_history",
        ["repo_id", "status", "started_at"]
    )
    op.create_index(
        "idx_file_history_commit",
        "file_change_history",
        ["commit_id"]
    )
    op.create_index(
        "idx_file_history_sync_status",
        "file_change_history",
        ["repo_id", "sync_status"]
    )
    op.create_index(
        "idx_file_history_retry",
        "file_change_history",
        ["sync_status", "next_retry_at"]
    )
    op.create_index(
        "idx_file_history_path",
        "file_change_history",
        ["repo_id", "file_path", "created_at"]
    )
    op.create_index(
        "idx_sync_queue_pending",
        "sync_queue",
        ["status", "priority", "created_at"]
    )
    op.create_index(
        "idx_sync_queue_repo",
        "sync_queue",
        ["repo_id", "status"]
    )
    op.create_index(
        "idx_sync_queue_retry",
        "sync_queue",
        ["status", "next_retry_at"]
    )
    op.create_index(
        "idx_repo_files_sync_status",
        "repository_files",
        ["repo_id", "last_commit_sha", "last_synced_commit_sha"]
    )
    op.create_index(
        "idx_synced_docs_repo_file",
        "synced_documents",
        ["repo_id", "file_path", "commit_sha"]
    )
    op.create_index(
        "idx_synced_docs_vector_store",
        "synced_documents",
        ["vector_store_id"]
    )


def downgrade() -> None:
    """Drop optimized sync tracking tables."""

    # Drop indexes
    op.drop_index("idx_synced_docs_vector_store", table_name="synced_documents")
    op.drop_index("idx_synced_docs_repo_file", table_name="synced_documents")
    op.drop_index("idx_repo_files_sync_status", table_name="repository_files")
    op.drop_index("idx_sync_queue_retry", table_name="sync_queue")
    op.drop_index("idx_sync_queue_repo", table_name="sync_queue")
    op.drop_index("idx_sync_queue_pending", table_name="sync_queue")
    op.drop_index("idx_file_history_path", table_name="file_change_history")
    op.drop_index("idx_file_history_retry", table_name="file_change_history")
    op.drop_index("idx_file_history_sync_status", table_name="file_change_history")
    op.drop_index("idx_file_history_commit", table_name="file_change_history")
    op.drop_index("idx_sync_history_repo_status", table_name="sync_history")

    # Drop tables in reverse dependency order
    op.drop_table("synced_documents")
    op.drop_table("repository_files")
    op.drop_table("sync_queue")
    op.drop_table("file_change_history")
    op.drop_table("sync_history")
    op.drop_table("sync_configs")
