from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from mysql.connector import Error, pooling
import time
from .config import settings

engine = create_engine(
    f"mysql+pymysql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)

session = sessionmaker(bind=engine)
base = declarative_base()


def get_db():
    db = session()
    try:
        yield db
    finally: 
        db.close()

# Create a connection pool for thread-safe concurrent database operations
db_pool = None
for _ in range(5):
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,
            host="localhost",
            user="root",
            password="vanshtank",
            database="FastAPI",
            port=3306
        )
        print('MySQL Connection Pool created successfully')
        break
    except Error as e:
        print(f"Error creating MySQL Connection Pool: {e}")
        time.sleep(2)

if not db_pool:
    raise RuntimeError("Failed to initialize MySQL Connection Pool")

# Legacy globals for backward compatibility with direct module imports
db = db_pool.get_connection()
cursor = db.cursor(dictionary=True, prepared=True)
print('retro database connected successfully (legacy global)')

# Dependency generator to get a thread-safe, request-scoped connection and cursor
def get_raw_db():
    conn = db_pool.get_connection()
    cur = conn.cursor(dictionary=True, prepared=True)
    try:
        yield conn, cur
    finally:
        cur.close()
        conn.close()