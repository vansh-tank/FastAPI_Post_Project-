# 📚 FastAPI Post Project — Complete Learning Notes

> **Who these notes are for:** Complete beginners who want to understand how a real-world FastAPI REST API works from the ground up.
> **Project:** A social-media-style Post API where users can register, login, create posts, and vote on them.

---

## 📂 Table of Contents

| # | File | What You'll Learn |
|---|------|-------------------|
| 01 | [01_PROJECT_OVERVIEW.md](./01_PROJECT_OVERVIEW.md) | Big picture, what the app does, folder structure |
| 02 | [02_FASTAPI_BASICS.md](./02_FASTAPI_BASICS.md) | What FastAPI is, how it works, entry point `main.py` |
| 03 | [03_DATABASE_AND_ORM.md](./03_DATABASE_AND_ORM.md) | MySQL, SQLAlchemy ORM, connection pools, `database.py` |
| 04 | [04_MODELS.md](./04_MODELS.md) | Database models (`models.py`) — your tables in Python |
| 05 | [05_SCHEMAS_PYDANTIC.md](./05_SCHEMAS_PYDANTIC.md) | Pydantic schemas (`schemas.py`) — input/output validation |
| 06 | [06_CONFIG_AND_ENV.md](./06_CONFIG_AND_ENV.md) | App configuration, environment variables, `config.py` |
| 07 | [07_AUTHENTICATION_JWT.md](./07_AUTHENTICATION_JWT.md) | Passwords, JWT tokens, login flow — `auth.py`, `oauth2.py`, `utils.py` |
| 08 | [08_ROUTERS_POSTS.md](./08_ROUTERS_POSTS.md) | Full CRUD for Posts — raw SQL vs ORM side by side |
| 09 | [09_ROUTERS_USERS_VOTE.md](./09_ROUTERS_USERS_VOTE.md) | User registration, lookup, voting system |
| 10 | [10_ALEMBIC_MIGRATIONS.md](./10_ALEMBIC_MIGRATIONS.md) | Database migrations — Alembic explained simply |
| 11 | [11_SQL_LEARN.md](./11_SQL_LEARN.md) | Raw SQL vs ORM — the learning experiments in `SQL_learn/` |
| 12 | [12_KEY_CONCEPTS_GLOSSARY.md](./12_KEY_CONCEPTS_GLOSSARY.md) | Quick-reference glossary of every concept used |
| 13 | [13_DOCKER_AND_COMPOSE.md](./13_DOCKER_AND_COMPOSE.md) | Containerization with Docker & Docker Compose |
| 14 | [14_TESTING_PYTEST.md](./14_TESTING_PYTEST.md) | Automated testing with Pytest, fixtures, TestClient & isolated DB |
| 15 | [15_CI_CD_GITHUB_ACTIONS.md](./15_CI_CD_GITHUB_ACTIONS.md) | CI/CD with GitHub Actions, MySQL services, Docker build/push, & deploy |

---

## 🗺️ How the App Works (The Big Flow)

```
Client (Browser / Postman)
        │
        ▼
   FastAPI App (main.py)
        │
   ┌────┴────────────────────────────────┐
   │              Routers                │
   │  /posts  /users  /login  /vote      │
   └────┬──────────┬──────────┬──────────┘
        │          │          │
    Depends    Depends    Depends
    (get_db)  (oauth2)   (schemas)
        │
   SQLAlchemy ORM  OR  Raw MySQL Cursor
        │
     MySQL Database
```

---

## 🏗️ Project Tech Stack

| Technology | Role |
|------------|------|
| **FastAPI** | Web framework — handles HTTP requests/responses |
| **Pydantic v2** | Data validation — checks inputs and shapes outputs |
| **SQLAlchemy** | ORM — lets you talk to a database using Python objects |
| **MySQL** | The actual database that stores data |
| **PyMySQL** | Python driver that connects to MySQL |
| **Alembic** | Database migration tool — safely evolves your schema |
| **python-jose** | Creates and verifies JWT tokens |
| **bcrypt** | Hashes passwords so they're never stored in plain text |
| **pydantic-settings** | Loads config from `.env` files |
| **Uvicorn** | ASGI server that actually *runs* FastAPI |
| **Docker & Compose** | Containerization and multi-service orchestration |

---

## ⚡ Quick Start Recap

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload

# View interactive docs
open http://127.0.0.1:8000/docs
```
