# KidCode Hub

KidCode Hub is a web application that gives young learners a friendly place to learn
to code and gives their teachers the tools to guide them. It is built as a group
project for **CITS5505 Agile Web Development** at the University of Western Australia.

## Purpose, design and use

### Purpose

KidCode Hub brings teachers and young students together around coding courses. Teachers
publish courses, lessons, assignments and learning resources; students enrol in those
courses, submit their work, and build a portfolio of personal projects. The best work
is celebrated on a public showcase so learners can see what their peers are creating.

### Design

The application is a server-rendered Flask app following a simple, classic web
architecture:

- **Backend** — Python with Flask. Routing, authentication, authorisation and form
  handling all live in `connect_db.py`.
- **Data layer** — SQLAlchemy ORM models defined in `database.py`, persisted to a
  SQLite database (`instance/kidcode.db`). The schema covers users, courses, lessons,
  assignments, submissions, resources, enrolments and student projects.
- **Frontend** — Jinja2 templates in `templates/` with shared styling in
  `static/style.css` and light interactivity in `static/script.js`.
- **Security** — passwords are hashed with Werkzeug, sessions track the logged-in
  user, role-based decorators (`login_required`, `teacher_required`) protect routes,
  and Flask-WTF provides CSRF protection on every form.

### Use

There are two roles, each with its own experience:

**Teachers** can create courses, add lessons and assignments, upload resources, review
student submissions, leave feedback and scores, and feature outstanding work on the
showcase.

**Students** can browse and enrol in courses, leave a course they no longer want,
submit work to assignments, receive feedback, add their own projects (with a title,
description and link), and manage those projects from their profile. Student projects
appear on the public showcase, and every student has a public profile page showing
their details, projects and courses.

Anyone — logged in or not — can browse courses, view the project showcase, and open a
student's public profile.

## Group members

| UWA ID | Name | GitHub username |
| ------ | ---- | --------------- |
| 24527328 | Yiyang Lu | LucasLu0618 |
|  24281099 | Sagar Ganagi | sagar-ganagi |
|  24368932 | Shee Wang | XI WANG |

## How to launch the application

The application needs **Python 3.10 or newer**.

1. **Clone the repository**

   ```
   git clone https://github.com/LucasLu0618/CITS5505.git
   cd CITS5505
   ```

2. **Create and activate a virtual environment**

   On Windows (PowerShell):

   ```
   python -m venv venv
   .\venv\Scripts\activate
   ```

   On macOS / Linux:

   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the dependencies**

   ```
   pip install -r requirements.txt
   ```

4. **(Optional) Set a secret key**

   The app reads `SECRET_KEY` from a `.env` file and falls back to a development key
   if none is set. For a non-default key, create a `.env` file in the project root:

   ```
   SECRET_KEY=your-own-secret-value
   ```

5. **Run the application**

   ```
   python connect_db.py
   ```

   The database tables are created automatically on first run. Open your browser at
   <http://127.0.0.1:5000> to use the app.

6. **(Optional) Add sample data**

   To populate the database with a sample teacher, student and course, run:

   ```
   python testdb.py
   ```

## How to run the tests

The test suite lives in the `tests/` folder and has two parts:

- **Unit tests** (`test_auth.py`, `test_courses.py`, `test_projects.py`) — 25 tests
  that exercise the Flask app through its built-in test client. They cover
  registration and login, role-based access control, course creation, joining and
  leaving courses, and the full create/edit/delete lifecycle of student projects.
  They are fast and need no browser.
- **Selenium tests** (`test_selenium.py`) — 7 tests that drive a real headless
  Chrome browser against a live copy of the server. `tests/conftest.py` starts the
  Flask app on a background thread (the `live_server` fixture) so these tests hit a
  genuinely running server, just as a real user would. They cover the home page,
  registration, valid and invalid login, adding a project, navigating to the
  showcase, and logging out.

Every test runs against a throwaway in-memory SQLite database that is created fresh
before each test and dropped afterwards, so the tests never touch the real
`instance/kidcode.db` file.

1. **Install the dependencies** (the testing tools are already in
   `requirements.txt`):

   ```
   pip install -r requirements.txt
   ```

   The Selenium tests also need **Google Chrome** (or Chromium) installed on the
   machine. Selenium downloads a matching driver automatically — no extra setup
   needed.

2. **Run the whole suite**

   ```
   pytest
   ```

3. **Run just the fast unit tests** (no browser required)

   ```
   pytest tests/test_auth.py tests/test_courses.py tests/test_projects.py
   ```

4. **Run just the Selenium tests**

   ```
   pytest tests/test_selenium.py
   ```

