# 12 — Key Concepts Glossary & Quick Reference

---

> This is your cheat sheet. Whenever you forget what something means, come here first.

---

## 🔤 A–Z Glossary

---

### API (Application Programming Interface)
A set of rules that defines how two software programs talk to each other. Your FastAPI app IS an API — it defines endpoints that other apps (frontend, mobile) can call.

**Analogy:** A menu at a restaurant. It defines what you can order (endpoints), what you need to provide (request body), and what you'll get back (response).

---

### Alembic
A database migration tool for SQLAlchemy. Tracks schema changes as versioned files so you can apply, roll back, and share database changes safely.

**Commands to remember:**
```bash
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                                # Apply all migrations
alembic downgrade -1                               # Undo last migration
alembic history                                    # See all migrations
alembic current                                    # Current DB version
```

---

### Authentication vs Authorization
- **Authentication:** Proving who you are ("I am Alice")
- **Authorization:** Proving you're allowed to do something ("Alice can edit her own posts")

---

### BaseModel (Pydantic)
The parent class all Pydantic schemas inherit from. Provides:
- Automatic type validation
- JSON serialization/deserialization
- `model_dump()` → convert to dict
- `model_validate()` → create from dict

---

### bcrypt
A password hashing algorithm designed to be intentionally slow (to resist brute force attacks). Never store plain text passwords — always bcrypt them.

```python
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
is_valid = bcrypt.checkpw(plain.encode(), hashed)
```

---

### CASCADE (ondelete)
A database rule: when a parent record is deleted, automatically delete all child records too.

```python
ForeignKey("users.id", ondelete="CASCADE")
```

**Analogy:** Deleting a folder also deletes all files inside it.

---

### Column (SQLAlchemy)
Defines a single column in a database table.

```python
Column(Integer, primary_key=True, autoincrement=True)
Column(String(255), nullable=False)
Column(Boolean, server_default="1")
Column(DateTime, server_default=func.now())
Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
```

---

### Composite Primary Key
A primary key made of TWO or more columns. The combination must be unique.

Used in the `votes` table: `(user_id, post_id)` must be unique (a user can only vote once per post).

---

### Connection Pool
A cache of database connections kept ready for reuse. Instead of creating a new connection for every request (slow), requests borrow from the pool (fast).

```python
pooling.MySQLConnectionPool(pool_name="mypool", pool_size=10, ...)
```

---

### CORS (Cross-Origin Resource Sharing)
A browser security mechanism that blocks web pages from making requests to a different domain than the one that served the page.

**Solution:** `CORSMiddleware` in FastAPI tells the browser which origins are allowed.

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

---

### CRUD
Create, Read, Update, Delete — the four basic database operations.

| CRUD | HTTP Method | SQL |
|------|-------------|-----|
| Create | POST | INSERT |
| Read | GET | SELECT |
| Update | PUT/PATCH | UPDATE |
| Delete | DELETE | DELETE |

---

### Cursor (Database)
An object used to execute SQL queries and fetch results. Created from a database connection.

```python
cursor = connection.cursor(dictionary=True, prepared=True)
cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
post = cursor.fetchone()
```

---

### declarative_base (SQLAlchemy)
A function that returns a base class for all your ORM models.

```python
base = declarative_base()

class Post(base):  # Post "knows" it's a DB table because of base
    __tablename__ = "posts"
```

---

### Decorator
A Python function that wraps another function to modify its behavior.

```python
@app.get('/posts')    # ← decorator
def get_posts():      # ← decorated function
    ...
```

The `@app.get('/posts')` registers `get_posts` as handling GET requests to `/posts`.

---

### Dependency Injection (`Depends`)
FastAPI's system for automatically running helper functions and injecting their results into route functions.

```python
def get_posts(
    db: Session = Depends(get_db),              # Opens DB session
    user: User = Depends(get_current_user)       # Validates JWT, returns user
):
```

FastAPI runs `get_db()` and `get_current_user()` automatically before calling `get_posts()`.

---

### `.env` File
A plain text file containing environment-specific configuration:
```
DATABASE_PASSWORD=mysecret
SECRET_KEY=abc123...
```

Always add to `.gitignore`! Never commit secrets to version control.

---

### `EmailStr` (Pydantic)
A special string type that validates email format. Requires `email-validator` package.

```python
from pydantic import EmailStr
email: EmailStr   # "not-an-email" → ValidationError, "user@example.com" → OK
```

---

### Engine (SQLAlchemy)
The connection point between Python and the database. Created once, used by all sessions.

```python
engine = create_engine("mysql+pymysql://user:pass@host:port/db")
```

---

### ForeignKey
A column that references the primary key of another table. Enforces referential integrity.

```python
user_id = Column(Integer, ForeignKey("users.id"))
```

**Analogy:** Like a "Customer ID" field on an order form — it points to a specific customer record.

---

### Generator Function (yield)
A function that uses `yield` instead of `return`. Can pause and resume execution.

```python
def get_db():
    db = Session()
    try:
        yield db        # Pause here and return db
    finally:
        db.close()      # Run this when done (even on error)
```

FastAPI uses this pattern for dependency cleanup.

---

### HTTPException
FastAPI's way to send HTTP error responses.

```python
raise HTTPException(
    status_code=404,
    detail="Post not found"
)
```

Automatically converted to:
```json
{"detail": "Post not found"}
```

---

### HTTP Methods (Verbs)
| Method | Purpose | Has Body? |
|--------|---------|-----------|
| GET | Read data | No |
| POST | Create data | Yes |
| PUT | Replace data | Yes |
| PATCH | Partially update | Yes |
| DELETE | Remove data | No |

---

### JWT (JSON Web Token)
A digitally signed string for transmitting claims between parties.

**Structure:** `header.payload.signature`
- Header: Algorithm info
- Payload: Your data (`{"sub": "email", "exp": timestamp}`)
- Signature: Proves the token hasn't been tampered with

```python
token = jwt.encode({"sub": "alice@example.com", "exp": ...}, SECRET_KEY, "HS256")
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

---

### `JSONResponse`
A FastAPI response class for manually controlling the status code and body.

```python
return JSONResponse(
    status_code=404,
    content={"success": False, "message": "Not found"}
)
```

---

### LEFT JOIN vs INNER JOIN
- **INNER JOIN:** Only returns rows where BOTH tables have matching records
- **LEFT JOIN:** Returns ALL rows from the left table, even if no match on the right

```python
# isouter=True = LEFT JOIN (include posts with 0 votes)
.join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)
```

---

### Middleware
Code that runs on EVERY request, before it reaches your route handlers.

```python
app.add_middleware(CORSMiddleware, ...)  # Runs on every request
```

**Analogy:** A hotel receptionist who greets every guest before they reach their room.

---

### Migration (Alembic)
A versioned script that modifies the database schema (add tables, add columns, etc.).

```python
def upgrade():
    op.create_table('posts', ...)

def downgrade():
    op.drop_table('posts')
```

---

### Model (SQLAlchemy)
A Python class representing a database table. Inherits from `declarative_base()`.

```python
class Post(base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
```

---

### `model_dump()` (Pydantic)
Converts a Pydantic model instance to a Python dictionary.

```python
post = schemas.Post(title="Hello", content="World", published=True)
post.model_dump()  # → {"title": "Hello", "content": "World", "published": True}
```

---

### nullable
Whether a database column can contain NULL (missing) values.
- `nullable=False` → field is required (cannot be NULL)
- `nullable=True` → field is optional

---

### OAuth2
An authorization framework (not just for OAuth, but FastAPI uses its forms for login).

```python
OAuth2PasswordBearer(tokenUrl="login")  # Extracts Bearer tokens from requests
OAuth2PasswordRequestForm               # Parses username/password from form body
```

---

### ORM (Object-Relational Mapper)
Software that converts between Python objects and database rows. Lets you use Python instead of SQL.

```python
# ORM:
posts = db.query(models.Post).filter(models.Post.published == True).all()

# Equivalent SQL:
# SELECT * FROM posts WHERE published = true
```

---

### `Optional` (Python typing)
Means a value can be of the given type OR `None`.

```python
from typing import Optional
search: Optional[str] = ""   # Can be a string or None
```

---

### Parameterized Query
A SQL query that uses placeholders (`%s`) instead of string formatting. Prevents SQL injection.

```python
cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))  # ✅ Safe
cursor.execute(f"SELECT * FROM posts WHERE id = {id}")       # ❌ Dangerous
```

---

### Path Parameter
A variable part of a URL path.

```python
@router.get('/{id}')       # {id} is the path parameter
def get_post(id: int):     # FastAPI extracts and converts it
    ...
# GET /posts/5  →  id = 5
```

---

### prefix (Router)
Automatically prepends a path to all routes in a router.

```python
router = APIRouter(prefix="/posts")  # All routes start with /posts
@router.get('')         # → GET /posts
@router.get('/{id}')   # → GET /posts/{id}
```

---

### primary_key
The column(s) that uniquely identify each row in a table. Must be unique and NOT NULL.

---

### Prepared Statement
A SQL template compiled once and executed many times. Faster for repeated queries and prevents SQL injection.

```python
cursor = conn.cursor(prepared=True)
```

---

### Pydantic
A Python data validation library. Validates data against your type annotations at runtime.

```python
class Post(BaseModel):
    title: str      # Must be a string
    content: str    # Must be a string
    published: bool # Must be boolean (True/False)
```

---

### Query Parameter
Parameters passed in the URL after `?`.

```python
# GET /posts/orm?limit=5&skip=10&search=hello
@router.get('/orm')
def get_posts(limit: int = 10, skip: int = 0, search: str = ""):
    ...
```

---

### `relationship` (SQLAlchemy)
Defines a Python-level link between two models. Not a database column — it's a shortcut.

```python
class Post(base):
    owner = relationship("User")   # Access post.owner to get User object

# SQLAlchemy auto-queries the User when you access post.owner
```

---

### Response Model
Tells FastAPI what shape the response should be. Pydantic validates and filters the return value.

```python
@router.get('/posts', response_model=list[schemas.PostResponse])
```

Fields not in `PostResponse` are automatically excluded (e.g., `password`).

---

### Router (`APIRouter`)
A mini-application that groups related routes. Included in the main `app`.

```python
router = APIRouter(prefix="/posts", tags=["posts"])
app.include_router(router)
```

---

### Salt (bcrypt)
A random value added to a password before hashing. Makes identical passwords hash to different values.

---

### Schema (Pydantic)
A class defining the expected shape of data. Used for input validation and output serialization.

---

### `server_default`
A default value set by the **database** when inserting a row (not by Python).

```python
published = Column(Boolean, server_default="1")      # DB sets to 1 (True)
created_at = Column(DateTime, server_default=func.now())  # DB sets to current time
```

---

### Session (SQLAlchemy)
The main interface for ORM operations. A "conversation" with the database.

```python
db = session()
db.add(obj)    # Stage for INSERT
db.commit()    # Execute and save
db.rollback()  # Undo pending changes
db.close()     # End the session
```

---

### `sessionmaker`
A factory that creates Session instances. Configure once, use everywhere.

```python
session = sessionmaker(bind=engine)  # Factory
db = session()                       # Create an instance
```

---

### SQL Injection
A security attack where malicious SQL is inserted into a query via user input.

```python
# User sends: id = "1; DROP TABLE posts"
# ❌ Dangerous:
cursor.execute(f"DELETE FROM posts WHERE id = {id}")
# → DELETE FROM posts WHERE id = 1; DROP TABLE posts

# ✅ Safe (parameterized):
cursor.execute("DELETE FROM posts WHERE id = %s", (id,))
# The semicolon and everything after is treated as literal data, not SQL
```

---

### Status Codes (Quick Ref)
| Code | Meaning | Use When |
|------|---------|----------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (new resource) |
| 401 | Unauthorized | Not logged in |
| 403 | Forbidden | Logged in but not allowed |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., already voted) |
| 422 | Unprocessable | Pydantic validation failed |
| 500 | Server Error | Unexpected crash |

---

### `unique=True` (SQLAlchemy)
Enforces that all values in a column are unique across all rows.

```python
email = Column(String(254), unique=True)  # No duplicate emails allowed
```

---

### Uvicorn
An ASGI (Asynchronous Server Gateway Interface) web server. Runs your FastAPI app.

```bash
uvicorn app.main:app --reload
#        ^^^^^^^^^^^  ^^^^^^^
#        app.main:app  auto-reload on changes
```

---

## 🗂️ Files Quick Reference

| File | Purpose | Key Things |
|------|---------|------------|
| `main.py` | App entry point | Creates `app`, adds middleware, includes routers |
| `database.py` | DB connections | `engine`, `get_db()`, `get_raw_db()`, connection pool |
| `models.py` | DB table definitions | `Post`, `User`, `Vote` SQLAlchemy models |
| `schemas.py` | Data validation | Pydantic schemas for requests and responses |
| `config.py` | App settings | `Settings` class reads from `.env` |
| `utils.py` | Helper functions | `hash_password()`, `verify_password()` |
| `routers/auth.py` | Login endpoint | `POST /login` → returns JWT |
| `routers/oauth2.py` | JWT handling | `create_access_token()`, `get_current_user()` |
| `routers/posts.py` | Post CRUD | GET/POST/PUT/DELETE for posts |
| `routers/users.py` | User endpoints | Register + lookup users |
| `routers/vote.py` | Voting | Add/remove votes on posts |
| `alembic/env.py` | Alembic config | Links migrations to your models |
| `alembic/versions/` | Migration scripts | Each file = one schema change |

---

## 🔄 Common Patterns — Cheat Sheet

### Creating a Resource (ORM)
```python
new_obj = models.SomeModel(**schema.model_dump())
db.add(new_obj)
db.commit()
db.refresh(new_obj)
return new_obj
```

### Querying (ORM)
```python
# All records:
db.query(models.Post).all()

# With filter:
db.query(models.Post).filter(models.Post.id == id).first()

# With search:
db.query(models.Post).filter(models.Post.title.contains("hello")).all()

# With pagination:
db.query(models.Post).offset(skip).limit(limit).all()
```

### Querying (Raw SQL)
```python
cur.execute("SELECT * FROM posts WHERE id = %s", (id,))
post = cur.fetchone()   # One row
posts = cur.fetchall()  # All rows
```

### Update (ORM)
```python
query = db.query(models.Post).filter(models.Post.id == id)
query.update(schema.model_dump(), synchronize_session=False)
db.commit()
```

### Delete (ORM)
```python
post = db.query(models.Post).filter(models.Post.id == id).first()
db.delete(post)
db.commit()
```

### Protected Route
```python
@router.get('/protected')
def protected_route(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)  # Auth guard
):
    # Only runs if JWT is valid
    return {"email": current_user.email}
```
