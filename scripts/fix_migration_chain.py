#!/usr/bin/env python3
"""
Fix migration chain mismatch by stamping database to head if schema is correct.

This script handles the case where the database has a migration history
that references revisions not in the current codebase (e.g., migrations moved to backup).
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from src.core.config import settings


def check_schema(engine):
    """Check if database schema is at the correct state."""
    with engine.connect() as conn:
        # Check for key tables
        result = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name IN ('users', 'chatbots', 'ai_models')"
            )
        )
        table_count = result.scalar()

        # Check for ai_models table (newest addition)
        result2 = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'ai_models'"
            )
        )
        has_ai_models = result2.scalar() > 0

        # Check if chatbots has model_id column (from recent migration)
        result3 = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'chatbots' AND column_name = 'model_id'"
            )
        )
        has_model_id = result3.scalar() > 0

        # Check if chatbots table doesn't have api_key_encrypted (removed in recent migration)
        result4 = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'chatbots' AND column_name = 'api_key_encrypted'"
            )
        )
        no_api_key = result4.scalar() == 0

        return table_count >= 3 and has_ai_models and has_model_id and no_api_key


def main():
    """Main function to fix migration chain."""
    print("Checking database schema...")

    # Create database engine
    db_url = settings.postgres_url.replace("+asyncpg", "")
    engine = create_engine(db_url)

    try:
        if check_schema(engine):
            print("✓ Schema validation passed")
            print("Database schema appears to be at the correct state.")
            print("You can stamp the database to head revision with:")
            print("  alembic stamp head")
            return 0
        else:
            print("✗ Schema validation failed")
            print("Database schema does not match expected state.")
            print("Please run migrations manually or check database state.")
            return 1
    except Exception as e:
        print(f"Error checking schema: {e}")
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())

