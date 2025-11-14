"""add total_tokens to conversations

Revision ID: add_total_tokens
Revises: 582d29a30554
Create Date: 2025-01-13 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_total_tokens'
down_revision = '582d29a30554'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('conversations',
        sa.Column('total_tokens', sa.Integer(), nullable=True, server_default='0')
    )


def downgrade():
    op.drop_column('conversations', 'total_tokens')
