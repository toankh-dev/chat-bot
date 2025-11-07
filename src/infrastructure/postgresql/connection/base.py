"""
SQLAlchemy base configuration and shared components.
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime

# SQLAlchemy Base for all models
Base = declarative_base()

# Association Tables for Many-to-Many relationships
user_roles_table = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('role_id', String, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', String, ForeignKey('users.id'))
)

workspace_users_table = Table(
    'workspace_users',
    Base.metadata,
    Column('workspace_id', String, ForeignKey('workspaces.id'), primary_key=True),
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('role', String, default='member'),  # owner, admin, member, viewer
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('invited_by', String, ForeignKey('users.id'))
)