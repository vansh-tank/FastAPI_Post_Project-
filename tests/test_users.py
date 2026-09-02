import pytest
from app import schemas


def test_root(client):
    """
    Test the root endpoint GET / returns a 200 OK and welcome message.
    """
    res = client.get("/")
    assert res.status_code == 200
    assert res.json().get("message") == "Welcome to my API!"


def test_create_user_success(client):
    """
    Test creating a new user with valid email and password.
    Should return HTTP 201 Created.
    """
    payload = {"email": "hello@example.com", "password": "securepassword123"}
    res = client.post("/users/", json=payload)
    assert res.status_code == 201
    assert res.json().get("message") == "User created successfully"


def test_create_user_invalid_email(client):
    """
    Test creating a user with an invalid email format.
    Pydantic EmailStr validation should reject it with HTTP 422.
    """
    payload = {"email": "not-a-valid-email", "password": "password123"}
    res = client.post("/users/", json=payload)
    assert res.status_code == 422


def test_create_user_duplicate_email(client, test_user):
    """
    Test creating a user with an email that already exists.
    Should raise HTTP 409 Conflict.
    """
    payload = {"email": test_user["email"], "password": "newpassword123"}
    res = client.post("/users/", json=payload)
    assert res.status_code == 409
    assert "already exists" in res.json().get("detail", "")


def test_get_user_by_id_success(client, test_user):
    """
    Test retrieving an existing user by ID.
    Should return HTTP 200 OK with email and id, and never expose password.
    """
    res = client.get(f"/users/{test_user['id']}")
    assert res.status_code == 200
    user_response = res.json()
    assert user_response["id"] == test_user["id"]
    assert user_response["email"] == test_user["email"]
    assert "password" not in user_response


def test_get_user_not_found(client):
    """
    Test retrieving a user with an ID that does not exist.
    Should return HTTP 404 Not Found.
    """
    res = client.get("/users/999999")
    assert res.status_code == 404
    assert res.json().get("detail") == "User with id 999999 not found"