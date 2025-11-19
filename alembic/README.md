# Database Migrations with Alembic

This directory contains database migrations for GrandmaScraper using Alembic.

## Common Commands

### Create a New Migration

Auto-generate a migration from model changes:
```bash
alembic revision --autogenerate -m "description of changes"
```

Create an empty migration (for manual changes):
```bash
alembic revision -m "description of changes"
```

### Apply Migrations

Upgrade to the latest version:
```bash
alembic upgrade head
```

Upgrade one version:
```bash
alembic upgrade +1
```

Downgrade one version:
```bash
alembic downgrade -1
```

### View Migration History

Show current version:
```bash
alembic current
```

Show migration history:
```bash
alembic history
```

Show pending migrations:
```bash
alembic history --verbose
```

## Migration Workflow

1. **Make changes to models** in `grandma_scraper/db/models.py`

2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "add webhook tables"
   ```

3. **Review the generated migration** in `alembic/versions/`
   - Check that the upgrade() and downgrade() functions are correct
   - Make manual edits if needed (e.g., data migrations)

4. **Test the migration**:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

5. **Commit the migration** to version control

## Best Practices

1. **Always review auto-generated migrations** - Alembic may not catch everything
2. **Test both upgrade and downgrade** - Ensure migrations are reversible
3. **One logical change per migration** - Keep migrations focused
4. **Include data migrations when needed** - Use op.execute() for data changes
5. **Never edit applied migrations** - Create a new migration instead
6. **Backup production database** before running migrations

## Database Configuration

The database URL is automatically loaded from `grandma_scraper.core.config.settings.database_url`.

You can override it via environment variable:
```bash
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
alembic upgrade head
```

## Initial Migration

To create the initial migration for the current schema:

```bash
# Make sure the database exists but is empty
alembic revision --autogenerate -m "initial schema"

# Review the generated migration file
# Then apply it:
alembic upgrade head
```

## Troubleshooting

**Problem**: Migration conflicts
**Solution**: Use `alembic merge` to merge divergent heads

**Problem**: Database out of sync
**Solution**: Use `alembic stamp head` to mark current version (careful!)

**Problem**: Want to see SQL without executing
**Solution**: Use `alembic upgrade head --sql` to output SQL

## Directory Structure

```
alembic/
├── versions/          # Migration scripts (auto-generated)
├── env.py            # Migration environment configuration
├── script.py.mako    # Template for new migrations
└── README.md         # This file
```

## Example Migration

```python
"""add user role column

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='user'))

def downgrade():
    op.drop_column('users', 'role')
```
