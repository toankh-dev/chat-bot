#!/usr/bin/env python3
"""
Database connection health check script.
Waits for the PostgreSQL database to be ready before proceeding.
"""

import sys
import time
import psycopg2
from psycopg2 import OperationalError
import os


def wait_for_db(max_retries=30, retry_interval=2):
    """
    Wait for the database to be ready.

    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds to wait between retries
    """
    # Get database configuration from environment variables
    db_config = {
        'host': os.getenv('DB_HOST', 'postgres'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'ai_backend'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
    }

    print(f"Waiting for database at {db_config['host']}:{db_config['port']}...")
    print(f"Database: {db_config['database']}")
    print(f"Max retries: {max_retries}, Retry interval: {retry_interval}s")
    print("-" * 50)

    for attempt in range(1, max_retries + 1):
        try:
            # Attempt to connect to the database
            conn = psycopg2.connect(**db_config)
            conn.close()

            print(f"✓ Database is ready! (attempt {attempt}/{max_retries})")
            return True

        except OperationalError as e:
            if attempt < max_retries:
                print(f"⏳ Attempt {attempt}/{max_retries}: Database not ready yet, retrying in {retry_interval}s...")
                time.sleep(retry_interval)
            else:
                print(f"✗ Failed to connect to database after {max_retries} attempts")
                print(f"Error: {e}")
                return False

        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return False

    return False


if __name__ == "__main__":
    success = wait_for_db()
    sys.exit(0 if success else 1)
