# 06 — Configuration & Environment Variables: `config.py`

---

## 🤔 Why Do We Need Configuration?

Imagine you have:
- A database password in your code
- You push to GitHub
- The whole world can now see your password!

Or imagine deploying to production — your production database has a different password than your local one. Do you edit the code every time?

**Solution: Environment Variables + `.env` files**

**Analogy:** Configuration is like a recipe card holder. The recipe (code) stays the same, but you swap the ingredient cards (config values) depending on if you're cooking for dinner at home (development) or at a restaurant (production).

---

## 📄 The `config.py` File — Full Breakdown

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_username: str = "root"
    database_password: str = "vanshtank"
    database_port: str = "3306"
    database_name: str = "FastAPI"
    database_hostname: str = "localhost"
    secret_key: str = "secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 🏗️ `BaseSettings` — Pydantic's Configuration Superpower

`pydantic_settings.BaseSettings` is a special class that:
1. Reads from **environment variables** first
2. Falls back to the **`.env` file**
3. Falls back to the **default values** in the class

The priority order:
```
Environment Variable > .env File > Default Value in Code
```

**Analogy:** Think of it as looking for your keys:
1. Check your pocket (env variable) → Found? Use it.
2. Check the key hook by the door (.env file) → Found? Use it.
3. Check the junk drawer (default in code) → Use that.

---

## 🔑 Each Setting Explained

### Database Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `database_username` | `"root"` | MySQL username |
| `database_password` | `"vanshtank"` | MySQL password |
| `database_port` | `"3306"` | MySQL port (3306 is default) |
| `database_name` | `"FastAPI"` | Database name to connect to |
| `database_hostname` | `"localhost"` | Where the DB server is running |

### JWT Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `secret_key` | `"secret"` | Secret used to sign JWT tokens |
| `algorithm` | `"HS256"` | Algorithm used to sign/verify tokens |
| `access_token_expire_minutes` | `30` | How long login tokens last |

> **⚠️ Security Alert:** The default `secret_key = "secret"` is terrible for production! Anyone who knows this secret can forge tokens. In production, use a long random string like `openssl rand -hex 32`.

---

## 📁 The `.env` File (Not in Version Control)

The `.env` file lives at `app/.env` and looks like:

```env
DATABASE_USERNAME=root
DATABASE_PASSWORD=vanshtank
DATABASE_PORT=3306
DATABASE_NAME=FastAPI
DATABASE_HOSTNAME=localhost
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Notice:** Environment variable names are `UPPERCASE` but pydantic-settings automatically matches them case-insensitively to the lowercase field names in the Settings class.

### Why the `.env` is in `.gitignore`
The `.gitignore` file lists files that Git should NOT track. Your `.env` should always be in `.gitignore` so:
- Your passwords never get committed to GitHub
- Different developers can have different local settings

---

## 🌐 The Singleton Pattern

```python
settings = Settings()  # Create ONE instance at the bottom
```

By creating `settings` at module level, it's loaded ONCE when Python imports this file. Every other file that does `from .config import settings` gets the **same** object (Python caches module imports).

**Analogy:** Like posting the company rules on the bulletin board once — everyone reads from the same board.

---

## 🔄 How Settings Flow Through the App

```
.env file
    ↓ (read by)
Settings class (config.py)
    ↓ (imported by)
├── database.py     → uses database_* settings for connection URL
└── routers/oauth2.py → uses secret_key, algorithm, expire_minutes for JWT
```

---

## 🛡️ Production vs Development Settings

In a real project, you'd have different settings for different environments:

```
# Development (.env.development)
DATABASE_HOSTNAME=localhost
DATABASE_PASSWORD=simple_password
SECRET_KEY=dev_secret

# Production (.env.production)  
DATABASE_HOSTNAME=prod-db.aws.com
DATABASE_PASSWORD=xK3!mN9@pQr7...
SECRET_KEY=a5b2c8d1e9f3g7h4i0j6k2l8m1n5...
```

---

## 💡 Type Annotations in Settings

```python
database_username: str = "root"
access_token_expire_minutes: int = 30
```

Pydantic will:
- Automatically **convert** the `.env` value `"30"` (a string) to `int` `30`
- **Reject** the app startup if `access_token_expire_minutes` is set to `"thirty"` (not a valid int)

This catches configuration errors at startup, not buried in runtime errors!

**Analogy:** Like a pre-flight checklist — the plane won't take off if any check fails.

---

## 📝 Using Settings in Other Files

```python
# In database.py:
from .config import settings

engine = create_engine(
    f"mysql+pymysql://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)

# In oauth2.py:
from ..config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
```

The settings are accessed as plain object attributes — clean and readable.
