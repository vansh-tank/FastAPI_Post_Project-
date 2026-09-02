import pytest
from app import schemas


def test_get_all_posts_unauthenticated(client, test_posts):
    """
    Test retrieving posts without being authenticated.
    Should return HTTP 401 Unauthorized.
    """
    res = client.get("/posts/orm")
    assert res.status_code == 401


def test_get_all_posts_authenticated(authorized_client, test_posts):
    """
    Test retrieving all posts with an authenticated client.
    Should return HTTP 200 and a list of posts.
    """
    res = authorized_client.get("/posts/orm")
    assert res.status_code == 200
    posts = res.json()
    assert len(posts) == len(test_posts)


def test_get_one_post_success(authorized_client, test_posts):
    """
    Test getting a single post by valid ID.
    Should return HTTP 200 and post details.
    """
    first_post = test_posts[0]
    res = authorized_client.get(f"/posts/orm/{first_post.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["response"]["id"] == first_post.id
    assert data["response"]["title"] == first_post.title


def test_get_one_post_not_found(authorized_client):
    """
    Test getting a single post with a non-existent ID.
    Should return HTTP 404 Not Found.
    """
    res = authorized_client.get("/posts/orm/999999")
    assert res.status_code == 404


@pytest.mark.parametrize(
    "title, content, published",
    [
        ("First Title", "First Content", True),
        ("Second Title", "Second Content", False),
        ("Third Title", "Third Content", True),
    ],
)
def test_create_post_success(authorized_client, test_user, title, content, published):
    """
    Test creating a post with various payloads using parametrization.
    Should return HTTP 201 Created and the created post.
    """
    payload = {"title": title, "content": content, "published": published}
    res = authorized_client.post("/posts/orm", json=payload)
    assert res.status_code == 201
    created_data = res.json()
    assert created_data["message"] == "Post created successfully"
    created_post = created_data["post"]
    assert created_post["title"] == title
    assert created_post["content"] == content
    assert created_post["published"] == published
    assert created_post["user_id"] == test_user["id"]


def test_create_post_default_published_true(authorized_client, test_user):
    """
    Test creating a post without specifying 'published'.
    Should default published to True.
    """
    payload = {"title": "Default Published Post", "content": "Some content"}
    res = authorized_client.post("/posts/orm", json=payload)
    assert res.status_code == 201
    created_post = res.json()["post"]
    assert created_post["published"] is True


def test_create_post_unauthenticated(client):
    """
    Test creating a post without authentication.
    Should return HTTP 401 Unauthorized.
    """
    payload = {"title": "Sneaky Post", "content": "Sneaky content"}
    res = client.post("/posts/orm", json=payload)
    assert res.status_code == 401


def test_delete_post_success(authorized_client, test_user, test_posts):
    """
    Test deleting a post that belongs to the authenticated user.
    Should return HTTP 200 OK.
    """
    # test_posts[0] belongs to test_user
    post_to_delete = test_posts[0]
    res = authorized_client.delete(f"/posts/orm/{post_to_delete.id}")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Verify the post is indeed deleted
    get_res = authorized_client.get(f"/posts/orm/{post_to_delete.id}")
    assert get_res.status_code == 404


def test_delete_post_not_found(authorized_client):
    """
    Test deleting a post that does not exist.
    Should return HTTP 404 Not Found.
    """
    res = authorized_client.delete("/posts/orm/999999")
    assert res.status_code == 404


def test_delete_other_user_post_forbidden(authorized_client, test_user2, test_posts):
    """
    Test attempting to delete a post that belongs to another user.
    Should return HTTP 403 Forbidden.
    """
    # test_posts[2] was created by test_user2, but authorized_client is test_user
    other_user_post = test_posts[2]
    res = authorized_client.delete(f"/posts/orm/{other_user_post.id}")
    assert res.status_code == 403
    assert res.json()["success"] is False
    assert "not authorized" in res.json()["message"]


def test_update_post_success(authorized_client, test_user, test_posts):
    """
    Test updating a post that belongs to the authenticated user.
    Should return HTTP 200 OK.
    """
    post_to_update = test_posts[0]
    update_payload = {
        "title": "Updated Title",
        "content": "Updated Content",
        "published": False,
    }
    res = authorized_client.put(f"/posts/orm/{post_to_update.id}", json=update_payload)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Verify updated post content
    get_res = authorized_client.get(f"/posts/orm/{post_to_update.id}")
    assert get_res.json()["response"]["title"] == "Updated Title"
    assert get_res.json()["response"]["content"] == "Updated Content"
    assert get_res.json()["response"]["published"] is False


def test_update_post_not_found(authorized_client):
    """
    Test updating a post that does not exist.
    Should return HTTP 404 Not Found.
    """
    update_payload = {"title": "Updated", "content": "Updated", "published": True}
    res = authorized_client.put("/posts/orm/999999", json=update_payload)
    assert res.status_code == 404


def test_update_other_user_post_forbidden(authorized_client, test_user2, test_posts):
    """
    Test attempting to update a post that belongs to another user.
    Should return HTTP 403 Forbidden.
    """
    other_user_post = test_posts[2]
    update_payload = {"title": "Hacked Title", "content": "Hacked Content", "published": True}
    res = authorized_client.put(f"/posts/orm/{other_user_post.id}", json=update_payload)
    assert res.status_code == 403
    assert res.json()["success"] is False
    assert "not authorized" in res.json()["message"]
