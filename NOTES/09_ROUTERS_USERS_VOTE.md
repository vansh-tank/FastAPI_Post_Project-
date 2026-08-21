# 09 — Users & Voting: `routers/users.py` & `routers/vote.py`

---

# Part 1: Users Router (`users.py`)

---

## 🔑 Router Setup

```python
router = APIRouter(
    prefix="/users",
    tags=["users"]
)
```

All routes here start with `/users`. This file handles:
1. Creating (registering) a new user
2. Looking up a user by ID

---

## ➕ POST `/users/` — Register a New User

```python
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.MessageResponse)
def create_user(user: schemas.User, db: Session = Depends(get_db)):
    # Step 1: Hash the password
    hashed_password = utils.hash_password(user.password)
    user.password = hashed_password
    
    # Step 2: Create a User model object
    new_user = models.User(**user.model_dump())
    
    # Step 3: Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully"}
```

### Step by Step Breakdown:

#### Step 1: Hashing the Password
```python
hashed_password = utils.hash_password(user.password)
user.password = hashed_password
```

**Why this step is critical:**
- User sends: `{"email": "alice@example.com", "password": "mysecret"}`
- `user.password` starts as `"mysecret"` (plain text)
- After hashing: `user.password` is `"$2b$12$abc123..."` (hashed)
- The plain text password is now gone from memory

**Analogy:** Like shredding the sticky note with the password after memorizing a secret code. The original doesn't exist anymore.

#### Step 2: `models.User(**user.model_dump())`
```python
new_user = models.User(**user.model_dump())
```

`user.model_dump()` returns:
```python
{"email": "alice@example.com", "password": "$2b$12$abc..."}
```

`**` unpacks this as keyword arguments:
```python
models.User(email="alice@example.com", password="$2b$12$abc...")
```

This creates a SQLAlchemy `User` object (NOT yet saved to DB).

#### Step 3: Save to DB
```python
db.add(new_user)      # Stage the object for insertion
db.commit()            # Execute the INSERT SQL
db.refresh(new_user)  # Reload from DB (get the auto-generated id, created_at)
```

**Analogy:**
- `db.add()` = putting items in a shopping basket
- `db.commit()` = checking out (paying)
- `db.refresh()` = getting the receipt with your transaction ID

#### Return Value
Returns only `{"message": "User created successfully"}` — NOT the user object. Why?
- The user's password (even hashed) isn't returned
- The plain text password was never stored
- Good API design: confirm success without leaking data

### What Happens if Email Already Exists?
The `email` column has `unique=True` in the model. If you try to create a user with a duplicate email, MySQL throws an integrity error, and FastAPI returns a 500 Internal Server Error. (A better implementation would catch this and return a 409 Conflict.)

---

## 🔍 GET `/users/{id}` — Get a User by ID

```python
@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found")
    return user
```

### Points to Note:

#### No Auth Required
Notice there's no `Depends(oauth2.get_current_user)` here. Anyone can look up a user's **public** info (id, email, created_at) without logging in.

#### `response_model=schemas.UserResponse`
`UserResponse` only includes `id`, `email`, and `created_at`. The password field is automatically excluded from the response — Pydantic only serializes fields defined in the response schema.

#### `raise HTTPException` vs `return JSONResponse`
Both send error responses, but:
- `raise HTTPException` → Cleaner, works with FastAPI's error handling system
- `return JSONResponse` → More manual control

```python
# HTTPException approach:
raise HTTPException(status_code=404, detail="User not found")

# JSONResponse approach:
return JSONResponse(status_code=404, content={"message": "User not found"})
```

#### ORM Query
```python
db.query(models.User)              # SELECT * FROM users
  .filter(models.User.id == id)    # WHERE id = 5
  .first()                         # LIMIT 1, returns None if not found
```

---

# Part 2: Vote Router (`vote.py`)

---

## 🗳️ What is the Voting System?

This is like Reddit's upvote/downvote system, simplified:
- `dir = 1` → Add a vote (upvote)
- `dir = 0` → Remove a vote (un-vote)

There's no downvote — just vote or un-vote.

**Analogy:** Like the ❤️ button on Instagram — you can either like or unlike. You can't like the same post twice.

---

## ➕ POST `/vote/` — Cast or Remove a Vote

```python
@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(
    vote: schemas.Vote,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
```

The `schemas.Vote` input:
```json
{
    "post_id": 5,
    "dir": 1
}
```

---

### Step 1: Verify the Post Exists

```python
post = db.query(models.Post).filter(models.Post.id == vote.post_id).first()
if not post:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Post with id {vote.post_id} does not exist"
    )
```

Can't vote on a post that doesn't exist. Simple check first.

---

### Step 2: Check if Already Voted

```python
vote_query = db.query(models.Vote).filter(
    models.Vote.post_id == vote.post_id,
    models.Vote.user_id == current_user.id
)
found_vote = vote_query.first()
```

This checks the `votes` table for an existing record where BOTH:
- `post_id` matches the post we're voting on
- `user_id` matches the current user

Since the `votes` table has a **composite primary key** on `(user_id, post_id)`, there can only be ONE such record per user per post.

**SQL equivalent:**
```sql
SELECT * FROM votes 
WHERE post_id = 5 AND user_id = 1
LIMIT 1;
```

---

### Step 3a: Adding a Vote (`dir = 1`)

```python
if vote.dir == 1:
    if found_vote:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {current_user.id} has already voted on post {vote.post_id}"
        )
    new_vote = models.Vote(post_id=vote.post_id, user_id=current_user.id)
    db.add(new_vote)
    db.commit()
    return {"message": "Vote added successfully"}
```

| Scenario | Action |
|----------|--------|
| No existing vote | Create new Vote record → 201 Created |
| Already voted | Raise 409 Conflict error |

**Why 409 Conflict?** It's the correct HTTP status for "this resource (the vote) already exists."

---

### Step 3b: Removing a Vote (`dir = 0`)

```python
else:
    if not found_vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vote does not exist for user {current_user.id} on post {vote.post_id}"
        )
    vote_query.delete(synchronize_session=False)
    db.commit()
    return {"message": "Vote removed successfully"}
```

| Scenario | Action |
|----------|--------|
| Vote exists | Delete it → 200 OK |
| Vote doesn't exist | Raise 404 Not Found |

### `vote_query.delete(synchronize_session=False)`
Notice we reuse `vote_query` (the stored query from Step 2) to delete. This is the same efficient pattern as in `update_post_orm` — write the filter once, use it for both SELECT and DELETE.

**`synchronize_session=False`** = Don't update the in-memory session after deleting. Efficient because we don't need the object anymore after deletion.

---

## 🔄 The Complete Vote Flow

```
Client: POST /vote/ {"post_id": 5, "dir": 1}
         │
         ↓ Depends(get_current_user)
         │  → Token verified, current_user = alice
         │
         ↓ Does post 5 exist?
         │  → Yes, continue
         │  → No, raise 404
         │
         ↓ Has alice already voted on post 5?
         │
         ├── dir=1 (vote):
         │   ├── Already voted? → raise 409 Conflict
         │   └── Not voted? → INSERT into votes → return "Vote added"
         │
         └── dir=0 (unvote):
             ├── Not voted? → raise 404 Not Found
             └── Already voted? → DELETE from votes → return "Vote removed"
```

---

## 📊 The Votes Table Revisited

```python
class Vote(base):
    __tablename__ = "votes"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
```

**Composite Primary Key = Natural Uniqueness**

The database itself enforces that a user can't vote twice on the same post. Even if there's a bug in your code and you try to INSERT a duplicate `(user_id, post_id)`, the database will reject it with a constraint violation.

**Analogy:** Like trying to register for the same event twice with the same name and email — the system catches it even before the code can.

---

## 🔗 How Votes Connect to the Posts ORM Query

In `posts.py`:
```python
results = db.query(models.Post, func.count(models.Vote.post_id).label("votes"))
    .join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)
    .group_by(models.Post.id)
    ...
```

The votes table is joined here to count votes per post. The `PostOut` schema then returns each post with its vote count:
```json
{
    "Post": { ...post data... },
    "votes": 42
}
```
