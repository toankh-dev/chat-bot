# Database Migrations

## Overview

This project uses Alembic for database migrations. The migrations have been consolidated into a clean, linear structure for better maintainability.

## Migration History

### Current State (2025-11-15)

**Consolidated Migrations:**
1. `2025_11_15_0803-90341b031afb_initial_complete_schema.py` - Complete database schema (20 tables)
2. `2025_11_15_0804-a2ace207a338_seed_initial_data.py` - Seed AI models and admin user

**Old Migrations (Backup):**
- Previous migration history has been backed up to `alembic/versions.backup/`
- 9 migration files were consolidated on 2025-11-15
- Backup includes: initial schema, connectors, repositories, knowledge bases, and seed migrations

### Why Consolidation?

The previous migration history had several issues:
- **Broken chain**: Missing revision IDs (e6f493a16494, 582d29a30554)
- **Schema duplication**: Initial schema contained tables also created in incremental migrations
- **Disconnected chains**: Seeding and table creation migrations were not linked

The consolidation resolves all these issues by creating a single source of truth.

## Database Schema

### Core Tables (21 tables)

**Authentication & Authorization:**
- `users` - User accounts
- `groups` - User groups
- `user_groups` - Many-to-many relationship

**AI Chatbot Management:**
- `chatbots` - Chatbot configurations
- `chatbot_tools` - Tools available to chatbots
- `user_chatbots` - User access to chatbots
- `group_chatbots` - Group access to chatbots
- `ai_models` - Available AI models (gemini, claude, etc.)

**Conversations:**
- `conversations` - Chat sessions
- `messages` - Individual messages

**RAG (Retrieval-Augmented Generation):**
- `documents` - Uploaded documents
- `knowledge_bases` - Knowledge base configurations
- `knowledge_base_sources` - Sources linked to knowledge bases

**External Integrations:**
- `connectors` - Available connectors (GitLab, GitHub, Slack, etc.)
- `user_connections` - User-specific connection credentials (encrypted)

**Repository Sync (GitLab/GitHub):**
- `repositories` - Tracked repositories
- `commits` - Repository commits
- `sync_queue` - Pending sync operations
- `sync_history` - Sync execution history
- `file_change_history` - File-level change tracking

## Running Migrations

### Local Execution

```bash
# Check current migration version
alembic current

# View migration history
alembic history --verbose

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to base (WARNING: Drops all tables)
alembic downgrade base
```

### Docker Compose Execution

```bash
# Apply migrations
docker-compose exec api alembic upgrade head

# Check current version
docker-compose exec api alembic current

# Rollback one migration
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history
```

## Creating New Migrations

### Auto-generate from Model Changes

```bash
# Local
alembic revision --autogenerate -m "description_of_changes"

# Docker
docker-compose exec api alembic revision --autogenerate -m "description_of_changes"
```

### Manual Migration (Data Changes)

```bash
# Create empty migration
docker-compose exec api alembic revision -m "seed_new_data"

# Edit the generated file in alembic/versions/
# Add your upgrade() and downgrade() logic
```

## Seeding Data

### Via Migration (Recommended)

Initial data seeding is handled by the `seed_initial_data` migration:
- AI models: gemini-2.5-flash, gemini-2.5-pro
- Admin user: admin@example.com / Admin@123

### Via Seed Script

```bash
# Run seed script (includes test data)
python alembic/seed.py

# Docker
docker-compose exec api python alembic/seed.py
```

The seed script creates:
- Admin user: admin@kass.dev / admin123
- Regular user: user@kass.dev / user123
- Default group and chatbot
- Sample conversations

## Migration Best Practices

### DO:
-  Review auto-generated migrations before applying
-  Test migrations on development database first
-  Always implement both `upgrade()` and `downgrade()`
-  Use `ON CONFLICT` for idempotent data seeding
-  Add descriptive comments for complex migrations
-  Run `black` formatter on migration files (auto-applied via hook)

### DON'T:
- L Modify existing migrations that have been applied to production
- L Delete migration files (creates broken chains)
- L Skip testing downgrade logic
- L Hard-code sensitive data in migrations
- L Create migrations with side effects (external API calls, file operations)

## Troubleshooting

### Migration Fails with "revision not found"

Check the revision chain:
```bash
docker-compose exec api alembic history
```

Ensure `down_revision` in your migration matches the latest migration ID.

### Tables Already Exist

If you get "table already exists" errors:
```bash
# Stamp the database with current migration version (no changes applied)
docker-compose exec api alembic stamp head
```

### Reset Database Completely

```bash
# WARNING: This deletes all data
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose up -d api
docker-compose exec api alembic upgrade head
```

### Check Applied Migrations

```bash
# View alembic_version table
docker-compose exec postgres psql -U postgres -d ai_backend -c "SELECT * FROM alembic_version;"
```

## Migration Naming Convention

Format: `YYYY_MM_DD_HHMM-<hash>-<slug>.py`

Example: `2025_11_15_0803-90341b031afb_initial_complete_schema.py`

- **Timestamp**: When the migration was created
- **Hash**: Alembic revision ID (first 12 chars)
- **Slug**: Descriptive name (use underscores)

## Important Notes

- **Backup before migrations**: Always backup production database before running migrations
- **Run during maintenance window**: For production, schedule migrations during low-traffic periods
- **Monitor logs**: Check application logs after migrations for any runtime issues
- **Test rollback**: Verify downgrade works before deploying to production
- **Version control**: Always commit migrations to git

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- Project CLAUDE.md - Database Operations section

---

**Last Updated:** 2025-11-15
**Migration Count:** 2 active migrations
**Database Schema Version:** a2ace207a338
