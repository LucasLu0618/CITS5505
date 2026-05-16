"""Shared pytest fixtures for the KidCode Hub test suite.

This file supports two kinds of tests:

* **Unit tests** - exercise the Flask app through its built-in test client
  (fast, no browser, no network).
* **Selenium tests** - drive a real browser against a live copy of the
  server running in a background thread.

Every test runs against a throwaway in-memory SQLite database that is created
fresh before the test and dropped afterwards, so tests never touch the real
``instance/kidcode.db`` file and never interfere with each other.
"""
import os
import socket
import sys
import threading

import pytest
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

# Make the project root importable when pytest collects tests from tests/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Redirect the app at a throwaway in-memory SQLite database BEFORE importing
# connect_db. Flask-SQLAlchemy binds its database engine when the app module is
# imported, so the override has to be in place first. connect_db reads the
# DATABASE_URL environment variable and falls back to the real file otherwise.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from connect_db import app as flask_app  # noqa: E402
from database import db, User, Course  # noqa: E402


# --- test database configuration -----------------------------------------

def pytest_configure(config):
    """Relax app settings for testing.

    The throwaway in-memory database is wired up via the DATABASE_URL
    environment variable set at the top of this file (before connect_db is
    imported). Flask-SQLAlchemy automatically keeps a single shared
    connection alive for in-memory SQLite, so the database survives between
    requests and across the live-server thread. The tables inside it are
    dropped and recreated around every test (see _fresh_database).
    """
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,          # forms can be posted without a CSRF token
        SECRET_KEY="test-secret-key",
    )


# --- core fixtures -------------------------------------------------------

@pytest.fixture(autouse=True)
def _fresh_database():
    """Give every test a clean, empty set of database tables."""
    with flask_app.app_context():
        db.create_all()
    yield
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app():
    """The Flask application object, configured for testing."""
    return flask_app


@pytest.fixture
def client(app):
    """A test client for fast, browser-less HTTP requests."""
    return app.test_client()


# --- data factory fixtures -----------------------------------------------

@pytest.fixture
def make_user(app):
    """Factory that inserts a user straight into the database.

    Returns the new user's id. Default password is ``password123``.
    """
    def _make(username, email=None, password="password123", role="student"):
        email = email or (username + "@example.com")
        with app.app_context():
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
            )
            db.session.add(user)
            db.session.commit()
            return user.id
    return _make


@pytest.fixture
def make_course(app):
    """Factory that inserts a course owned by ``teacher_id``. Returns its id."""
    def _make(teacher_id, title="Intro to Scratch",
              description="Learn the basics of coding."):
        with app.app_context():
            course = Course(title=title, description=description,
                            teacher_id=teacher_id)
            db.session.add(course)
            db.session.commit()
            return course.id
    return _make


@pytest.fixture
def login_as(client):
    """Log the test client in as an existing user (by username or email)."""
    def _login(identifier, password="password123"):
        return client.post(
            "/login",
            data={"email": identifier, "password": password},
            follow_redirects=True,
        )
    return _login


# --- live server for Selenium tests --------------------------------------

def _free_port():
    """Find a free TCP port to run the live test server on."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class _LiveServer:
    """A real WSGI server running the app in a background thread."""

    def __init__(self, app):
        self.port = _free_port()
        self.url = "http://127.0.0.1:{}".format(self.port)
        self._server = make_server("127.0.0.1", self.port, app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._thread.join(timeout=5)


@pytest.fixture(scope="session")
def live_server():
    """Run the real app in a background thread for Selenium tests to hit.

    Started once and shared across all Selenium tests in the run.
    """
    server = _LiveServer(flask_app)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def browser():
    """A headless Chrome browser for Selenium tests.

    Selenium 4.6+ downloads a matching driver automatically, so the only
    requirement on the machine is that Chrome (or Chromium) is installed.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1024")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(3)
    yield driver
    driver.quit()
