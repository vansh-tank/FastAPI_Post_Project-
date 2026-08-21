# 05 — Pydantic Schemas: `schemas.py` Explained

---

## 🤔 What Are Pydantic Schemas?

**Pydantic** is a data validation library. A **schema** is a class that defines:
1. **What data you accept** (input validation)
2. **What data you return** (output shaping)

**Analogy:** Think of schemas like a **customs form** at an airport:
- When entering (request): You fill out exactly what's required. Wrong format → rejected.
- When leaving (response): The response is packed in a specific format. No extras, no missing fields.

---

## 📦 The Import

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Any
```

| Import | Purpose |
|--------|---------|
| `BaseModel` | Parent class for all schemas |
| `EmailStr` | Special string type that validates email format |
| `datetime` | Python's date/time type |
| `Optional` | Makes a field optional (can be `None`) |

---

## 👤 User-Related Schemas

### `User` — For Creating a User (Input)

```python
class User(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True
```

This is what you send when registering:
```json
{
    "email": "alice@example.com",
    "password": "mysecretpassword"
}
```

- `EmailStr` → Pydantic automatically validates the email format. `"not-an-email"` would be **rejected** with a clear error.
- The `class Config: from_attributes = True` → Tells Pydantic it can read data from SQLAlchemy model objects (not just dicts). This is needed for ORM compatibility.

> **Security Note:** Even though `password` is accepted here, it's **immediately hashed** in the route before saving. The plain text is never stored.

---

### `UserResponse` — What Gets Returned About a User (Output)

```python
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True
```

Notice: `password` is **intentionally absent**! When the API returns user data, it never exposes the password (even the hashed one).

```json
{
    "id": 1,
    "email": "alice@example.com",
    "created_at": "2026-06-01T10:00:00"
}
```

**Analogy:** Like a membership card — it shows your name and member ID, but never your PIN.

---

## 📝 Post-Related Schemas

### `Post` — For Creating/Updating a Post (Input)

```python
class Post(BaseModel):
    title: str
    content: str
    published: bool = True
```

- `published: bool = True` → The `= True` is a **default value**. If you don't include `published` in your request, it defaults to `True`.

```json
{
    "title": "My First Post",
    "content": "Hello World!"
}
```
↑ This is valid! `published` will be `true` automatically.

---

### `PostResponse` — What Gets Returned for a Post (Output)

```python
class PostResponse(Post):   # Inherits from Post!
    id: int
    created_at: datetime
    user_id: int
    owner: UserResponse     # Nested schema!

    class Config:
        from_attributes = True
```

#### Key concepts here:

**1. Inheritance** — `PostResponse(Post)` means it has everything `Post` has PLUS the extra fields.

So `PostResponse` has: `title`, `content`, `published` (from `Post`) + `id`, `created_at`, `user_id`, `owner` (added here).

**2. Nested Schema** — `owner: UserResponse` means the response contains a full user object nested inside it!

```json
{
    "id": 1,
    "title": "My First Post",
    "content": "Hello World!",
    "published": true,
    "created_at": "2026-06-01T12:00:00",
    "user_id": 1,
    "owner": {
        "id": 1,
        "email": "alice@example.com",
        "created_at": "2026-06-01T10:00:00"
    }
}
```

**Analogy:** It's like a pizza order receipt — it shows the pizza details AND the customer details nested inside the same document.

---

### `PostOut` — Post With Vote Count (ORM Route)

```python
class PostOut(BaseModel):
    Post: PostResponse   # Note: capital P — it's the field name!
    votes: int

    class Config:
        from_attributes = True
```

This is returned by the `/posts/orm` route which does a JOIN with the votes table.

```json
{
    "Post": {
        "id": 1,
        "title": "My First Post",
        ...
    },
    "votes": 42
}
```

> **Gotcha:** Notice `Post` (capital P) as a field name is unusual in JSON. This is because SQLAlchemy returns query results as tuples of `(Post_object, vote_count)` and Pydantic maps them directly.

---

## 🔐 Authentication Schemas

### `UserLogin` — Login Request

```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

```json
{
    "email": "alice@example.com",
    "password": "mysecretpassword"
}
```

Note: The auth route actually uses `OAuth2PasswordRequestForm` from FastAPI (not this schema) for the login endpoint. `UserLogin` exists as an alternative.

---

### `Token` — Login Response (Inherits from `MessageResponse`)

```python
class Token(MessageResponse):
    access_token: str
    token_type: str
```

`MessageResponse` has `message: str`, so `Token` has:

```json
{
    "message": "Login successful",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

**Analogy:** Like getting a receipt that says "Transaction approved" + your receipt number (token).

---

### `TokenData` — Internal Token Payload

```python
class TokenData(BaseModel):
    email: Optional[EmailStr] = None
```

This is NOT sent to clients. It's used **internally** to hold decoded token data.

When a JWT token is decoded, the payload might contain `{"sub": "alice@example.com"}`. `TokenData` wraps that email for type safety within Python.

---

## 🗳️ Vote Schema

```python
class Vote(BaseModel):
    post_id: int
    dir: int       # 1 = vote, 0 = unvote
```

```json
{
    "post_id": 5,
    "dir": 1
}
```

`dir` stands for "direction":
- `dir = 1` → Add a vote (like a Reddit upvote)
- `dir = 0` → Remove a vote

---

## 📤 Response Wrapper Schemas

### `MessageResponse`
```python
class MessageResponse(BaseModel):
    message: str
```
Simple success messages:
```json
{"message": "Post created successfully"}
```

### `CreatePostResponse`
```python
class CreatePostResponse(BaseModel):
    message: str
    post: PostResponse
```
Returns a message + the created post:
```json
{
    "message": "Post created successfully",
    "post": { ... full post object ... }
}
```

### `SinglePostResponse`
```python
class SinglePostResponse(BaseModel):
    success: bool
    response: Optional[PostResponse | str] = None
```
The `response` field can be EITHER a `PostResponse` object OR a string (like an error message). This is Python's **Union type** using `|`.

```json
// Success:
{"success": true, "response": { ... post object ... }}

// Not found:
{"success": false, "response": "id:99 not found"}
```

### `ActionResponse`
```python
class ActionResponse(BaseModel):
    success: bool
    message: str
```
For update/delete operations:
```json
{"success": true, "message": "Post with id 5 deleted successfully"}
```

---

## 🔄 Schema Inheritance Tree

```
BaseModel
├── User                  (input: create user)
├── UserResponse          (output: return user)
├── MessageResponse       (output: simple message)
│   └── Token             (output: JWT token)
├── Post                  (input: create/update post)
│   └── PostResponse      (output: return post)
├── PostOut               (output: post + votes)
├── SinglePostResponse    (output: one post or error)
├── CreatePostResponse    (output: message + post)
├── ActionResponse        (output: success + message)
├── UserLogin             (input: login)
├── TokenData             (internal: decoded token)
└── Vote                  (input: vote action)
```

---

## ⚙️ `class Config: from_attributes = True`

This is required on schemas that will be populated from SQLAlchemy model objects.

**Without it:** Pydantic expects a plain dict: `{"id": 1, "title": "..."}`.

**With it:** Pydantic can also read SQLAlchemy objects: `post.id`, `post.title` (attribute access).

If you're getting `response_model` errors, this is often the missing piece!

**Analogy:** It's like telling your translator: "These instructions might come in either written form (dict) or spoken form (object attributes) — understand both."
