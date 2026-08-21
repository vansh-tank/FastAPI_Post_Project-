# 01 — Project Overview: What Are We Building?

---

## 🎯 The Big Picture

Think of this project like a **mini Reddit or Twitter backend**.

Users can:
1. **Register** an account (email + password)
2. **Login** and get a token (like a wristband at an event)
3. **Create posts** (like tweets or Reddit posts)
4. **Read** their posts and others'
5. **Update or delete** their own posts
6. **Vote** on posts (like Reddit upvotes/downvotes)

This is **not a frontend app** — it's a **REST API**. That means it speaks in JSON and other apps (React, mobile, Postman) call it.

---

## 📁 Folder Structure — The Map of the Code

```
FastAPI_Post_Project-/
│
├── app/                        ← The heart of the application
│   ├── main.py                 ← Entry point — where the app starts
│   ├── models.py               ← Database table definitions (Python classes)
│   ├── schemas.py              ← Input/output shape definitions (validation)
│   ├── database.py             ← Database connection setup
│   ├── config.py               ← App settings loaded from .env
│   ├── utils.py                ← Helper functions (e.g., hashing passwords)
│   ├── .env                    ← Secret settings file (NOT committed to git)
│   └── routers/                ← Route handlers split by feature
│       ├── posts.py            ← All post endpoints (CRUD)
│       ├── users.py            ← User registration and lookup
│       ├── auth.py             ← Login endpoint
│       ├── oauth2.py           ← JWT token creation and verification
│       └── vote.py             ← Voting logic
│
├── alembic/                    ← Database migration scripts
│   ├── env.py                  ← Alembic config (links to our models)
│   └── versions/               ← Individual migration files
│       ├── e7242895bbf3_create_post_table.py
│       ├── 04cfff068645_create_users_table.py
│       └── d623d442a72d_create_votes_table.py
│
├── SQL_learn/                  ← Experimental/learning scripts (not production)
│   ├── orm.py                  ← ORM experiments
│   └── sql.py                  ← Raw SQL experiments
│
├── alembic.ini                 ← Alembic configuration file
└── requirements.txt            ← All Python packages this project needs
```

---

## 🗄️ Database Schema — The Three Tables

Think of a database as a spreadsheet book. Each **table** is one sheet.

### `users` table
```
+----+-------------------+----------------+---------------------+
| id | email             | password       | created_at          |
+----+-------------------+----------------+---------------------+
|  1 | alice@example.com | $2b$12$...     | 2026-06-01 10:00:00 |
|  2 | bob@example.com   | $2b$12$...     | 2026-06-01 11:00:00 |
+----+-------------------+----------------+---------------------+
```

### `posts` table
```
+----+-----------+---------+-----------+---------------------+---------+
| id | title     | content | published | created_at          | user_id |
+----+-----------+---------+-----------+---------------------+---------+
|  1 | My Post   | Hello!  | 1         | 2026-06-01 12:00:00 | 1       |
|  2 | Another   | World!  | 1         | 2026-06-01 13:00:00 | 1       |
+----+-----------+---------+-----------+---------------------+---------+
       ↑ user_id links back to users.id (Foreign Key)
```

### `votes` table
```
+---------+---------+
| user_id | post_id |
+---------+---------+
|       1 |       2 |  ← User 1 voted on Post 2
|       2 |       1 |  ← User 2 voted on Post 1
+---------+---------+
  ↑ Both columns together = composite primary key (unique pair)
```

---

## 🔗 Relationships Between Tables

```
users ──── has many ──→ posts   (one user owns many posts)
users ──── has many ──→ votes   (one user can vote many times)
posts ──── has many ──→ votes   (one post can receive many votes)
```

**Analogy:** Think of `users` as authors, `posts` as their articles, and `votes` as readers clicking the ❤️ button on articles.

---

## 🌐 API Endpoints Overview

| Method | Path | Auth Required | What it Does |
|--------|------|:---:|--------------|
| GET | `/` | ❌ | Health check / welcome message |
| POST | `/users/` | ❌ | Register a new user |
| GET | `/users/{id}` | ❌ | Get a user by ID |
| POST | `/login` | ❌ | Login and get JWT token |
| GET | `/posts` | ✅ | Get your posts (raw SQL) |
| GET | `/posts/orm` | ✅ | Get all posts with vote count (ORM) |
| POST | `/posts` | ✅ | Create a new post (raw SQL) |
| POST | `/posts/orm` | ✅ | Create a new post (ORM) |
| GET | `/posts/{id}` | ✅ | Get a specific post by ID |
| GET | `/posts/orm/{id}` | ✅ | Get a specific post (ORM) |
| DELETE | `/posts/{id}` | ✅ | Delete your post |
| DELETE | `/posts/orm/{id}` | ✅ | Delete your post (ORM) |
| PUT | `/posts/{id}` | ✅ | Update your post |
| PUT | `/posts/orm/{id}` | ✅ | Update your post (ORM) |
| POST | `/vote/` | ✅ | Vote or un-vote on a post |

> **Note:** The project has **two implementations** of most post endpoints — one using raw SQL and one using the ORM. This was done intentionally as a learning exercise. In production you'd pick one.

---

## 🔒 Authentication Flow (How Login Works)

```
1. User sends: POST /login {email, password}
2. Server checks password against hashed DB password
3. Server creates JWT token: {sub: email, exp: 30min}
4. User gets token back
5. User sends token in header for protected routes:
   Authorization: Bearer eyJhbGci...
6. Server decodes token → gets email → looks up user
7. If valid → route proceeds; if not → 401 Unauthorized
```

**Analogy:** The JWT token is like a **concert wristband**. You show your ID once (login), get a wristband (token), and then flash it at every gate (protected route) without showing your ID again.
