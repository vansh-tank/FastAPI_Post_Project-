# 10 — Database Migrations with Alembic

---

## 🤔 What is a Database Migration?

**The Problem:**
You have an app in production with real user data. You need to add a new column to the `posts` table. How do you do it safely?

- **Option A:** Drop and recreate the table → **You lose all data!**
- **Option B:** Manually ALTER TABLE → Error-prone, not tracked, can't undo
- **Option C:** Use Alembic → Tracked, reversible, safe

**Alembic is a database migration tool** that:
1. Tracks every schema change as a versioned "migration script"
2. Knows which changes have been applied
3. Can **upgrade** (apply) or **downgrade** (undo) changes

**Analogy:** Alembic is like Git for your database schema. Just as Git tracks code changes with commits, Alembic tracks schema changes with migration files.

---

## 📁 The Alembic Structure

```
alembic/
├── env.py              ← Config: connects Alembic to your SQLAlchemy models
├── script.py.mako      ← Template for new migration files
└── versions/           ← Each migration is a file here
    ├── e7242895bbf3_create_post_table.py   ← Migration 1 (first)
    ├── 04cfff068645_create_users_table.py  ← Migration 2
    └── d623d442a72d_create_votes_table.py  ← Migration 3 (latest)

alembic.ini             ← Main Alembic config file
```

---

## ⚙️ The `alembic.ini` File — Configuration

```ini
[alembic]
script_location = %(here)s/alembic    # Where the alembic/ folder is
prepend_sys_path = .                   # Add current dir to Python path

sqlalchemy.url = mysql+pymysql://root:vanshtank@localhost:3306/FastAPI
```

**Key setting:** `sqlalchemy.url` is the database connection URL. However, in `env.py`, this is overridden programmatically to use the settings from `config.py`:

```python
config.set_main_option("sqlalchemy.url", f"mysql+pymysql://...")
```

This way, the URL always comes from your `.env` file, not from `alembic.ini` directly.

---

## 🔧 The `alembic/env.py` — The Brain

```python
from app.config import settings
from app.models import base

config = context.config
# Override the DB URL from our settings (reads from .env):
config.set_main_option(
    "sqlalchemy.url", 
    f"mysql+pymysql://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)

# Tell Alembic which models to track for autogenerate:
target_metadata = base.metadata
```

### `target_metadata = base.metadata`
This links Alembic to your SQLAlchemy models. When you run `alembic revision --autogenerate`, Alembic:
1. Looks at your current models (via `base.metadata`)
2. Looks at the current database schema
3. Generates migration code for the differences

---

## 📜 Migration Files — Anatomy

Every migration has the same structure. Let's look at the first one:

### Migration 1: Create Posts Table

```python
"""create post table

Revision ID: e7242895bbf3
Revises:                        ← No parent (this is the first migration)
Create Date: 2026-06-02 17:40:06
"""

revision: str = 'e7242895bbf3'
down_revision = None            # No parent migration

def upgrade() -> None:
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('published', sa.Boolean, server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('posts')      # Undo: drop the table
```

| Part | Meaning |
|------|---------|
| `revision` | Unique ID for this migration |
| `down_revision` | ID of the previous migration (forms a chain) |
| `upgrade()` | What to DO (apply the change) |
| `downgrade()` | What to UNDO (reverse the change) |

---

### Migration 2: Create Users Table

```python
revision: str = '04cfff068645'
down_revision = 'e7242895bbf3'   # Comes AFTER the posts migration
```

Wait — posts reference users via foreign key, but users table is created SECOND. Doesn't this cause an error?

**Yes, this is actually a problem in this migration sequence!** If you run `upgrade` on a fresh database:
1. Migration 1 creates `posts` table with `ForeignKey('users.id')` → **ERROR: users table doesn't exist yet!**

The correct order should have been: users first, then posts. This is a common gotcha when learning Alembic — migration order matters!

In practice, the project likely had the database tables created manually first, and the migrations were written afterward as a learning exercise.

---

### Migration 3: Create Votes Table

```python
revision: str = 'd623d442a72d'
down_revision = '04cfff068645'   # Comes after users migration

def upgrade() -> None:
    op.create_table(
        'votes',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('post_id', sa.Integer, sa.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    )
```

The votes table references both `users` and `posts`. This is the last table, so both dependencies exist by the time it's created.

---

## 🔗 The Migration Chain

```
(START) → e7242895bbf3 → 04cfff068645 → d623d442a72d (LATEST)
           create posts    create users    create votes
```

Alembic tracks a special `alembic_version` table in your database:
```sql
SELECT * FROM alembic_version;
-- version_num
-- d623d442a72d
```

This tells Alembic "the database is currently at version `d623d442a72d`."

---

## 💻 Alembic Commands — Your Toolkit

### Create a New Migration Manually
```bash
alembic revision -m "add phone number to users"
```
Creates a new file in `versions/` with empty `upgrade()` and `downgrade()` functions.

### Create a Migration Automatically
```bash
alembic revision --autogenerate -m "add phone number to users"
```
Alembic compares your models to the DB and writes the migration code for you!

### Apply All Pending Migrations (Upgrade to Latest)
```bash
alembic upgrade head
```
Runs all migrations that haven't been applied yet. `head` means "latest version."

### Apply a Specific Migration
```bash
alembic upgrade e7242895bbf3
```
Applies migrations up to (and including) this revision ID.

### Undo the Last Migration
```bash
alembic downgrade -1
```
Runs the `downgrade()` function of the most recent migration.

### Undo ALL Migrations (Start Fresh)
```bash
alembic downgrade base
```
Runs all `downgrade()` functions in reverse order.

### View Migration History
```bash
alembic history --verbose
```

### See Current Version
```bash
alembic current
```

---

## 🆚 Alembic vs `create_all()`

| Feature | `Base.metadata.create_all()` | Alembic |
|---------|------------------------------|---------|
| Speed | Instant (one command) | Need to write migrations |
| Safety | Dangerous with existing data | Safe, incremental |
| History | None | Full history |
| Team use | Hard to sync | Easy (migrations are files in git) |
| Rollback | None | `alembic downgrade` |
| Recommended for | Quick prototyping | Production apps |

---

## 📝 Common Alembic Operations

### Adding a New Column
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'phone')
```

### Renaming a Column
```python
def upgrade() -> None:
    op.alter_column('posts', 'content', new_column_name='body')

def downgrade() -> None:
    op.alter_column('posts', 'body', new_column_name='content')
```

### Adding an Index
```python
def upgrade() -> None:
    op.create_index('ix_posts_title', 'posts', ['title'])

def downgrade() -> None:
    op.drop_index('ix_posts_title', 'posts')
```

---

## ⚠️ Alembic Gotchas for Beginners

### 1. Import your models in `env.py`!
```python
# MUST have this in env.py for autogenerate to work:
from app.models import base
target_metadata = base.metadata
```

Without this, Alembic doesn't know about your tables.

### 2. Run from the project root
```bash
# ✅ Correct (from the FastAPI_Post_Project- directory):
alembic upgrade head

# ❌ Wrong (from inside alembic/):
cd alembic && alembic upgrade head
```

### 3. Always write `downgrade()`
Even if you think you'll never rollback, always write it. You will need it someday.

### 4. Don't edit past migrations
Once a migration is applied to production, never modify it. Create a new migration instead.
