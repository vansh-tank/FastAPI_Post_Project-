import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app import models
from app.routers import oauth2

# Connect to the dedicated test database
TEST_DATABASE_URL = (
    f"mysql+pymysql://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def session():
    """
    Creates fresh database tables before each test and drops them after.
    Yields an isolated SQLAlchemy session.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(session):
    """
    Provides a FastAPI TestClient with the get_db dependency overridden
    to use the isolated test database session.
    """
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(client, session):
    """
    Registers a primary test user and returns user info including plain password.
    """
    user_data = {"email": "testuser@example.com", "password": "password123"}
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    user = session.query(models.User).filter(models.User.email == user_data["email"]).first()
    return {
        "id": user.id,
        "email": user.email,
        "password": user_data["password"],
        "created_at": user.created_at,
    }


@pytest.fixture(scope="function")
def test_user2(client, session):
    """
    Registers a second test user for testing cross-user authorization.
    """
    user_data = {"email": "otheruser@example.com", "password": "password123"}
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    user = session.query(models.User).filter(models.User.email == user_data["email"]).first()
    return {
        "id": user.id,
        "email": user.email,
        "password": user_data["password"],
        "created_at": user.created_at,
    }


@pytest.fixture(scope="function")
def token(test_user):
    """
    Generates a valid JWT access token for test_user.
    """
    return oauth2.create_access_token(data={"sub": test_user["email"]})


@pytest.fixture(scope="function")
def authorized_client(client, token):
    """
    Provides a TestClient pre-configured with Bearer authentication header.
    """
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}",
    }
    return client


@pytest.fixture(scope="function")
def test_posts(test_user, test_user2, session):
    """
    Seeds test posts in the database:
    2 belonging to test_user, 1 belonging to test_user2.
    """
    posts_data = [
        {
            "title": "First Post by User 1",
            "content": "Content of the first post",
            "published": True,
            "user_id": test_user["id"],
        },
        {
            "title": "Second Post by User 1",
            "content": "Content of the second post",
            "published": False,
            "user_id": test_user["id"],
        },
        {
            "title": "Post by User 2",
            "content": "Content belonging to user 2",
            "published": True,
            "user_id": test_user2["id"],
        },
    ]

    posts = [models.Post(**post) for post in posts_data]
    session.add_all(posts)
    session.commit()
    return session.query(models.Post).all()
