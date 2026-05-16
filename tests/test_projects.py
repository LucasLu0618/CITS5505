"""Unit tests for student project CRUD and public display.

These use the Flask test client - no browser involved.
"""
from database import db, Project


def _add_project(app, student_id, title="My Game",
                 description="A cool game.", link=None):
    """Helper: insert a project directly into the database, return its id."""
    with app.app_context():
        project = Project(student_id=student_id, title=title,
                          description=description, link=link)
        db.session.add(project)
        db.session.commit()
        return project.id


def test_student_can_add_project(client, make_user, login_as, app):
    """A logged-in student can add a project through the form."""
    make_user("projkid", role="student")
    login_as("projkid")
    response = client.post(
        "/projects/new",
        data={
            "title": "My First Game",
            "description": "Made with Scratch.",
            "link": "https://example.com/game",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        project = Project.query.filter_by(title="My First Game").first()
        assert project is not None
        assert project.link == "https://example.com/game"


def test_teacher_cannot_add_project(client, make_user, login_as, app):
    """A teacher is not allowed to add a student project."""
    make_user("teacherx", role="teacher")
    login_as("teacherx")
    response = client.post(
        "/projects/new",
        data={"title": "Teacher Project", "description": "Nope."},
    )
    assert response.status_code == 302  # redirected away
    with app.app_context():
        assert Project.query.filter_by(title="Teacher Project").first() is None


def test_project_requires_title_and_description(client, make_user, login_as, app):
    """Submitting an empty project form is rejected with a validation error."""
    make_user("validatekid", role="student")
    login_as("validatekid")
    response = client.post(
        "/projects/new",
        data={"title": "", "description": ""},
    )
    assert b"required" in response.data
    with app.app_context():
        assert Project.query.count() == 0


def test_student_can_edit_own_project(client, make_user, login_as, app):
    """A student can edit a project they own."""
    student_id = make_user("editkid", role="student")
    project_id = _add_project(app, student_id, title="Old Title")
    login_as("editkid")
    client.post(
        "/projects/{}/edit".format(project_id),
        data={"title": "New Title", "description": "Updated description."},
        follow_redirects=True,
    )
    with app.app_context():
        assert db.session.get(Project, project_id).title == "New Title"


def test_student_cannot_edit_someone_elses_project(client, make_user, login_as, app):
    """A student cannot edit a project that belongs to someone else."""
    owner_id = make_user("owner", role="student")
    make_user("intruder", role="student")
    project_id = _add_project(app, owner_id, title="Owned Project")
    login_as("intruder")
    response = client.post(
        "/projects/{}/edit".format(project_id),
        data={"title": "Hijacked", "description": "Changed by intruder."},
    )
    assert response.status_code == 302  # ownership check redirects away
    with app.app_context():
        assert db.session.get(Project, project_id).title == "Owned Project"


def test_student_can_delete_own_project(client, make_user, login_as, app):
    """A student can delete a project they own."""
    student_id = make_user("delkid", role="student")
    project_id = _add_project(app, student_id)
    login_as("delkid")
    client.post("/projects/{}/delete".format(project_id), follow_redirects=True)
    with app.app_context():
        assert db.session.get(Project, project_id) is None


def test_student_cannot_delete_someone_elses_project(client, make_user, login_as, app):
    """A student cannot delete a project that belongs to someone else."""
    owner_id = make_user("owner2", role="student")
    make_user("intruder2", role="student")
    project_id = _add_project(app, owner_id)
    login_as("intruder2")
    client.post("/projects/{}/delete".format(project_id), follow_redirects=True)
    with app.app_context():
        assert db.session.get(Project, project_id) is not None


def test_project_appears_on_showcase(client, make_user, app):
    """A student's project is shown on the public showcase page."""
    student_id = make_user("showkid", role="student")
    _add_project(app, student_id, title="Showcased Project")
    response = client.get("/showcase")
    assert response.status_code == 200
    assert b"Showcased Project" in response.data


def test_project_appears_on_public_profile(client, make_user, app):
    """A student's project is shown on their public profile page."""
    student_id = make_user("publickid", role="student")
    _add_project(app, student_id, title="Profile Project")
    response = client.get("/users/{}".format(student_id))
    assert response.status_code == 200
    assert b"Profile Project" in response.data
