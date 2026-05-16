"""Unit tests for registration, login, logout and route protection.

These use the Flask test client - no browser involved.
"""
from database import User


def test_register_creates_user(client, app):
    """A valid registration creates a user with a hashed password."""
    response = client.post(
        "/register",
        data={
            "username": "newkid",
            "email": "newkid@example.com",
            "role": "student",
            "password": "password123",
            "confirm": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="newkid").first()
        assert user is not None
        assert user.role == "student"
        # the password must be stored hashed, never in plain text
        assert user.password_hash != "password123"


def test_register_rejects_mismatched_passwords(client, app):
    """Registration fails when the two password fields do not match."""
    response = client.post(
        "/register",
        data={
            "username": "mismatch",
            "email": "mismatch@example.com",
            "role": "student",
            "password": "password123",
            "confirm": "password999",
        },
    )
    assert b"Passwords do not match" in response.data
    with app.app_context():
        assert User.query.filter_by(username="mismatch").first() is None


def test_register_rejects_short_password(client):
    """Registration fails for passwords shorter than 8 characters."""
    response = client.post(
        "/register",
        data={
            "username": "shorty",
            "email": "shorty@example.com",
            "role": "student",
            "password": "short",
            "confirm": "short",
        },
    )
    assert b"at least 8 characters" in response.data


def test_register_rejects_duplicate_username(client, make_user):
    """Registration fails when the username is already taken."""
    make_user("taken", role="student")
    response = client.post(
        "/register",
        data={
            "username": "taken",
            "email": "different@example.com",
            "role": "student",
            "password": "password123",
            "confirm": "password123",
        },
    )
    assert b"Username already exists" in response.data


def test_login_with_correct_credentials(client, make_user):
    """Logging in with the right details populates the session."""
    make_user("loginkid", email="loginkid@example.com")
    client.post(
        "/login",
        data={"email": "loginkid@example.com", "password": "password123"},
        follow_redirects=True,
    )
    with client.session_transaction() as sess:
        assert sess.get("username") == "loginkid"
        assert sess.get("role") == "student"


def test_login_works_with_username(client, make_user):
    """A user can log in with their username instead of their email."""
    make_user("byusername")
    client.post(
        "/login",
        data={"email": "byusername", "password": "password123"},
        follow_redirects=True,
    )
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None


def test_login_with_wrong_password_fails(client, make_user):
    """A wrong password is rejected and no session is created."""
    make_user("wrongpw")
    response = client.post(
        "/login",
        data={"email": "wrongpw", "password": "notmypassword"},
    )
    assert b"Invalid username/email or password" in response.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_clears_session(client, make_user, login_as):
    """Logging out empties the session."""
    make_user("logoutkid")
    login_as("logoutkid")
    client.get("/logout")
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_profile_requires_login(client):
    """Visiting /profile while logged out redirects to the login page."""
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_course_creation_blocked_for_students(client, make_user, login_as):
    """A student cannot reach the teacher-only 'create course' page."""
    make_user("juststudent", role="student")
    login_as("juststudent")
    response = client.get("/courses/new")
    assert response.status_code == 302
    assert "/courses" in response.headers["Location"]
