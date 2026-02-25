"""seed_initial_data

Revision ID: a2ace207a338
Revises: 90341b031afb
Create Date: 2025-11-15 08:04:15.130577+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import bcrypt
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "a2ace207a338"
down_revision = "90341b031afb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed initial data: AI models and admin user."""
    conn = op.get_bind()
    now = datetime.utcnow()

    # 1. Seed AI models
    predefined_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]

    for model_name in predefined_models:
        conn.execute(
            text("""
                INSERT INTO ai_models (name, created_at, updated_at)
                VALUES (:name, :created_at, :updated_at)
                ON CONFLICT (name) DO NOTHING
            """),
            {"name": model_name, "created_at": now, "updated_at": now}
        )

    print(f"✓ Seeded {len(predefined_models)} AI models")

    # 2. Seed admin user (only if no admin exists)
    result = conn.execute(text("SELECT COUNT(*) FROM users WHERE is_admin = true"))
    admin_count = result.scalar()

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
                "created_at": now,
                "updated_at": now
            }
        )
        print("✓ Created default admin user (admin@example.com / Admin@123)")
    else:
        print("✓ Admin user already exists, skipping creation")


def downgrade() -> None:
    """Remove seeded initial data."""
    conn = op.get_bind()

    # Remove AI models
    predefined_models = ["gemini-2.5-flash", "gemini-2.5-pro"]
    for model_name in predefined_models:
        conn.execute(
            text("DELETE FROM ai_models WHERE name = :name"),
            {"name": model_name}
        )

    # Remove admin user
    conn.execute(
        text("DELETE FROM users WHERE email = :email"),
        {"email": "admin@example.com"}
    )
