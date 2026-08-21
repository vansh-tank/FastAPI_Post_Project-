# 11 — SQL Learning Scripts: `SQL_learn/sql.py` & `SQL_learn/orm.py`

---

## 🎓 What Are These Files?

The `SQL_learn/` folder contains **standalone experiment scripts** — not part of the actual API, but learning exercises that show different ways to interact with a database. They're great for understanding the progression from raw SQL to ORM.

---

# Part 1: Raw SQL with `mysql.connector` (`sql.py`)

---

## 📄 The Complete `sql.py`

```python
import mysql.connector  
from mysql.connector import Error

try:
    conn = mysql.connector.connect(
        host='localhost',
        database='FastAPI',
        user='root',
        password='vanshtank',
        port=3306
    )
    if conn.is_connected():
        print('Connected to MySQL database')
except Error as e:
    print(f'Error connecting to MySQL database: {e}') 

cursor = conn.cursor()
cursor.execute('desc posts')     # DESCRIBE the posts table

for i in cursor:
    print(i)

sql = "INSERT INTO posts (title, content, published) VALUES (%s, %s, %s)"
cursor.execute(sql, ('vansh', 'tank', True))
conn.commit()
cursor.close()
conn.close()
print('MySQL connection closed')
```

---

## 🔍 Deep Dive

### Connecting to MySQL
```python
conn = mysql.connector.connect(
    host='localhost',
    database='FastAPI',
    user='root',
    password='vanshtank',
    port=3306
)
```

This is the **most basic** way to connect to MySQL in Python. No abstraction, just a direct connection.

**What you get:**
- `conn` = the connection object (represents the DB session)
- Use `conn.commit()` to save changes
- Use `conn.close()` to disconnect

### The Cursor Object
```python
cursor = conn.cursor()
```

A cursor is like a **pointer** in the database. You use it to execute SQL and read results.

**Analogy:** If the database is a book, the cursor is your finger — it points to where you are, and you read line by line.

### `DESCRIBE posts`
```python
cursor.execute('desc posts')
for i in cursor:
    print(i)
```

`DESC posts` or `DESCRIBE posts` shows the structure of the `posts` table:
```
('id', 'int', 'NO', 'PRI', None, 'auto_increment')
('title', 'varchar(255)', 'NO', '', None, '')
('content', 'varchar(2000)', 'NO', '', None, '')
('published', 'tinyint(1)', 'NO', '', '1', '')
('created_at', 'datetime', 'NO', '', 'current_timestamp()', ...)
('user_id', 'int', 'NO', 'MUL', None, '')
```

### Iterating the Cursor
```python
for i in cursor:
    print(i)
```

After `cursor.execute()`, you can iterate the cursor directly. Each iteration gives you one row as a tuple.

> **⚠️ Gotcha:** If you don't read ALL rows (using `fetchall()` or iterating fully), and then close the cursor, MySQL throws an "Unread result found" error! Always read all results before closing.

### Parameterized INSERT
```python
sql = "INSERT INTO posts (title, content, published) VALUES (%s, %s, %s)"
cursor.execute(sql, ('vansh', 'tank', True))
conn.commit()
```

The `%s` placeholders are filled in by `mysql.connector` safely. This prevents SQL injection.

### The Comment Notes (Learning Gold!)
```python
# cursor.rowcount returns the number of rows affected by the last executed statement
# fetchone give one reverses pointer and throws internal error when we close cursor 
#   without reading all data at end None is given 
# fetchmany we define how many rows we want to read and it gives us that many rows
# put in conn.cursor(prepared=True) for fast and prevent injection
```

These are notes taken while learning! Key facts:
- `cursor.rowcount` → How many rows were affected by INSERT/UPDATE/DELETE
- `cursor.fetchone()` → Get one row, moves pointer forward
- `cursor.fetchmany(n)` → Get `n` rows at a time
- `cursor.fetchall()` → Get ALL remaining rows
- `prepared=True` → Use prepared statements (faster for repeated queries, SQL injection safe)

---

## 📊 Cursor Methods Summary

| Method | Returns | Use When |
|--------|---------|----------|
| `cursor.fetchone()` | One row (dict or tuple) | Expecting single result |
| `cursor.fetchmany(n)` | List of n rows | Processing in batches |
| `cursor.fetchall()` | All remaining rows | Small result sets |
| `cursor.rowcount` | Int (rows affected) | After INSERT/UPDATE/DELETE |

---

# Part 2: SQLAlchemy ORM Learning (`orm.py`)

---

## 📄 The `orm.py` File — A Learning Journey

This file shows the evolution from raw SQL-style SQLAlchemy to full ORM usage.

### Phase 1: SQLAlchemy as a SQL Wrapper (Commented Out)

```python
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import Session
# engine = create_engine('sqlite:///mydb.db', echo=True)
# conn = engine.connect()
# conn.execute(text('''CREATE TABLE IF NOT EXISTS posts (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     ...
# )'''))
# conn.commit()
```

This approach uses SQLAlchemy but still writes raw SQL strings wrapped in `text()`. Not much better than `mysql.connector`, but it's step 1 of the learning journey.

`echo=True` → SQLAlchemy prints every SQL query it executes to the console. Great for debugging/learning!

### Phase 2: Core API with Table Objects (Commented Out)

```python
# metadata = MetaData()
# posts = Table(
#   'posts',
#   metadata,
#   Column('id', Integer, primary_key=True, autoincrement=True),
#   Column('title', String, nullable=False),
#   ...
# )
# metadata.create_all(engine)
```

The SQLAlchemy **Core** API — you define tables as objects but still write SQL-ish expressions:

```python
# insert_statement = posts.insert().values(title='First Post', ...)
# con.execute(insert_statement)
```

Better than raw SQL strings, but not full ORM.

### Phase 3: Full ORM with Declarative Base (Active Code)

```python
engine = create_engine("mysql+pymysql://root:vanshtank@localhost:3306/FastAPI", echo=True)

base = declarative_base()

class Post(base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, nullable=False, default=True)

base.metadata.create_all(engine)  # Create table if it doesn't exist
```

Now you define your schema as Python classes and let SQLAlchemy handle everything.

### Creating and Saving a Record

```python
new_post = Post(title='First Post from ORM', content='...', published=True)

Session = sessionmaker(bind=engine)
session = Session()
session.add(new_post)
session.commit()
```

Note the naming: `Session` (capital S) is the factory class, `session` (lowercase) is an instance. Same pattern as in `database.py` but with different naming here.

### The Comments as Notes

```python
# session.flush() # to get the id of the new post before commit
# use filter instead of where for this instance
# update takes dictionary 
```

`flush()` is interesting:
- `flush()` → Sends SQL to the database but keeps the transaction open. The object gets its `id` (auto-generated), but changes can still be rolled back.
- `commit()` → Permanently saves changes.

**Analogy:** `flush()` is like placing an order at a restaurant — the kitchen starts working but you haven't paid yet. `commit()` is paying the bill.

---

## 🆚 Raw SQL vs Core vs ORM — Evolution

```
Level 1: mysql.connector + raw SQL strings
   → Most control, most verbose, no Python object mapping
   
Level 2: SQLAlchemy Core + text()
   → Still raw SQL but using SQLAlchemy's connection management
   
Level 3: SQLAlchemy Core + Table objects
   → Define tables in Python, use Expression Language
   
Level 4: SQLAlchemy ORM + Declarative Base
   → Full Python objects, automatic SQL generation
   ← This is what the main app uses
```

---

## 💡 Key Learnings From These Scripts

1. **Always commit or rollback** — Changes aren't saved until you call `commit()`
2. **Always close your connection** — Leaked connections exhaust the connection pool
3. **Use prepared statements** — `cursor(prepared=True)` for safety and performance
4. **`echo=True` is your friend** — See exactly what SQL SQLAlchemy generates
5. **`flush()` vs `commit()`** — `flush()` to get generated values mid-transaction, `commit()` to save permanently
6. **Iterating a cursor** — If you don't read all results, MySQL will complain on close

---

## 🔧 SQLite vs MySQL

The `orm.py` started with SQLite (`sqlite:///mydb.db`) then switched to MySQL. Key differences:

| Feature | SQLite | MySQL |
|---------|--------|-------|
| Setup | Zero config (file-based) | Server required |
| Use case | Development, small apps | Production, large apps |
| File | `mydb.db` | Running server on port 3306 |
| Python driver | Built-in | `pymysql` or `mysql-connector-python` |
| Concurrent writes | Limited | Full support |

SQLite is great for quickly testing ORM code (the file `mydb.db` in the project root is from these experiments).
