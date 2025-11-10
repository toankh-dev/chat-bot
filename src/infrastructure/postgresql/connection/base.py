"""
SQLAlchemy base configuration and shared components.
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime

# SQLAlchemy Base for all models
Base = declarative_base()

# Note: association tables that reference other models (e.g. roles, workspaces)
# were removed from the base module because they create ForeignKey references
# during module import time to tables that are not yet registered in
# `Base.metadata` (or are not implemented in `src.infrastructure.postgresql.models`).
#
# If you need many-to-many association tables, define them in a models module
# that is imported after the referenced ORM models exist (or define them
# in the same module as their related models). This avoids NoReferencedTableError
# during Alembic autogenerate.

# TODO: re-introduce association tables in a models file when `roles` and
# `workspaces` DB models are implemented.