"""Selenium (end-to-end) tests - drive a real browser against a live server.

Unlike the unit tests, these start an actual copy of the KidCode Hub server
in a background thread (see the ``live_server`` fixture in conftest.py) and
use a headless Chrome browser to click through real pages.

Requirements to run these:
  * pip install selenium
  * Google Chrome (or Chromium) installed on the machine.
    Selenium 4.6+ downloads the matching driver automatically.

If selenium is not installed the whole module is skipped rather than failing.
"""
import pytest

pytest.importorskip("selenium")

from selenium.webdriver.common.by import By              # noqa: E402
from selenium.webdriver.support.ui import Select, WebDriverWait  # noqa: E402
from selenium.common.exceptions import (                 # noqa: E402
    NoAlertPresentException,
    TimeoutException,
)


# --- small helpers -------------------------------------------------------

def _register(browser, base_url, username, password="password123", role="student"):
    """Fill in and submit the registration form."""
    browser.get(base_url + "/register")
    browser.find_element(By.ID, "username").send_keys(username)
    browser.find_element(By.ID, "email").send_keys(username + "@example.com")
    Select(browser.find_element(By.ID, "role")).select_by_value(role)
    browser.find_element(By.ID, "password").send_keys(password)
    browser.find_element(By.ID, "confirm").send_keys(password)
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()


def _login(browser, base_url, identifier, password="password123"):
    """Fill in and submit the login form."""
    browser.get(base_url + "/login")
    browser.find_element(By.ID, "email").send_keys(identifier)
    browser.find_element(By.ID, "password").send_keys(password)
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()


def _accept_any_confirm(browser):
    """Some forms pop a 'Are you sure?' confirm() dialog - accept it if shown."""
    try:
        WebDriverWait(browser, 2).until(lambda d: d.switch_to.alert)
        browser.switch_to.alert.accept()
    except (TimeoutException, NoAlertPresentException):
        pass


# --- tests ---------------------------------------------------------------

def test_home_page_loads(browser, live_server):
    """The home page loads and shows the site name."""
    browser.get(live_server.url + "/")
    assert "KidCode Hub" in browser.page_source


def test_register_new_student(browser, live_server):
    """Registering through the form sends the user to the login page."""
    _register(browser, live_server.url, "seleniumkid")
    WebDriverWait(browser, 5).until(lambda d: "/login" in d.current_url)
    assert "/login" in browser.current_url


def test_login_with_valid_credentials(browser, live_server):
    """A registered user can log in and then sees a Logout link."""
    _register(browser, live_server.url, "loginuser")
    _login(browser, live_server.url, "loginuser")
    logout_link = WebDriverWait(browser, 5).until(
        lambda d: d.find_element(By.LINK_TEXT, "Logout")
    )
    assert logout_link is not None


def test_login_with_invalid_credentials_shows_error(browser, live_server):
    """Logging in with bad credentials shows an error message."""
    _login(browser, live_server.url, "ghost", "wrongpassword")
    WebDriverWait(browser, 5).until(
        lambda d: "Invalid username/email or password" in d.page_source
    )
    assert "Invalid username/email or password" in browser.page_source


def test_student_can_add_project(browser, live_server):
    """A logged-in student can add a project and see it on their profile."""
    _register(browser, live_server.url, "projmaker")
    _login(browser, live_server.url, "projmaker")
    browser.get(live_server.url + "/projects/new")
    browser.find_element(By.ID, "title").send_keys("My Selenium Project")
    browser.find_element(By.ID, "description").send_keys(
        "Built and tested end to end with Selenium."
    )
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    _accept_any_confirm(browser)  # the add-project form asks for confirmation
    WebDriverWait(browser, 5).until(
        lambda d: "My Selenium Project" in d.page_source
    )
    assert "My Selenium Project" in browser.page_source


def test_showcase_page_is_reachable_from_nav(browser, live_server):
    """The Showcase link in the navigation bar opens the showcase page."""
    browser.get(live_server.url + "/")
    browser.find_element(By.LINK_TEXT, "Showcase").click()
    WebDriverWait(browser, 5).until(lambda d: "/showcase" in d.current_url)
    assert "Student Project" in browser.page_source


def test_logout_returns_to_login(browser, live_server):
    """Clicking Logout ends the session and brings back the Login link."""
    _register(browser, live_server.url, "logoutuser")
    _login(browser, live_server.url, "logoutuser")
    WebDriverWait(browser, 5).until(
        lambda d: d.find_element(By.LINK_TEXT, "Logout")
    ).click()
    login_link = WebDriverWait(browser, 5).until(
        lambda d: d.find_element(By.LINK_TEXT, "Login")
    )
    assert login_link is not None
