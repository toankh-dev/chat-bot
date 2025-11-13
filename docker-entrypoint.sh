#!/bin/bash
# Docker entrypoint script that optionally runs migrations before starting the app

set -e

# Run migrations if AUTO_MIGRATE is set to true
if [ "${AUTO_MIGRATE:-false}" = "true" ]; then
    echo "=========================================="
    echo "Running database migrations..."
    echo "=========================================="
    
    # Wait for database to be ready
    python3 scripts/wait_for_db.py
    
    # Run migrations
    alembic upgrade head
    
    echo "✓ Migrations completed"
    echo ""
fi

# Execute the main command (uvicorn)
exec "$@"

