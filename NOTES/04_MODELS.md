# 04 — Database Models: `models.py` Explained

---

## 🤔 What Are Models?

A **model** in SQLAlchemy is a Python class that represents a **database table**. Each attribute of the class represents a **column** in that table.

**Analogy:** If a database table is a spreadsheet, then:
- The model class = the spreadsheet template (defines columns)
- A model instance = one row in the spreadsheet

```python
# This class ↓
class Post(base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))

# Represents this table ↓
# posts
# | id | title     |
# |----|-----------|
# |  1 | My Post   |
# |  2 | Another   |
```

---

## 📦 Imports

```python
from .database import base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
```

| Import | What it is |
|--------|-----------|
| `base` | The parent class all models inherit from (from `database.py`) |
| `Column` | Defines a column in the table |
| `Integer, String, Boolean, DateTime` | Column data types |
| `func` | SQL functions like `NOW()` |
| `ForeignKey` | Links one table to another |
| `relationship` | Defines the Python-level link between models |

---

## 📄 The `Post` Model

```python
class Post(base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(String(2000), nullable=False)
    published = Column(Boolean, nullable=False, server_default="1")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User")
```

### Column by Column Breakdown:

#### `id`
```python
id = Column(Integer, primary_key=True, autoincrement=True)
```
- `Integer` → stores whole numbers
- `primary_key=True` → uniquely identifies each row, must be unique and not null
- `autoincrement=True` → database automatically assigns 1, 2, 3... when new rows are added

**Analogy:** Like a ticket number at a deli counter — every ticket is unique and auto-numbered.

#### `title`
```python
title = Column(String(255), nullable=False)
```
- `String(255)` → text up to 255 characters
- `nullable=False` → this field MUST have a value, can't be empty

#### `content`
```python
content = Column(String(2000), nullable=False)
```
- `String(2000)` → text up to 2000 characters (the post body)

#### `published`
```python
published = Column(Boolean, nullable=False, server_default="1")
```
- `Boolean` → True or False (1 or 0 in MySQL)
- `server_default="1"` → the **database** sets this to 1 (True) if not specified
  - Note: `server_default` is a string because it's passed as raw SQL
  - `"1"` = True in MySQL boolean context

**Analogy:** Like a "Published" checkbox on a blog that's checked by default.

#### `created_at`
```python
created_at = Column(DateTime, nullable=False, server_default=func.now())
```
- `DateTime` → stores date + time
- `server_default=func.now()` → database automatically sets this to the current timestamp when a row is inserted
- You **never** need to set this manually — the DB handles it!

**Analogy:** Like a receipt that auto-prints the current time.

#### `user_id` (Foreign Key)
```python
user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
```
- `ForeignKey("users.id")` → this column links to the `id` column of the `users` table
- `ondelete="CASCADE"` → if a user is deleted, ALL their posts are automatically deleted too

**Analogy:** If you delete a customer account, their orders are automatically cancelled too (CASCADE). Without CASCADE, you'd get an error trying to delete a user who has posts.

#### `owner` (Relationship)
```python
owner = relationship("User")
```
- This is **NOT** a database column — it's a Python-level convenience
- When you access `post.owner`, SQLAlchemy automatically runs a query to fetch the associated User object
- The string `"User"` refers to the `User` model class

**Analogy:** It's like a shortcut. Instead of manually looking up a user by `user_id`, you just say `post.owner` and get the full User object.

---

## 👤 The `User` Model

```python
class User(base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(254), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

### Notable differences from Post:

#### `email`
```python
email = Column(String(254), nullable=False, unique=True)
```
- `unique=True` → no two users can have the same email (enforced at database level)
- `String(254)` → 254 is the maximum valid length for an email address per RFC 5321

#### `password`
```python
password = Column(String(255), nullable=False)
```
- Stores the **hashed** password (never the plain text!)
- bcrypt hashes are always ~60 characters but String(255) gives room for different algorithms

---

## 🗳️ The `Vote` Model (Composite Primary Key)

```python
class Vote(base):
    __tablename__ = "votes"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
```

### What's special here? No `id` column!

The `Vote` table uses a **composite primary key** — both `user_id` AND `post_id` together form the unique key.

**Why?** Because:
- A user can vote on many posts (user_id alone isn't unique)
- A post can get many votes (post_id alone isn't unique)
- But a specific user can only vote ONCE on a specific post (the PAIR is unique)

**Analogy:** A concert ticket has a seat row AND seat number. Row B alone isn't unique (many seats in row B). Seat 5 alone isn't unique (many rows have seat 5). But Row B, Seat 5 = unique!

### CASCADE on both sides:
- If a user is deleted → their votes are deleted
- If a post is deleted → its votes are deleted

This prevents "orphan" records (votes pointing to users or posts that no longer exist).

---

## 🔗 The ORM Relationship Explained

```python
# In the Post model:
owner = relationship("User")
```

When you do:
```python
post = db.query(models.Post).filter(models.Post.id == 1).first()
print(post.owner)        # ← Returns the User object!
print(post.owner.email)  # ← Access user's email directly
```

SQLAlchemy automatically does a JOIN query behind the scenes. This is the power of ORMs — they make related data feel natural to work with.

---

## 🆚 Model vs Schema — A Common Confusion

These two terms look similar but are completely different!

| Concept | File | Purpose |
|---------|------|---------|
| **Model** | `models.py` | Defines the DATABASE TABLE structure |
| **Schema** | `schemas.py` | Defines REQUEST/RESPONSE data shapes |

**Analogy:**
- Model = The actual warehouse shelves (where stuff is physically stored)
- Schema = The order form and packing slip (what goes in, what comes out)

You use models to read/write from the database. You use schemas to validate what a user sends and shape what you send back.

---

## 📋 Summary: All Column Options

| Option | What it does |
|--------|-------------|
| `primary_key=True` | Makes this the unique identifier |
| `autoincrement=True` | DB auto-assigns next number |
| `nullable=False` | Field is required (can't be NULL) |
| `nullable=True` | Field is optional |
| `unique=True` | Value must be unique across all rows |
| `server_default="value"` | DB sets this default, not Python |
| `default=value` | Python sets this default |
| `ForeignKey("table.col")` | Links to another table's column |
| `ondelete="CASCADE"` | Delete related rows when parent is deleted |
