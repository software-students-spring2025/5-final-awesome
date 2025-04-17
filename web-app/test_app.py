import pytest
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


@patch("app.render_template")
def test_index_route(mock_render, client):
    client.get("/")
    mock_render.assert_called_with("index.html")


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
    assert "/poll/123456" in response.headers["Location"]


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
    response = client.get("/poll/abc123/edit")
    assert response.status_code == 200
    mock_render.assert_called_with("edit.html", poll=mock_poll)

    # 2. POST update with valid data
    response = client.post(
        "/poll/abc123/edit",
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
    response = client.post("/poll/abc123/edit", data={"question": "", "options": []})
    assert response.status_code == 400

    # 4. GET non-existent poll
    mock_db["polls"].find_one.return_value = None
    response = client.get("/poll/xyz/edit")
    assert response.status_code == 404
