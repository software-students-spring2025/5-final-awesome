import pytest
from unittest.mock import patch, MagicMock
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

    # 3. GET nonexistent poll
    mock_db["polls"].find_one.return_value = None
    response = client.get("/poll/doesnotexist")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


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
    mock_users.find_one.return_value = None

    resp = client.post(
        "/signup",
        data={"username": "unique", "password": "secret"},
        follow_redirects=False,
    )
    assert mock_users.insert_one.call_count == 1
    inserted = mock_users.insert_one.call_args[0][0]

    assert inserted["username"] == "unique"
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
        "_id": 123,
        "username": "alice",
        "password": pw_hash,
    }

    resp = client.post(
        "/login",
        data={"username": "alice", "password": "secret"},
        follow_redirects=False,
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
        "/login", data={"username": "bob", "password": "wrong"}, follow_redirects=False
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


@patch("app.render_template")
@patch("app.current_user")
@patch("app.database")
def test_profile_requires_login(mock_db, mock_current_user, mock_render, client):
    resp = client.get("/profile", follow_redirects=False)
    assert resp.status_code == 302
    # login_required should bounce to /login?next=/profile
    assert resp.headers["Location"].startswith("/login")
    mock_db["polls"].find.assert_not_called()
    mock_render.assert_not_called()


@patch("app.render_template")
@patch("app.database")
def test_poll_results(mock_db, mock_render, client):
    mock_db["polls"].find_one.return_value = {"_id": "123456"}
    response = client.get("/poll/123456/results")
    assert response.status_code == 200
    mock_render.assert_called()


@patch("app.render_template")
@patch("app.database")
@patch("app.current_user")
def test_profile_no_query(mock_current_user, mock_db, mock_render, client):
    owner = "aaaaaaaaaaaaaaaaaaaaaaaa"
    mock_current_user.id = owner
    POLL1 = {
        "_id": ObjectId(),
        "question": "First Poll",
        "options": [{"text": "Yes"}, {"text": "No"}],
        "owner": ObjectId(owner),
    }
    POLL2 = {
        "_id": ObjectId(),
        "question": "Searchable Poll",
        "options": [{"text": "Foo"}, {"text": "Bar"}],
        "owner": ObjectId(owner),
    }

    with client.session_transaction() as sess:
        sess["_user_id"] = "680930a5ee1e01323d98a8b2"

    # Stub out database["polls"].find() to return our two sample polls
    mock_collection = MagicMock()
    mock_collection.find.return_value = [POLL1, POLL2]
    mock_db.__getitem__.return_value = mock_collection

    rv = client.get("/profile")
    assert rv.status_code == 200

    # Ensure we rendered the right template once
    mock_render.assert_called_once()
    args, kwargs = mock_render.call_args

    # First positional arg is the template name
    assert args[0] == "profile.html"
    # The view should pass an empty query
    assert kwargs["query"] == ""
    # Both polls should be returned
    assert len(kwargs["polls"]) == 2
    titles = {p["question"] for p in kwargs["polls"]}
    assert titles == {"First Poll", "Searchable Poll"}


@patch("app.database")
def test_avatar_update_success(mock_db, client):
    mock_db["users"].update_one.return_value = {
        "_id": 123,
        "username": "alice",
        "password": 12345678,
        "avatar": "https://testURL",
    }
    response = client.post(
        "/avatar",
        data={"avatar_url": "https://testURL", "username": "testUser"},
        follow_redirects=False,
    )
    mock_db["users"].update_one.assert_called_once()
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")


@patch("app.database")
def test_avatar_update_failure(mock_db, client):
    mock_db["users"].update_one.side_effect = Exception("Test error")
    response = client.post(
        "/avatar",
        data={"avatar_url": "https://testURL", "username": "testUser"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


@patch("app.render_template")
@patch("app.database")
def test_poll_created_exists(mock_db, mock_render, client):
    # Arrange: make the DB return a poll
    mock_poll = {
        "_id": "abc123",
        "question": "Is this working?",
        "options": [{"text": "Yes", "votes": 0}, {"text": "No", "votes": 0}],
    }
    mock_db["polls"].find_one.return_value = mock_poll

    # Act
    resp = client.get("/created/abc123")

    # Assert
    assert resp.status_code == 200
    mock_render.assert_called_once_with("created.html", poll=mock_poll)


@patch("app.render_template")
@patch("app.database")
def test_poll_created_not_found(mock_db, mock_render, client):
    # Arrange: make the DB return nothing
    mock_db["polls"].find_one.return_value = None

    # Act
    resp = client.get("/created/doesnotexist")

    # Assert
    assert resp.status_code == 404
    assert b"Poll not found" in resp.data
