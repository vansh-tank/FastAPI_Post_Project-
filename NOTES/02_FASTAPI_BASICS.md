# 02 — FastAPI Basics & `main.py` Explained

---

## 🤔 What is FastAPI?

FastAPI is a **web framework** for Python. A web framework is like a toolbox that handles the boring repetitive stuff (parsing HTTP requests, validating inputs, generating docs) so you can focus on *your* business logic.

**Analogy:** Imagine you're opening a restaurant. You don't build the kitchen from scratch — you buy equipment. FastAPI is the kitchen equipment for web APIs.

### Why FastAPI is special:
| Feature | What it means for you |
|---------|----------------------|
| **Fast** | One of the fastest Python frameworks (powered by Starlette + Uvicorn) |
| **Auto Documentation** | Visit `/docs` and get a free Swagger UI |
| **Type hints** | Write normal Python types, FastAPI validates everything automatically |
| **Async support** | Can handle many requests at once without blocking |

---

## 🚀 How a FastAPI App Starts

When you run:
```bash
uvicorn app.main:app --reload
```

This means:
- `uvicorn` → the web server that listens for HTTP connections
- `app.main` → the Python module `app/main.py`
- `:app` → the variable named `app` inside that module
- `--reload` → auto-restart on code changes (development only)

---

## 📄 The `main.py` File — Line by Line

```python
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from . import models 
from .database import engine
from . import schemas
from .routers import posts, users, auth, vote
from .config import settings
```

### What are these imports?
- `FastAPI` → the main class that creates your API application
- `status` → a collection of HTTP status codes (200, 201, 404, etc.) as readable names
- `CORSMiddleware` → handles browser security rules (explained below)
- `models` → your database table definitions
- `engine` → the SQLAlchemy database connection engine
- `schemas` → your Pydantic input/output validation models
- `posts, users, auth, vote` → your route handlers split into files
- `settings` → your app configuration

---

## 🏗️ Creating the App Instance

```python
app = FastAPI()
```

**Analogy:** This is like opening your restaurant. `app` is now your restaurant object — you'll attach menus (routes), rules (middleware), etc. to it.

---

## 🌐 CORS Middleware — The Browser Security Guard

```python
origin = ['https://www.google.com', 'https://www.youtube.com']

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # Allow ALL origins
    allow_credentials=True,
    allow_methods=["*"],    # Allow ALL HTTP methods
    allow_headers=["*"],    # Allow ALL headers
)
```

### What is CORS?
**CORS (Cross-Origin Resource Sharing)** is a browser security feature. When your React app at `http://localhost:3000` tries to call your API at `http://localhost:8000`, the browser blocks it by default, thinking it might be malicious.

**Analogy:** CORS is like a nightclub bouncer. Without CORS config, the bouncer blocks everyone from a different neighbourhood. Setting `allow_origins=["*"]` tells the bouncer: "let everyone in."

### The `origin` variable — a mistake to learn from
Notice the code creates an `origin` variable but never uses it! The actual middleware uses `["*"]` (allow all). The commented intent was to restrict which websites can call the API. This is left as a learning artifact showing the difference between:
- `["*"]` → anyone can call your API from any website
- `['https://www.google.com']` → only Google's website can call your API

> **Security Note:** In production, replace `["*"]` with your actual frontend domain!

---

## 🚫 Why `models.base.metadata.create_all(bind=engine)` is Commented Out

```python
# models.base.metadata.create_all(bind=engine)
# alembic can handle database migrations, so we don't need to create tables manually here.
```

This line would tell SQLAlchemy to **automatically create all database tables** based on your models. However, it's commented out because the project uses **Alembic** for migrations instead.

**Analogy:** 
- `create_all` = bulldozing and rebuilding your entire house
- Alembic = renovating room by room, keeping history of every change

---

## 🔗 Including Routers

```python
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(vote.router)
```

**Routers** are like chapters in a book. Instead of putting all 300+ lines of route code in `main.py`, you split them into separate files and then "include" them here.

Each router has a `prefix` (e.g., `/posts`) so all routes in `posts.router` automatically start with `/posts`.

---

## ✅ Your First Route

```python
@app.get('/', status_code=status.HTTP_200_OK, response_model=schemas.MessageResponse)
def root():
    return {'message': 'Welcome to my API!'}
```

### Breaking it down:

| Part | Meaning |
|------|---------|
| `@app.get('/')` | **Decorator** — registers this function as handling GET requests to `/` |
| `status_code=status.HTTP_200_OK` | The HTTP response code to return (200 = success) |
| `response_model=schemas.MessageResponse` | The shape of the JSON this returns |
| `def root():` | The actual function that runs when someone hits `/` |
| `return {'message': '...'}` | FastAPI converts this dict to JSON automatically |

**Analogy:** The decorator `@app.get('/')` is like pinning a sign on a door that says "GET requests knock here." When someone knocks, the `root()` function answers.

---

## 📊 HTTP Status Codes — The Language of the Web

| Code | Name | Meaning |
|------|------|---------|
| 200 | OK | Success |
| 201 | Created | Something new was created |
| 204 | No Content | Success but nothing to return |
| 400 | Bad Request | You sent bad data |
| 401 | Unauthorized | You're not logged in |
| 403 | Forbidden | You're logged in but not allowed |
| 404 | Not Found | The resource doesn't exist |
| 409 | Conflict | Duplicate resource conflict |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Internal Server Error | Something broke on the server |

---

## 🔄 Request/Response Lifecycle

```
1. Request comes in: GET /posts
2. FastAPI matches URL to router function
3. Dependency injection runs (get_db, get_current_user)
4. Function body executes
5. Return value validated against response_model
6. JSON response sent back to client
```

Every step is handled automatically by FastAPI — you just write the function body!

---

## 📖 Auto-Generated Documentation

FastAPI automatically generates interactive documentation:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

These are real, interactive UIs where you can test every endpoint without writing any code. This is FREE and auto-generated from your code.
