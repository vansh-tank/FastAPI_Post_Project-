# 08 — Posts Router: `routers/posts.py` — Full CRUD Deep Dive

---

## 🤔 What is a Router?

A **router** is a mini-app that handles a group of related routes. Instead of putting all routes in `main.py`, you create separate files for each "resource" (posts, users, votes).

```python
router = APIRouter(
    prefix="/posts",   # All routes in this file start with /posts
    tags=["posts"]     # Groups them in the Swagger docs
)
```

**Analogy:** In a restaurant, one team handles the bar, another handles food. Each team is a "router" — they handle their own section but work together in the same restaurant.

---

## 🔄 Dependency Injection — The `Depends()` Pattern

This is FastAPI's most powerful feature. Before understanding the routes, understand this:

```python
def get_posts(
    db_raw: tuple = Depends(get_raw_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
```

`Depends()` tells FastAPI: "Before calling this function, run `get_raw_db()` and `get_current_user()` and inject their results as arguments."

**What happens automatically:**
1. `Depends(get_raw_db)` → Opens a DB connection from the pool, yields it, closes it after
2. `Depends(oauth2.get_current_user)` → Reads the JWT token from the header, decodes it, looks up the user

**Analogy:** `Depends()` is like a restaurant that requires you to show your reservation (token) and sit down (db connection) before you can order (route logic). The maître d' handles all that before sending you to your table.

---

## 📖 GET `/posts` — List Posts (Raw SQL)

```python
@router.get('', status_code=status.HTTP_200_OK, response_model=list[schemas.PostResponse])
def get_posts(
    db_raw: tuple = Depends(get_raw_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    conn, cur = db_raw
    cur.execute(
        'SELECT p.id, p.title, p.content, p.published, p.created_at, p.user_id, '
        'u.email AS user_email, u.created_at AS user_created_at '
        'FROM posts p JOIN users u ON p.user_id = u.id WHERE p.user_id = %s',
        (get_current_user.id,)
    )
    posts = cur.fetchall()
    
    formatted_posts = []
    for post in posts:
        formatted_posts.append({
            "id": post["id"],
            "title": post["title"],
            "content": post["content"],
            "published": bool(post["published"]),
            "created_at": post["created_at"],
            "user_id": post["user_id"],
            "owner": {
                "id": post["user_id"],
                "email": post["user_email"],
                "created_at": post["user_created_at"]
            }
        })
    return formatted_posts
```

### The SQL Query — Explained

```sql
SELECT 
    p.id, p.title, p.content, p.published, p.created_at, p.user_id,
    u.email AS user_email, 
    u.created_at AS user_created_at
FROM posts p 
JOIN users u ON p.user_id = u.id 
WHERE p.user_id = %s
```

| Part | Meaning |
|------|---------|
| `p.id`, `p.title` etc. | Get these columns from the `posts` table (aliased as `p`) |
| `u.email AS user_email` | Get user's email, rename it to avoid conflict with post columns |
| `FROM posts p` | Query from `posts` table, calling it `p` for short |
| `JOIN users u ON p.user_id = u.id` | Link each post to its owner |
| `WHERE p.user_id = %s` | Only get posts belonging to the logged-in user |

**Analogy:** It's like asking: "Show me all orders (posts) along with the customer info (users), but only orders placed by THIS customer."

### Why Manual Formatting?
```python
"owner": {
    "id": post["user_id"],
    "email": post["user_email"],
    ...
}
```
Raw SQL returns a flat dictionary. Pydantic expects a nested `owner` object (as defined in `PostResponse`). So we manually reshape the data to match the schema.

### `bool(post["published"])` — Why the Cast?
MySQL returns boolean columns as integers (`0` or `1`). The schema expects a Python `bool`. `bool(1)` = `True`, `bool(0)` = `False`.

---

## 📖 GET `/posts/orm` — List Posts with Votes (ORM)

```python
@router.get('/orm', response_model=list[schemas.PostOut])
def get_posts_orm(
    db: Session = Depends(get_db),
    get_current_user: models.User = Depends(oauth2.get_current_user),
    limit: int = 10,
    skip: int = 0,
    search: Optional[str] = ""
):
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes"))\
        .join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)\
        .group_by(models.Post.id)\
        .filter(models.Post.title.contains(search))\
        .offset(skip)\
        .limit(limit)\
        .all()
    return results
```

### Query Parameters
These come from the URL: `GET /posts/orm?limit=5&skip=10&search=hello`

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `limit` | `10` | Return at most 10 posts |
| `skip` | `0` | Skip 0 posts (for pagination) |
| `search` | `""` | Filter posts whose title contains this text |

**Analogy:** Like browsing page 2 of Google results — `skip=10` means "skip the first 10 results."

### The ORM Query with JOIN and COUNT

```python
db.query(models.Post, func.count(models.Vote.post_id).label("votes"))
```
This selects BOTH the Post object AND a vote count.

```python
.join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)
```
- `isouter=True` = **LEFT JOIN** — include posts even if they have 0 votes
- Without `isouter`, posts with no votes would be excluded (INNER JOIN)

```python
.group_by(models.Post.id)
```
Needed when using aggregate functions like `COUNT`. Groups results by post.

```python
.filter(models.Post.title.contains(search))
```
Translates to SQL `WHERE title LIKE '%search%'`.

```python
.offset(skip).limit(limit)
```
Pagination: skip N rows, return at most M rows.

**Equivalent SQL:**
```sql
SELECT posts.*, COUNT(votes.post_id) AS votes
FROM posts
LEFT JOIN votes ON votes.post_id = posts.id
WHERE posts.title LIKE '%search%'
GROUP BY posts.id
LIMIT 10 OFFSET 0;
```

---

## ➕ POST `/posts` — Create a Post (Raw SQL)

```python
@router.post('', status_code=status.HTTP_201_CREATED, response_model=schemas.MessageResponse)
def create_item(
    item: schemas.Post,
    db_raw: tuple = Depends(get_raw_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    conn, cur = db_raw
    cur.execute(
        'INSERT INTO posts (title, content, published, user_id) VALUES (%s, %s, %s, %s)',
        (item.title, item.content, item.published, get_current_user.id)
    )
    conn.commit()
    return {"message": "Post created successfully"}
```

### Key Points:

1. **`item: schemas.Post`** — FastAPI automatically reads the request body and validates it against the `Post` schema. If validation fails, it returns a 422 error automatically.

2. **`conn.commit()`** — Without this, the INSERT would be in a transaction that gets ROLLED BACK when the connection closes. You must commit to permanently save changes.

3. **`get_current_user.id`** — The `user_id` for the new post is taken from the authenticated user, NOT from the request body. This prevents a user from creating posts on behalf of others.

---

## ➕ POST `/posts/orm` — Create a Post (ORM)

```python
@router.post('/orm', status_code=status.HTTP_201_CREATED, response_model=schemas.CreatePostResponse)
def create_post_orm(
    item: schemas.Post,
    db: Session = Depends(get_db),
    get_current_user: models.User = Depends(oauth2.get_current_user),
):
    new_post = models.Post(**item.model_dump())   # Create Post object
    new_post.user_id = get_current_user.id         # Set the owner
    db.add(new_post)      # Stage the object
    db.commit()           # Persist to database
    db.refresh(new_post)  # Reload from DB (gets generated id, created_at)
    return {"message": "Post created successfully", "post": new_post}
```

### `item.model_dump()` — Schema to Dict

`model_dump()` converts a Pydantic model to a Python dict:
```python
item.model_dump() == {"title": "My Post", "content": "Hello!", "published": True}
```

`models.Post(**item.model_dump())` unpacks that dict as keyword arguments:
```python
# Same as:
models.Post(title="My Post", content="Hello!", published=True)
```

### `db.refresh(new_post)` — Why Necessary?

After `db.commit()`, the `new_post` object in Python memory is out of sync with the database. The DB assigned `id` and `created_at`. `db.refresh()` re-reads the row and updates the Python object.

Without it, `new_post.id` would be `None`.

**Analogy:** Like submitting a form online and refreshing the page to see your updated profile with the system-generated ID.

---

## 🔍 GET `/posts/{id}` — Get One Post (Raw SQL)

```python
@router.get('/{id}', response_model=schemas.SinglePostResponse)
def get_post(id: int, db_raw: tuple = Depends(get_raw_db), ...):
    conn, cur = db_raw
    cur.execute(
        'SELECT p.id, p.title, p.content, p.published, p.created_at, p.user_id, '
        'u.email AS user_email, u.created_at AS user_created_at '
        'FROM posts p JOIN users u ON p.user_id = u.id WHERE p.id = %s',
        (id,)
    )
    post = cur.fetchone()   # Get one row (or None)
    if post:
        formatted_post = { ... }
        return {'success': True, 'response': formatted_post}
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'success': False, 'response': f'id:{id} not found'}
    )
```

### Path Parameters
`{id}` in the route path becomes the `id: int` parameter. FastAPI automatically:
- Extracts `5` from `/posts/5`
- Converts it to `int`
- Validates it's actually a valid int

### `cur.fetchone()` vs `cur.fetchall()`
- `fetchone()` → Returns one row as a dict (or `None` if no result)
- `fetchall()` → Returns all rows as a list of dicts

### `JSONResponse` — Manual Response

Usually you just `return` a dict and FastAPI converts it. But here we need to return a **404 status code** with a JSON body. `JSONResponse` lets you control both:

```python
return JSONResponse(
    status_code=status.HTTP_404_NOT_FOUND,
    content={'success': False, 'response': 'id:99 not found'}
)
```

---

## 🗑️ DELETE `/posts/{id}` — Delete a Post

```python
@router.delete('/{id}', response_model=schemas.ActionResponse)
def delete_post(id: int, db_raw: tuple = Depends(get_raw_db), get_current_user: models.User = Depends(oauth2.get_current_user)):
    conn, cur = db_raw
    cur.execute('SELECT * FROM posts WHERE id = %s', (id,))
    post = cur.fetchone()
    
    if not post:
        return JSONResponse(status_code=404, content={"success": False, "message": f"Post with id {id} not found"})
    
    if post['user_id'] != get_current_user.id:     # Authorization check!
        return JSONResponse(status_code=403, content={"success": False, "message": "You are not authorized to delete this post"})
    
    cur.execute('DELETE FROM posts WHERE id = %s', (id,))
    conn.commit()
    return JSONResponse(status_code=200, content={"success": True, "message": f"Post with id {id} deleted successfully"})
```

### Two-Stage Check — First Find, Then Authorize

1. **Does the post exist?** → 404 if not found
2. **Is this the owner?** → 403 (Forbidden) if someone else's post

**Why not combine them?** Clearer error messages. If you only check ownership and the post doesn't exist, you'd get a cryptic error.

### Authorization vs Authentication
- **Authentication:** "Are you logged in?" → handled by `Depends(oauth2.get_current_user)`
- **Authorization:** "Are you ALLOWED to do THIS?" → handled manually: `post['user_id'] != get_current_user.id`

---

## ✏️ PUT `/posts/{id}` — Update a Post

```python
@router.put('/{id}', response_model=schemas.ActionResponse)
def update_post(id: int, item: schemas.Post, db_raw: tuple = Depends(get_raw_db), get_current_user: models.User = Depends(oauth2.get_current_user)):
    conn, cur = db_raw
    cur.execute('SELECT * FROM posts WHERE id = %s', (id,))
    post = cur.fetchone()
    
    if not post: ...       # 404
    if post['user_id'] != get_current_user.id: ...  # 403
    
    cur.execute(
        'UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s',
        (item.title, item.content, item.published, id)
    )
    conn.commit()
    return JSONResponse(status_code=200, content={"success": True, "message": f"Post with id {id} updated successfully"})
```

`PUT` replaces the entire resource. The client must send ALL fields (title, content, published).

---

## ✏️ PUT `/posts/orm/{id}` — Update a Post (ORM)

```python
@router.put('/orm/{id}', response_model=schemas.ActionResponse)
def update_post_orm(id: int, item: schemas.Post, db: Session = Depends(get_db), ...):
    post_query = db.query(models.Post).filter(models.Post.id == id)  # Store the QUERY
    post = post_query.first()                                          # Execute it
    
    if not post: ...
    if post.user_id != get_current_user.id: ...
    
    post_query.update(item.model_dump(), synchronize_session=False)  # Update all fields
    db.commit()
    return JSONResponse(...)
```

### `post_query` vs `post` — The Stored Query Pattern

Notice we store the **query object** (`post_query`) and the **result** (`post`) separately.

- `post_query` = the SQLAlchemy query (not yet executed fully)
- `post = post_query.first()` = fetches one result
- `post_query.update(...)` = runs an UPDATE on the same filtered query

This avoids querying twice. The same `WHERE id = X` filter is reused for both the SELECT and the UPDATE.

### `synchronize_session=False`
Tells SQLAlchemy not to try to update in-memory session objects after the SQL UPDATE. Usually fine for straightforward updates.

### `item.model_dump()` for Update
Converts the input schema to a dict and uses it as the SET values:
```sql
UPDATE posts SET title='New', content='Updated', published=true WHERE id=5
```

---

## 📊 Summary: All Post Endpoints

| Method | Path | Implementation | Auth | Returns |
|--------|------|---------------|------|---------|
| GET | `/posts` | Raw SQL | ✅ | Your posts |
| GET | `/posts/orm` | ORM + JOIN | ✅ | All posts + vote count |
| POST | `/posts` | Raw SQL | ✅ | Success message |
| POST | `/posts/orm` | ORM | ✅ | Message + new post |
| GET | `/posts/{id}` | Raw SQL | ✅ | Single post |
| GET | `/posts/orm/{id}` | ORM | ✅ | Single post |
| DELETE | `/posts/{id}` | Raw SQL | ✅ | Success/error message |
| DELETE | `/posts/orm/{id}` | ORM | ✅ | Success/error message |
| PUT | `/posts/{id}` | Raw SQL | ✅ | Success/error message |
| PUT | `/posts/orm/{id}` | ORM | ✅ | Success/error message |
