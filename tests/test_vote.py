import pytest
from app import models


@pytest.fixture
def test_vote(test_posts, session, test_user):
    """
    Seeds a vote by test_user on test_posts[0] in the database.
    """
    new_vote = models.Vote(post_id=test_posts[0].id, user_id=test_user["id"])
    session.add(new_vote)
    session.commit()


def test_vote_on_post_success(authorized_client, test_posts):
    """
    Test voting on a post (dir = 1).
    Should return HTTP 201 Created with success message.
    """
    payload = {"post_id": test_posts[0].id, "dir": 1}
    res = authorized_client.post("/vote/", json=payload)
    assert res.status_code == 201
    assert res.json().get("message") == "Vote added successfully"


def test_vote_twice_on_same_post_conflict(authorized_client, test_posts, test_vote):
    """
    Test attempting to upvote a post twice.
    Should return HTTP 409 Conflict.
    """
    payload = {"post_id": test_posts[0].id, "dir": 1}
    res = authorized_client.post("/vote/", json=payload)
    assert res.status_code == 409
    assert "already voted" in res.json().get("detail", "")


def test_delete_vote_success(authorized_client, test_posts, test_vote):
    """
    Test removing a vote (dir = 0) on an already voted post.
    Should return HTTP 201 with 'Vote removed successfully'.
    """
    payload = {"post_id": test_posts[0].id, "dir": 0}
    res = authorized_client.post("/vote/", json=payload)
    assert res.status_code == 201
    assert res.json().get("message") == "Vote removed successfully"


def test_delete_vote_non_existent(authorized_client, test_posts):
    """
    Test removing a vote (dir = 0) when no vote was cast yet.
    Should return HTTP 404 Not Found.
    """
    payload = {"post_id": test_posts[0].id, "dir": 0}
    res = authorized_client.post("/vote/", json=payload)
    assert res.status_code == 404
    assert "does not exist" in res.json().get("detail", "")


def test_vote_post_does_not_exist(authorized_client):
    """
    Test voting on a post that does not exist.
    Should return HTTP 404 Not Found.
    """
    payload = {"post_id": 999999, "dir": 1}
    res = authorized_client.post("/vote/", json=payload)
    assert res.status_code == 404


def test_vote_unauthenticated(client, test_posts):
    """
    Test voting without authentication.
    Should return HTTP 401 Unauthorized.
    """
    payload = {"post_id": test_posts[0].id, "dir": 1}
    res = client.post("/vote/", json=payload)
    assert res.status_code == 401
