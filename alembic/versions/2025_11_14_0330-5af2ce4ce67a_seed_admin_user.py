"""seed_admin_user

Revision ID: 5af2ce4ce67a
Revises: 2b7cff221de5
Create Date: 2025-11-14 03:30:14.394052+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import bcrypt
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "5af2ce4ce67a"
down_revision = "2b7cff221de5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed initial admin user."""
    conn = op.get_bind()

    # Check if any admin users exist
    result = conn.execute(text("SELECT COUNT(*) FROM users WHERE is_admin = true"))
    admin_count = result.scalar()

    # Only create admin if no admin users exist
    if admin_count == 0:
        # Hash the default password: Admin@123
        password = "Admin@123"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert admin user
        conn.execute(
            text("""
                INSERT INTO users (email, password_hash, name, is_admin, status, created_at, updated_at)
                VALUES (:email, :password_hash, :name, :is_admin, :status, :created_at, :updated_at)
            """),
            {
                "email": "admin@example.com",
                "password_hash": hashed_password,
                "name": "System Administrator",
                "is_admin": True,
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        )
        print("✓ Created default admin user (admin@example.com / Admin@123)")
    else:
        print("✓ Admin user already exists, skipping creation")


def downgrade() -> None:
    """Remove seeded admin user."""
    conn = op.get_bind()

    # Remove the seeded admin user
    conn.execute(
        text("DELETE FROM users WHERE email = :email"),
        {"email": "admin@example.com"}
    )
