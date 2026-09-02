import pytest
from jose import jwt
from app.config import settings
from app import schemas


def test_login_user_success(client, test_user):
    """
    Test logging in with valid user credentials via OAuth2 form-data.
    Should return HTTP 200, an access token, and token type 'bearer'.
    """
    res = client.post(
        "/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert res.status_code == 200
    token_res = res.json()
    assert token_res.get("token_type") == "bearer"
    assert "access_token" in token_res

    # Verify the JWT token can be decoded and contains correct subject
    payload = jwt.decode(
        token_res["access_token"], settings.secret_key, algorithms=[settings.algorithm]
    )
    assert payload.get("sub") == test_user["email"]


@pytest.mark.parametrize(
    "email, password, expected_status",
    [
        ("wrongemail@example.com", "password123", 403),
        ("testuser@example.com", "wrongpassword", 403),
        ("wrongemail@example.com", "wrongpassword", 403),
    ],
)
def test_login_incorrect_credentials(client, test_user, email, password, expected_status):
    """
    Test logging in with various incorrect credentials.
    Should return HTTP 403 Forbidden with 'Invalid email or password'.
    """
    res = client.post("/login", data={"username": email, "password": password})
    assert res.status_code == expected_status
    assert res.json().get("detail") == "Invalid email or password"


def test_login_missing_fields(client):
    """
    Test logging in with missing username or password fields.
    FastAPI / OAuth2PasswordRequestForm should reject with HTTP 422 Unprocessable Entity.
    """
    res = client.post("/login", data={"username": "testuser@example.com"})
    assert res.status_code == 422
