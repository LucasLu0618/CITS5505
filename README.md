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
| _TODO_ | _TODO_ | _TODO_ |
| _TODO_ | _TODO_ | _TODO_ |
| _TODO_ | _TODO_ | _TODO_ |

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

> **Placeholder — to be completed before submission.**
>
> The repository does not yet contain an automated test suite. Once tests have been
> added, replace this section with the real instructions. The expected setup is:
>
> 1. Make sure the dependencies are installed (see launch instructions above) along
>    with the test runner, e.g. `pip install pytest`.
> 2. From the project root, run the test suite:
>
>    ```
>    pytest
>    ```
>
> Add a short note here describing what the tests cover (e.g. authentication, course
> enrolment, project CRUD) and any setup the tests need.
