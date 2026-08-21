# 03 — Database & ORM: `database.py` Explained

---

## 🤔 What is a Database Driver vs an ORM?

Before diving in, understand these two different ways to talk to a database:

### Way 1: Raw SQL (Direct)
```python
cursor.execute("SELECT * FROM posts WHERE id = 5")
post = cursor.fetchone()
```
You write SQL directly. You get back raw dictionaries.

### Way 2: ORM (Object-Relational Mapper)
```python
post = db.query(models.Post).filter(models.Post.id == 5).first()
```
You write Python. The ORM translates it to SQL for you.

**Analogy:** 
- Raw SQL = speaking directly to the chef in the kitchen (fast, precise, but complex)
- ORM = ordering from a menu (easier, safer, but sometimes less flexible)

This project does **both** — which is great for learning!

---

## 📄 The `database.py` File — Full Breakdown

### Part 1: Imports

```python
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from mysql.connector import Error, pooling
import time
from .config import settings
```

| Import | What it does |
|--------|-------------|
| `create_engine` | Creates the "engine" — the connection point to your database |
| `declarative_base` | Creates a base class that your models will inherit from |
| `sessionmaker` | Factory for creating database sessions |
| `pooling` | MySQL's built-in connection pool system |
| `Error` | MySQL-specific exception class |
| `settings` | Our app config (db credentials) |

---

### Part 2: SQLAlchemy Engine

```python
engine = create_engine(
    f"mysql+pymysql://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)
```

The URL format is: `dialect+driver://user:password@host:port/database`

Breaking down each piece:
| Part | Value | Meaning |
|------|-------|---------|
| `mysql` | MySQL | The database type |
| `pymysql` | PyMySQL | The Python driver library |
| `settings.database_username` | `root` | DB username |
| `settings.database_password` | `vanshtank` | DB password |
| `settings.database_hostname` | `localhost` | DB server address |
| `settings.database_port` | `3306` | MySQL's default port |
| `settings.database_name` | `FastAPI` | The specific database name |

**Analogy:** The engine URL is like a postal address. It tells SQLAlchemy exactly where to "deliver" every database query.

> **Security Note:** Notice the password is coming from `settings`, which reads from `.env`. Never hardcode passwords in source code!

---

### Part 3: Session Factory and Base

```python
session = sessionmaker(bind=engine)
base = declarative_base()
```

- **`session`** (lowercase) = a factory. Think of it as a blueprint for making database "conversations."
- **`base`** = a parent class for all your models. When you define `class Post(base)`, you're telling SQLAlchemy that `Post` is a database table.

---

### Part 4: The ORM Dependency — `get_db()`

```python
def get_db():
    db = session()       # Create a new database session
    try:
        yield db         # Give it to the route function
    finally: 
        db.close()       # Always close it, even if an error occurs
```

This is a **generator function** (uses `yield` instead of `return`).

**How it's used:**
```python
@router.get('/posts')
def get_posts(db: Session = Depends(get_db)):
    # db is now an open database session
    posts = db.query(models.Post).all()
    # db is automatically closed after this function ends
```

**Analogy:** `get_db()` is like a library book checkout system:
1. You check out the book (`db = session()`)
2. You use it (`yield db`)
3. No matter what, it gets returned to the library (`db.close()`)

The `Depends(get_db)` in the route tells FastAPI: "Before running this route, run `get_db()` and inject the result as `db`."

---

### Part 5: The Connection Pool — Raw MySQL

```python
db_pool = None
for _ in range(5):       # Try up to 5 times
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,         # Keep 10 connections ready
            host="localhost",
            user="root",
            password="vanshtank",
            database="FastAPI",
            port=3306
        )
        print('MySQL Connection Pool created successfully')
        break
    except Error as e:
        print(f"Error creating MySQL Connection Pool: {e}")
        time.sleep(2)   # Wait 2 seconds before retrying
```

### What is a Connection Pool?

**Analogy:** A connection pool is like a taxi fleet parked outside an airport.

Without a pool: Every customer (request) has to call a taxi company, wait for a car to arrive, use it, and send it away. Very slow!

With a pool: 10 taxis are ALWAYS parked outside (pool_size=10). When a customer arrives, they grab a taxi. When done, the taxi goes back to the parking lot (not dismissed).

### Why the retry loop?
Sometimes the database server isn't ready yet (especially in Docker environments). The `for _ in range(5)` loop tries 5 times with 2-second waits. `_` is used as the variable name when you don't care about the value (it's a Python convention).

---

### Part 6: Legacy Globals (For Backward Compatibility)

```python
db = db_pool.get_connection()
cursor = db.cursor(dictionary=True, prepared=True)
print('retro database connected successfully (legacy global)')
```

These exist for backward compatibility — early in the project, routes used a single global connection. This is **NOT thread-safe** for production use (two requests could interfere with each other).

- `dictionary=True` → Returns rows as `{"column": value}` dicts instead of tuples
- `prepared=True` → Uses prepared statements (faster + prevents SQL injection)

---

### Part 7: The Raw SQL Dependency — `get_raw_db()`

```python
def get_raw_db():
    conn = db_pool.get_connection()          # Get a connection from the pool
    cur = conn.cursor(dictionary=True, prepared=True)  # Create a cursor
    try:
        yield conn, cur                      # Give both to the route
    finally:
        cur.close()                          # Always close cursor
        conn.close()                         # Always return connection to pool
```

This is the thread-safe way to use raw SQL. Each request gets its own connection from the pool.

**Usage in routes:**
```python
def get_posts(db_raw: tuple = Depends(get_raw_db)):
    conn, cur = db_raw   # Unpack the tuple
    cur.execute('SELECT * FROM posts')
    posts = cur.fetchall()
```

---

## 🔄 ORM vs Raw SQL — When to Use Which

| Scenario | ORM | Raw SQL |
|----------|-----|---------|
| Simple CRUD | ✅ Great | ✅ OK |
| Complex joins | ⚠️ Can get messy | ✅ Easier to read |
| Learning SQL | ❌ | ✅ |
| Auto-validation | ✅ | ❌ Manual |
| Database portability | ✅ Switch DB easily | ❌ Tied to MySQL syntax |
| Performance tuning | ⚠️ Less control | ✅ Full control |

---

## 🛡️ SQL Injection — Why We Use `%s` Placeholders

```python
# ❌ DANGEROUS — SQL Injection vulnerable:
cur.execute(f"SELECT * FROM posts WHERE id = {user_id}")

# ✅ SAFE — Parameterized query:
cur.execute("SELECT * FROM posts WHERE id = %s", (user_id,))
```

If a hacker sends `user_id = "1; DROP TABLE posts"`, the first version would delete your table! The second version escapes the input safely.

**Analogy:** SQL injection is like a customer at a restaurant writing their order as: "One burger; also burn the kitchen down." Parameterized queries make sure the kitchen reads it as a literal order, not instructions.
