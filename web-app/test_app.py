import pytest
from unittest.mock import patch
from app import app
from flask import url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash
from bson import ObjectId


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


@patch("app.render_template")
def test_index_route(mock_render, client):
    client.get("/")
    mock_render.assert_called_with("index.html", user=current_user)


@patch("app.random.randint")
@patch("app.render_template")
@patch("app.database")
def test_create_poll(mock_db, mock_render, mock_randint, client):
    # 1. GET request should render create.html
    response = client.get("/create")
    assert response.status_code == 200
    mock_render.assert_called_with("create.html")

    # 2. POST request: mock poll_id = 123456
    mock_db["polls"].find_one.return_value = None
    mock_randint.return_value = 123456  # control randomness
    response = client.post(
        "/create",
        data={"question": "Test?", "options": ["A", "B"]},
        follow_redirects=False,
    )
    mock_db["polls"].insert_one.assert_called_once()
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/created/123456")


@patch("app.render_template")
@patch("app.database")
def test_view_poll(mock_db, mock_render, client):
    # 1. GET existing poll
    mock_poll = {
        "_id": "abc123",
        "question": "Pick one",
        "options": [{"text": "Red", "votes": 0}],
    }
    mock_db["polls"].find_one.return_value = mock_poll
    response = client.get("/poll/abc123")
    assert response.status_code == 200
    mock_render.assert_called_with("poll.html", poll=mock_poll)

    # 2. POST to vote
    response = client.post("/poll/abc123", data={"option": "0"}, follow_redirects=False)
    mock_db["polls"].update_one.assert_called()
    assert response.status_code == 302
    assert "/poll/abc123" in response.headers["Location"]

    # 3. GET nonexistent poll
    mock_db["polls"].find_one.return_value = None
    response = client.get("/poll/doesnotexist")
    assert response.status_code == 404


@patch("app.render_template")
@patch("app.database")
def test_edit_poll(mock_db, mock_render, client):
    # 1. GET existing poll
    mock_poll = {"_id": "abc123", "question": "Edit me", "options": []}
    mock_db["polls"].find_one.return_value = mock_poll
    response = client.get("/created/abc123/edit")
    assert response.status_code == 200
    mock_render.assert_called_with("edit.html", poll=mock_poll)

    # 2. POST update with valid data
    response = client.post(
        "/created/abc123/edit",
        data={"question": "Updated?", "options": ["New A", "New B"]},
        follow_redirects=False,
    )
    mock_db["polls"].update_one.assert_called_with(
        {"_id": "abc123"},
        {
            "$set": {
                "question": "Updated?",
                "options": [
                    {"text": "New A", "votes": 0},
                    {"text": "New B", "votes": 0},
                ],
            }
        },
    )
    assert response.status_code == 302

    # 3. POST with missing data
    response = client.post("/created/abc123/edit", data={"question": "", "options": []})
    assert response.status_code == 400

    # 4. GET non-existent poll
    mock_db["polls"].find_one.return_value = None
    response = client.get("/created/xyz/edit")
    assert response.status_code == 404


@patch("app.render_template")
@patch("app.database")
def test_signup_get(mock_db, mock_render, client):
    mock_render.return_value = b"signup page"
    resp = client.get("/signup")
    mock_render.assert_called_once_with("signup.html")
    assert resp.data == b"signup page"
    assert resp.status_code == 200


@patch("app.database")
def test_signup_post_creates_user_and_redirects(mock_db, client):
    mock_users = mock_db["users"]

    resp = client.post(
        "/signup",
        data={"username": "alice", "password": "secret"},
        follow_redirects=False
    )
    assert mock_users.insert_one.call_count == 1
    inserted = mock_users.insert_one.call_args[0][0]

    assert inserted["username"] == "alice"
    assert inserted["password"] != "secret"

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


@patch("app.render_template")
@patch("app.database")
def test_login_get(mock_db, mock_render, client):
    mock_render.return_value = b"login page"
    resp = client.get("/login")
    mock_render.assert_called_once_with("login.html")
    assert resp.data == b"login page"
    assert resp.status_code == 200


@patch("app.login_user")
@patch("app.database")
def test_login_post_success(mock_db, mock_login_user, client):
    # pretend there is a user with a hashed password
    pw_hash = generate_password_hash("secret")
    mock_db["users"].find_one.return_value = {
        "_id": 123, "username": "alice", "password": pw_hash
    }

    resp = client.post(
        "/login",
        data={"username": "alice", "password": "secret"},
        follow_redirects=False
    )

    # Assert login_user was called with a User instance
    assert mock_login_user.call_count == 1
    assert resp.status_code == 302

@patch("app.login_user")
@patch("app.database")
def test_login_post_failure(mock_db, mock_login_user, client):
    # no such user
    mock_db["users"].find_one.return_value = None

    resp = client.post(
        "/login",
        data={"username": "bob", "password": "wrong"},
        follow_redirects=False
    )

    # Assert login_user was never called
    assert mock_login_user.call_count == 0
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


@patch("app.logout_user")
@patch("app.database")
def test_logout_when_logged_in(mock_db, mock_logout_user, client):
    with client.session_transaction() as sess:
        sess["_user_id"] = "680930a5ee1e01323d98a8b2"

    resp = client.get("/logout", follow_redirects=False)

    assert mock_logout_user.call_count == 1
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")