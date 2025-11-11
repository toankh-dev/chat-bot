#!/usr/bin/env python3
"""
Wait for database to be ready before running migrations.
This script checks database connectivity and retries until successful.
"""
import sys
import time
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings


def wait_for_database(max_retries=30, retry_interval=2):
    """
    Wait for database to be ready.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_interval: Seconds to wait between retries
    
    Returns:
        bool: True if database is ready, False otherwise
    """
    # Use synchronous connection for health check
    db_url = settings.postgres_url.replace("+asyncpg", "")
    
    print(f"Waiting for database at {settings.DB_HOST}:{settings.DB_PORT}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                # Test connection with a simple query
                conn.execute(text("SELECT 1"))
                print(f"✓ Database is ready (attempt {attempt}/{max_retries})")
                engine.dispose()
                return True
        except OperationalError as e:
            if attempt < max_retries:
                print(f"✗ Database not ready (attempt {attempt}/{max_retries}): {str(e)[:100]}")
                time.sleep(retry_interval)
            else:
                print(f"✗ Database connection failed after {max_retries} attempts")
                print(f"  Error: {e}")
                return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            if attempt < max_retries:
                time.sleep(retry_interval)
            else:
                return False
    
    return False


if __name__ == "__main__":
    success = wait_for_database()
    sys.exit(0 if success else 1)

