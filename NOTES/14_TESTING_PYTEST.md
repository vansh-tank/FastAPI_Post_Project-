# 🧪 14. Testing FastAPI with Pytest: `tests/`, `conftest.py`, & TestClient

> **Goal:** Master automated testing in FastAPI from scratch. Learn why automated tests matter, how Pytest works, how an isolated test database is managed, and read a complete **line-by-line** walkthrough of every test file in this project.

---

## 📌 1. Why Automated Testing Matters

### The Problem: Manual Testing Doesn't Scale
When building APIs, developers often test by:
1. Starting `uvicorn`
2. Opening Postman or `/docs` (Swagger)
3. Manually typing emails, passwords, and clicking "Execute"
4. Checking if the database got updated

**Why this breaks down:**
- **Time consuming:** Testing 30 endpoints by hand takes 20 minutes every time you make a change.
- **Human error:** You forget to test that obscure error case (like duplicate email or invalid token).
- **Regressions:** You fix a bug in `/posts` and accidentally break `/vote`, but you don't notice until users complain in production.

### The Solution: Automated Testing with Pytest
An automated test is Python code that tests your Python code.
With one command:
```bash
pytest -v
```
35+ tests run in **under 11 seconds**, testing registration, invalid passwords, token expiration, post creation, permissions, and voting.

### The Testing Pyramid
```
       / \
      /   \     E2E Tests (Entire system, real browser, slowest)
     /=====\
    /       \   Integration Tests (FastAPI + Test Database + Auth)  <-- OUR TESTS!
   /=========\
  /           \ Unit Tests (Single functions, isolated logic, fastest)
 /=============\
```

---

## 🗄️ 2. The Test Database Architecture

### Rule #1 of Testing: NEVER Test on Production or Development Data
If tests ran on your development database (`FastAPI`):
- Test runs would wipe out your personal development posts and users.
- Leftover dummy data (`testuser@example.com`) would clutter your app.

### How We Solve It: A Dedicated Test Database (`FastAPI_test`)
1. In MySQL, we have two databases:
   - `FastAPI`: The real database used when running `uvicorn app.main:app --reload`.
   - `FastAPI_test`: The disposable sandbox used **only** when running `pytest`.
2. Before each test:
   - `Base.metadata.drop_all(bind=engine)` drops all tables (wipes out old test residue).
   - `Base.metadata.create_all(bind=engine)` recreates fresh, empty tables.
3. Each test runs in **complete isolation**, ensuring no test ever depends on or breaks another test!

---

## 🪄 3. Pytest Magic: `conftest.py` & Fixtures

### What is a Fixture?
A **fixture** is a helper function that prepares the environment for a test (e.g. provides a database session, creates a user, logs in a client).
Tests request fixtures simply by listing the fixture's name as an argument in the test function!

```python
def test_create_post(authorized_client):  # <-- authorized_client is a fixture!
    ...
```

### What is `conftest.py`?
`conftest.py` is a special file that Pytest automatically discovers. Any fixture defined in `conftest.py` is **globally available** to all test files in the directory without needing to `import` it!

### The Setup & Teardown Pattern (`yield`)
In Pytest fixtures, `yield` replaces `return`:
```python
@pytest.fixture
def session():
    # 1. SETUP (Runs BEFORE the test starts)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    yield db  # <-- Hands the db to the test
    
    # 2. TEARDOWN (Runs AFTER the test finishes)
    db.close()
    Base.metadata.drop_all(bind=engine)
```

### Fixture Scopes
- `scope="function"` (default): Runs once for **every individual test function**. Cleanest and safest!
- `scope="module"`: Runs once per test file.
- `scope="session"`: Runs once across the entire test suite.

---

## 🚀 4. FastAPI `TestClient` & `dependency_overrides`

### How `TestClient` Works
FastAPI provides `TestClient` (powered by `httpx`).
Instead of running a live web server on `http://127.0.0.1:8000`, `TestClient` passes HTTP requests directly into the FastAPI application in-memory. It is blazing fast!

### Swapping the Database: `app.dependency_overrides`
In `app/routers/posts.py`, endpoints use:
```python
db: Session = Depends(get_db)
```
During tests, we do NOT want `get_db` to connect to the dev database. We override it:
```python
def override_get_db():
    try:
        yield session  # points to FastAPI_test!
    finally:
        pass

app.dependency_overrides[get_db] = override_get_db
```
Now, whenever any router calls `Depends(get_db)`, FastAPI automatically uses our test database session instead!

---

## 📖 5. Line-by-Line Code Breakdown: `tests/conftest.py`

Let's read [`tests/conftest.py`](file:///Users/vanshtank/Desktop/web-dev/FastAPI_Post_Project-/tests/conftest.py) line by line:

```python
1:  import pytest
2:  from fastapi.testclient import TestClient
3:  from sqlalchemy import create_engine
4:  from sqlalchemy.orm import sessionmaker
5:  
6:  from app.main import app
7:  from app.config import settings
8:  from app.database import Base, get_db
9:  from app import models
10: from app.routers import oauth2
```
- **Lines 1–4:** Imports Pytest, FastAPI's `TestClient`, and SQLAlchemy connection tools.
- **Lines 6–10:** Imports the FastAPI app, configuration settings, models, database base metadata, and the `oauth2` router (for token creation).

```python
12: TEST_DATABASE_URL = (
13:     f"mysql+pymysql://{settings.database_username}:{settings.database_password}"
14:     f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"
15: )
16: 
17: engine = create_engine(TEST_DATABASE_URL)
18: TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```
- **Lines 12–15:** Constructs the connection string specifically targeting `{settings.database_name}_test` (i.e. `FastAPI_test`).
- **Line 17:** Creates the SQLAlchemy Engine for this test database.
- **Line 18:** Creates a session factory (`TestingSessionLocal`) bound to our test engine.

```python
21: @pytest.fixture(scope="function")
22: def session():
23:     Base.metadata.drop_all(bind=engine)
24:     Base.metadata.create_all(bind=engine)
25:     db = TestingSessionLocal()
26:     try:
27:         yield db
28:     finally:
29:         db.close()
```
- **Line 21:** Decorates `session` as a Pytest fixture that runs once per test (`scope="function"`).
- **Line 23:** Drops all tables in `FastAPI_test` to wipe away any leftover data from prior runs.
- **Line 24:** Re-creates all tables (`users`, `posts`, `votes`) brand new.
- **Line 25:** Spawns a new SQLAlchemy `db` session.
- **Line 27:** `yield db` supplies the active session to whatever test or fixture requested it.
- **Lines 28–29:** Once the test finishes, closes the session.

```python
32: @pytest.fixture(scope="function")
33: def client(session):
34:     def override_get_db():
35:         try:
36:             yield session
37:         finally:
38:             pass
39: 
40:     app.dependency_overrides[get_db] = override_get_db
41:     yield TestClient(app)
42:     app.dependency_overrides.clear()
```
- **Line 33:** `client` fixture depends on `session`.
- **Lines 34–38:** Defines `override_get_db`, returning our test `session`.
- **Line 40:** Replaces `get_db` inside FastAPI with our `override_get_db`.
- **Line 41:** Yields a `TestClient(app)` ready to make HTTP requests against `FastAPI_test`.
- **Line 42:** Clears dependency overrides after the test to prevent side effects.

```python
45: @pytest.fixture(scope="function")
46: def test_user(client, session):
47:     user_data = {"email": "testuser@example.com", "password": "password123"}
48:     res = client.post("/users/", json=user_data)
49:     assert res.status_code == 201
50:     user = session.query(models.User).filter(models.User.email == user_data["email"]).first()
51:     return {
52:         "id": user.id,
53:         "email": user.email,
54:         "password": user_data["password"],
55:         "created_at": user.created_at,
56:     }
```
- **Lines 45–56:** Helper fixture that automatically registers a user in the test database via `client.post("/users/")`. It returns a dictionary with the user's `id`, `email`, and plain `password` (needed later for login tests).

```python
59: @pytest.fixture(scope="function")
60: def test_user2(client, session):
61:     user_data = {"email": "otheruser@example.com", "password": "password123"}
62:     res = client.post("/users/", json=user_data)
63:     assert res.status_code == 201
64:     user = session.query(models.User).filter(models.User.email == user_data["email"]).first()
65:     return {
66:         "id": user.id,
67:         "email": user.email,
68:         "password": user_data["password"],
69:         "created_at": user.created_at,
70:     }
```
- **Lines 59–70:** Creates a second user. This is essential for testing **cross-user permissions** (e.g. verifying that User 2 cannot delete User 1's post).

```python
73: @pytest.fixture(scope="function")
74: def token(test_user):
75:     return oauth2.create_access_token(data={"sub": test_user["email"]})
76: 
77: @pytest.fixture(scope="function")
78: def authorized_client(client, token):
79:     client.headers = {
80:         **client.headers,
81:         "Authorization": f"Bearer {token}",
82:     }
83:     return client
```
- **Lines 73–75:** Takes `test_user` and generates a real, cryptographically signed JWT token with their email.
- **Lines 77–83:** Takes the standard `client` and injects `Authorization: Bearer <token>` into the HTTP headers. Any test using `authorized_client` behaves as an authenticated user!

```python
86: @pytest.fixture(scope="function")
87: def test_posts(test_user, test_user2, session):
88:     posts_data = [
89:         {"title": "First Post by User 1", "content": "Content of the first post", "published": True, "user_id": test_user["id"]},
90:         {"title": "Second Post by User 1", "content": "Content of the second post", "published": False, "user_id": test_user["id"]},
91:         {"title": "Post by User 2", "content": "Content belonging to user 2", "published": True, "user_id": test_user2["id"]},
92:     ]
93:     posts = [models.Post(**post) for post in posts_data]
94:     session.add_all(posts)
95:     session.commit()
96:     return session.query(models.Post).all()
```
- **Lines 86–96:** Automatically seeds the database with 3 sample posts (2 owned by User 1, 1 owned by User 2). Tests can immediately query, update, delete, or vote on them!

---

## 📖 6. Line-by-Line Code Breakdown: `tests/test_users.py`

Let's read [`tests/test_users.py`](file:///Users/vanshtank/Desktop/web-dev/FastAPI_Post_Project-/tests/test_users.py):

```python
1: def test_root(client):
2:     res = client.get("/")
3:     assert res.status_code == 200
4:     assert res.json().get("message") == "Welcome to my API!"
```
- Tests `GET /`. Verifies the status code is 200 OK and response JSON contains `"Welcome to my API!"`.

```python
7: def test_create_user_success(client):
8:     payload = {"email": "hello@example.com", "password": "securepassword123"}
9:     res = client.post("/users/", json=payload)
10:    assert res.status_code == 201
11:    assert res.json().get("message") == "User created successfully"
```
- Sends a valid user JSON payload to `POST /users/`.
- Asserts status is 201 Created and confirmation message is returned.

```python
14: def test_create_user_invalid_email(client):
15:     payload = {"email": "not-a-valid-email", "password": "password123"}
16:     res = client.post("/users/", json=payload)
17:     assert res.status_code == 422
```
- Sends an improperly formatted email (`"not-a-valid-email"`).
- Pydantic's `EmailStr` type validation intercepts the invalid payload and automatically responds with **422 Unprocessable Entity**.

```python
20: def test_create_user_duplicate_email(client, test_user):
21:     payload = {"email": test_user["email"], "password": "newpassword123"}
22:     res = client.post("/users/", json=payload)
23:     assert res.status_code == 409
24:     assert "already exists" in res.json().get("detail", "")
```
- Requests `test_user` (which registers `testuser@example.com`).
- Tries to create another user with the exact same email.
- The router checks `db.query(models.User).filter(...)` and raises **409 Conflict** with `"User with email '...' already exists"`.

```python
27: def test_get_user_by_id_success(client, test_user):
28:     res = client.get(f"/users/{test_user['id']}")
29:     assert res.status_code == 200
30:     user_response = res.json()
31:     assert user_response["id"] == test_user["id"]
32:     assert user_response["email"] == test_user["email"]
33:     assert "password" not in user_response
```
- Retrieves user by ID via `GET /users/{id}`.
- Asserts HTTP 200 OK.
- **Crucial Security Check:** `assert "password" not in user_response` guarantees that hashed passwords are never leaked through the API output schema!

```python
36: def test_get_user_not_found(client):
37:     res = client.get("/users/999999")
38:     assert res.status_code == 404
39:     assert res.json().get("detail") == "User with id 999999 not found"
```
- Queries a non-existent ID `999999`. Asserts HTTP 404 Not Found.

---

## 📖 7. Line-by-Line Code Breakdown: `tests/test_auth.py`

Let's read [`tests/test_auth.py`](file:///Users/vanshtank/Desktop/web-dev/FastAPI_Post_Project-/tests/test_auth.py):

```python
1: def test_login_user_success(client, test_user):
2:     res = client.post(
3:         "/login",
4:         data={"username": test_user["email"], "password": test_user["password"]},
5:     )
6:     assert res.status_code == 200
7:     token_res = res.json()
8:     assert token_res.get("token_type") == "bearer"
9:     assert "access_token" in token_res
10:    payload = jwt.decode(token_res["access_token"], settings.secret_key, algorithms=[settings.algorithm])
11:    assert payload.get("sub") == test_user["email"]
```
- **Why `data=...` instead of `json=...`?**
  FastAPI's `OAuth2PasswordRequestForm` expects URL-encoded form data (`application/x-www-form-urlencoded`), where username is passed in the `username` field.
- **Lines 10–11:** Decodes the returned JWT with `jose.jwt.decode` using our `SECRET_KEY` and asserts that the `sub` (subject) claim matches `test_user["email"]`.

```python
14: @pytest.mark.parametrize(
15:     "email, password, expected_status",
16:     [
17:         ("wrongemail@example.com", "password123", 403),
18:         ("testuser@example.com", "wrongpassword", 403),
19:         ("wrongemail@example.com", "wrongpassword", 403),
20:     ],
21: )
22: def test_login_incorrect_credentials(client, test_user, email, password, expected_status):
23:     res = client.post("/login", data={"username": email, "password": password})
24:     assert res.status_code == expected_status
25:     assert res.json().get("detail") == "Invalid email or password"
```
- **Parametrization:** Runs this test 3 separate times with different inputs:
  1. Non-existent email
  2. Correct email with wrong password
  3. Both wrong
- In all cases, asserts **403 Forbidden** and a generic `"Invalid email or password"` message (which prevents user enumeration attacks).

```python
28: def test_login_missing_fields(client):
29:     res = client.post("/login", data={"username": "testuser@example.com"})
30:     assert res.status_code == 422
```
- Omits the required `password` field. Asserts **422 Unprocessable Entity**.

---

## 📖 8. Line-by-Line Code Breakdown: `tests/test_posts.py`

Let's read [`tests/test_posts.py`](file:///Users/vanshtank/Desktop/web-dev/FastAPI_Post_Project-/tests/test_posts.py):

```python
1: def test_get_all_posts_unauthenticated(client, test_posts):
2:     res = client.get("/posts/orm")
3:     assert res.status_code == 401
```
- Calls `GET /posts/orm` with unauthenticated `client`.
- Asserts **401 Unauthorized**.

```python
6: def test_get_all_posts_authenticated(authorized_client, test_posts):
7:     res = authorized_client.get("/posts/orm")
8:     assert res.status_code == 200
9:     posts = res.json()
10:    assert len(posts) == len(test_posts)
```
- Calls `GET /posts/orm` using `authorized_client`.
- Asserts **200 OK** and that all 3 seeded posts are returned.

```python
13: @pytest.mark.parametrize("title, content, published", [
14:     ("First Title", "First Content", True),
15:     ("Second Title", "Second Content", False),
16:     ("Third Title", "Third Content", True),
17: ])
18: def test_create_post_success(authorized_client, test_user, title, content, published):
19:     payload = {"title": title, "content": content, "published": published}
20:     res = authorized_client.post("/posts/orm", json=payload)
21:     assert res.status_code == 201
22:     created_data = res.json()
23:     created_post = created_data["post"]
24:     assert created_post["title"] == title
25:     assert created_post["content"] == content
26:     assert created_post["published"] == published
27:     assert created_post["user_id"] == test_user["id"]
```
- Parametrized test creating posts with various titles, contents, and boolean `published` values.
- Asserts 201 Created and verifies `user_id` was automatically tied to the logged-in user!

```python
30: def test_create_post_default_published_true(authorized_client, test_user):
31:     payload = {"title": "Default Published Post", "content": "Some content"}
32:     res = authorized_client.post("/posts/orm", json=payload)
33:     assert res.status_code == 201
34:     assert res.json()["post"]["published"] is True
```
- Tests default schema behavior: when `published` is omitted, it defaults to `True`.

```python
37: def test_delete_post_success(authorized_client, test_user, test_posts):
38:     post_to_delete = test_posts[0]
39:     res = authorized_client.delete(f"/posts/orm/{post_to_delete.id}")
40:     assert res.status_code == 200
41:     assert res.json()["success"] is True
42:     get_res = authorized_client.get(f"/posts/orm/{post_to_delete.id}")
43:     assert get_res.status_code == 404
```
- Deletes user's own post.
- Immediately performs a `GET /posts/orm/{id}` to verify it now returns **404 Not Found**.

```python
46: def test_delete_other_user_post_forbidden(authorized_client, test_user2, test_posts):
47:     other_user_post = test_posts[2]  # owned by test_user2
48:     res = authorized_client.delete(f"/posts/orm/{other_user_post.id}")
49:     assert res.status_code == 403
50:     assert "not authorized" in res.json()["message"]
```
- **Authorization Boundary Test:** `authorized_client` (logged in as User 1) attempts to delete User 2's post.
- The router checks `if post.user_id != get_current_user.id:` and returns **403 Forbidden**!

---

## 📖 9. Line-by-Line Code Breakdown: `tests/test_vote.py`

Let's read [`tests/test_vote.py`](file:///Users/vanshtank/Desktop/web-dev/FastAPI_Post_Project-/tests/test_vote.py):

```python
1: @pytest.fixture
2: def test_vote(test_posts, session, test_user):
3:     new_vote = models.Vote(post_id=test_posts[0].id, user_id=test_user["id"])
4:     session.add(new_vote)
5:     session.commit()
```
- Local fixture that pre-inserts a vote by `test_user` on post 0 so we can test duplicate votes and vote deletion.

```python
7: def test_vote_on_post_success(authorized_client, test_posts):
8:     payload = {"post_id": test_posts[0].id, "dir": 1}
9:     res = authorized_client.post("/vote/", json=payload)
10:    assert res.status_code == 201
11:    assert res.json().get("message") == "Vote added successfully"
```
- Upvotes a post (`dir: 1`). Asserts 201 Created and `"Vote added successfully"`.

```python
14: def test_vote_twice_on_same_post_conflict(authorized_client, test_posts, test_vote):
15:     payload = {"post_id": test_posts[0].id, "dir": 1}
16:     res = authorized_client.post("/vote/", json=payload)
17:     assert res.status_code == 409
18:     assert "already voted" in res.json().get("detail", "")
```
- Uses `test_vote` fixture (vote already exists). Attempts to upvote again.
- Asserts **409 Conflict** with `"has already voted"`.

```python
21: def test_delete_vote_success(authorized_client, test_posts, test_vote):
22:     payload = {"post_id": test_posts[0].id, "dir": 0}
23:     res = authorized_client.post("/vote/", json=payload)
24:     assert res.status_code == 201
25:     assert res.json().get("message") == "Vote removed successfully"
```
- Removes a vote (`dir: 0`) from an already-voted post. Asserts 201 Created and `"Vote removed successfully"`.

```python
28: def test_delete_vote_non_existent(authorized_client, test_posts):
29:     payload = {"post_id": test_posts[0].id, "dir": 0}
30:     res = authorized_client.post("/vote/", json=payload)
31:     assert res.status_code == 404
32:     assert "does not exist" in res.json().get("detail", "")
```
- Tries to remove a vote when no vote was ever cast. Asserts **404 Not Found**.

```python
35: def test_vote_post_does_not_exist(authorized_client):
36:     payload = {"post_id": 999999, "dir": 1}
37:     res = authorized_client.post("/vote/", json=payload)
38:     assert res.status_code == 404
```
- Tries to vote on a post that does not exist (`id: 999999`). Asserts **404 Not Found**.

```python
41: def test_vote_unauthenticated(client, test_posts):
42:     payload = {"post_id": test_posts[0].id, "dir": 1}
43:     res = client.post("/vote/", json=payload)
44:     assert res.status_code == 401
```
- Tries to vote without providing a JWT bearer token. Asserts **401 Unauthorized**.

---

## 📊 10. HTTP Status Code Testing Checklist

| Status Code | Meaning | When to Test It |
| :--- | :--- | :--- |
| **200 OK** | Request succeeded | `GET`, `PUT`, `DELETE` success responses |
| **201 Created** | New resource created | `POST /users/`, `POST /posts/orm`, `POST /vote/` |
| **401 Unauthorized** | Missing or invalid JWT token | Protected endpoints called without `Authorization` header |
| **403 Forbidden** | Authenticated, but not permitted | User A attempting to delete/edit User B's post |
| **404 Not Found** | Resource does not exist | Invalid IDs in `/users/99999`, `/posts/orm/99999`, voting on fake post |
| **409 Conflict** | State collision / duplicate | Duplicate email registration, voting twice on same post |
| **422 Unprocessable Entity** | Schema validation failed | Invalid email string, missing required fields |

---

## ⌨️ 11. Pytest CLI Commands Reference

```bash
# Run all tests with verbose output
pytest -v

# Run all tests and print stdout (print statements)
pytest -v -s

# Stop immediately on first test failure
pytest -x

# Run only tests matching a keyword (e.g. only post tests)
pytest -k "posts"

# Run tests in a specific file
pytest tests/test_posts.py -v

# Run a specific test function in a specific file
pytest tests/test_posts.py::test_delete_other_user_post_forbidden -v

# Suppress deprecation warnings in terminal output
pytest -v --disable-warnings
```
