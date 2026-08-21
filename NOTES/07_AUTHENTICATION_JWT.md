# 07 — Authentication & JWT: `utils.py`, `auth.py`, `oauth2.py`

---

## 🤔 Why Authentication Matters

Without authentication, anyone could:
- Delete anyone's posts
- Pretend to be any user
- Access private data

Authentication is the process of proving "I am who I say I am."
Authorization is "Is this person allowed to do this?"

**Analogy:** 
- **Authentication** = Showing your ID at a bar
- **Authorization** = The bouncer checking you're old enough to enter

---

## 🔐 Part 1: Password Hashing — `utils.py`

### The Problem: Never Store Plain Passwords

If your database is hacked and passwords are stored as plain text:
- Every user's password is exposed
- If users reuse passwords, their other accounts (Gmail, banking) are at risk

### The Solution: One-Way Hashing

```python
import bcrypt

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')   # Convert string to bytes
    salt = bcrypt.gensalt()                # Generate random salt
    hashed = bcrypt.hashpw(pwd_bytes, salt)  # Hash password
    return hashed.decode('utf-8')          # Convert bytes back to string
```

**What is bcrypt?**
bcrypt is a **one-way hashing algorithm**. You can go forward (password → hash) but NOT backward (hash → password).

**What is a salt?**
A salt is a random string added to the password before hashing. This means:
- Two users with the same password get **different** hashes
- Pre-computed "rainbow table" attacks don't work

**Analogy:** 
- Hashing = Shredding a document. You can shred it but can't unshred it.
- Salt = Before shredding, mix in random confetti. Even identical documents shred differently.

### Example:
```
Password: "mysecret"
Salt 1:   "$2b$12$abc..." (random)
Hash 1:   "$2b$12$abcXYZ..."

Password: "mysecret"  ← Same password!
Salt 2:   "$2b$12$xyz..." (different random)
Hash 2:   "$2b$12$xyzABC..."  ← Different hash!
```

---

### Verifying a Password

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)
```

`bcrypt.checkpw()` extracts the salt from the stored hash, re-hashes the provided password with the SAME salt, and compares. This is the only safe way to verify!

**Analogy:** Like checking if two paintings were made with the same paint — you don't need to know the exact paint formula, you just compare the results.

---

## 🔑 Part 2: JWT Tokens — `oauth2.py`

### What is a JWT (JSON Web Token)?

A JWT is a **digitally signed string** that contains information. It looks like:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZUBleGFtcGxlLmNvbSIsImV4cCI6MTYyMDAwMDAwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

It has 3 parts separated by dots:
1. **Header** → Algorithm info (base64 encoded)
2. **Payload** → Your data (base64 encoded) — e.g., `{"sub": "alice@example.com", "exp": 1620000000}`
3. **Signature** → Header + Payload signed with your secret key

**Analogy:** A JWT is like a government-issued ID card:
- It contains information (name, photo, birthdate = payload)
- It has a security feature proving it's real (hologram = signature)
- Anyone can read the info (payload is not encrypted, just encoded)
- But only the government (your server) can ISSUE a valid one (because they have the secret key)

> **Important:** JWT payloads are NOT encrypted — just base64 encoded. Don't put sensitive data in them! The signature only proves the data hasn't been tampered with.

---

### Setting Up JWT Config

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config import settings

SECRET_KEY = settings.secret_key          # "secret" (or from .env)
ALGORITHM = settings.algorithm            # "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes  # 30
```

**`HS256`** = HMAC with SHA-256. A symmetric algorithm — the same key is used to sign AND verify. Great for simple single-server setups.

---

### Creating a Token

```python
oauth_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()             # Don't modify the original dict
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})   # Add expiry time to payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

**Step by step:**
1. Copy the input data (e.g., `{"sub": "alice@example.com"}`)
2. Calculate the expiry time (current time + 30 minutes)
3. Add expiry to the payload
4. Sign and encode everything into a JWT string

**Usage in `auth.py`:**
```python
access_token = oauth2.create_access_token(data={"sub": db_user.email})
```

The `"sub"` (subject) claim is the JWT standard field for identifying the user.

---

### `OAuth2PasswordBearer` — The Token Extractor

```python
oauth_scheme = OAuth2PasswordBearer(tokenUrl="login")
```

This tells FastAPI:
- Users authenticate via the `/login` endpoint
- Tokens are sent as `Authorization: Bearer <token>` headers
- When a route uses `Depends(oauth_scheme)`, FastAPI automatically extracts the token from the request header

**Analogy:** `OAuth2PasswordBearer` is like a receptionist who knows to look for ID in the right pocket of every visitor.

---

### Verifying a Token

```python
def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    return token_data
```

**Step by step:**
1. Decode the JWT using our secret key
2. Extract the `sub` (email) from the payload
3. If `sub` is missing → raise exception (invalid token)
4. If decoding fails (`JWTError`) → token is tampered/expired → raise exception
5. Return a `TokenData` object wrapping the email

---

### Getting the Current User — The Auth Guard

```python
def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user
```

This function is the **authentication guard**. Any route that includes `Depends(get_current_user)` requires a valid JWT.

**Flow:**
1. FastAPI extracts the Bearer token from the `Authorization` header
2. `verify_access_token` decodes it and gets the email
3. Look up the user in the database by email
4. Return the User object (or raise 401 if anything fails)

**Why look up from DB every request?** To handle cases like "user was deleted after token was issued."

**Usage:**
```python
@router.get('/posts')
def get_posts(get_current_user: models.User = Depends(oauth2.get_current_user)):
    # If we reach here, get_current_user is the authenticated User object
    print(get_current_user.email)  # alice@example.com
```

---

## 🚪 Part 3: The Login Endpoint — `auth.py`

```python
router = APIRouter(prefix="/login", tags=["Authentication"])

@router.post('', status_code=status.HTTP_200_OK, response_model=schemas.Token)
def login(user: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Find user by email
    db_user = db.query(models.User).filter(models.User.email == user.username).first()
    
    # 2. Check if user exists
    if not db_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
    
    # 3. Verify password
    if not utils.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
    
    # 4. Create and return token
    access_token = oauth2.create_access_token(data={"sub": db_user.email})
    return schemas.Token(message="Login successful", access_token=access_token, token_type="bearer")
```

### `OAuth2PasswordRequestForm` — Special Login Form

This is a FastAPI built-in that expects:
```
username: alice@example.com
password: mysecretpassword
```

Note: It uses `username` (not `email`) as the field name — this is the OAuth2 standard. The code maps `user.username` to the email field.

### Security: Why 403 instead of 404?

```python
# ❌ Don't do this:
if not db_user:
    raise HTTPException(404, "User not found")  # Reveals user doesn't exist!

# ✅ Do this:
if not db_user:
    raise HTTPException(403, "Invalid email or password")  # Same error for both cases
```

If you return different errors for "user not found" vs "wrong password", a hacker can use trial and error to discover valid email addresses.

---

## 🔄 The Complete Authentication Flow

```
┌─────────────────────────────────────────────────────────┐
│                    REGISTRATION                          │
│  POST /users/ {email, password}                         │
│       ↓                                                  │
│  hash_password(password) → hashed                       │
│       ↓                                                  │
│  Save user to DB with hashed password                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                      LOGIN                               │
│  POST /login {username=email, password}                 │
│       ↓                                                  │
│  Find user by email in DB                               │
│       ↓                                                  │
│  verify_password(plain, hashed) → True/False            │
│       ↓                                                  │
│  create_access_token({sub: email}) → JWT string         │
│       ↓                                                  │
│  Return: {message, access_token, token_type: "bearer"}  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│               PROTECTED ROUTE ACCESS                     │
│  GET /posts                                             │
│  Headers: Authorization: Bearer eyJhbGci...             │
│       ↓                                                  │
│  oauth_scheme extracts token from header                │
│       ↓                                                  │
│  verify_access_token(token) → TokenData(email)          │
│       ↓                                                  │
│  DB lookup by email → User object                       │
│       ↓                                                  │
│  Route function runs with current_user                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🛡️ JWT Token Expiry

```python
expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
```

Tokens expire after 30 minutes. After that, `jwt.decode()` raises `JWTError` (specifically `ExpiredSignatureError`), and the user gets a 401 response.

This means:
- Users must login again every 30 minutes (or when their token expires)
- In real apps, you'd implement "refresh tokens" — a longer-lived token that can get new access tokens without re-login

**Analogy:** It's like a parking ticket. It expires after a certain time. Once expired, you can't use it to prove you paid — you need a new one.
