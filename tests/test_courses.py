"""Unit tests for course creation, enrolment and leaving courses.

These use the Flask test client - no browser involved.
"""
from database import Course, Enrollment


def test_teacher_can_create_course(client, make_user, login_as, app):
    """A logged-in teacher can create a new course."""
    make_user("teacher1", role="teacher")
    login_as("teacher1")
    response = client.post(
        "/courses/new",
        data={"title": "Python for Kids", "description": "A fun intro to Python."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Course.query.filter_by(title="Python for Kids").first() is not None


def test_student_cannot_create_course(client, make_user, login_as, app):
    """A student is blocked from creating a course."""
    make_user("student1", role="student")
    login_as("student1")
    response = client.post(
        "/courses/new",
        data={"title": "Sneaky Course", "description": "Should not be created."},
    )
    assert response.status_code == 302  # bounced away by teacher_required
    with app.app_context():
        assert Course.query.filter_by(title="Sneaky Course").first() is None


def test_student_can_join_course(client, make_user, make_course, login_as, app):
    """A student can enrol in a course."""
    teacher_id = make_user("teacher2", role="teacher")
    student_id = make_user("student2", role="student")
    course_id = make_course(teacher_id)
    login_as("student2")
    client.post("/courses/{}/join".format(course_id), follow_redirects=True)
    with app.app_context():
        enrollment = Enrollment.query.filter_by(
            student_id=student_id, course_id=course_id
        ).first()
        assert enrollment is not None


def test_student_cannot_join_twice(client, make_user, make_course, login_as, app):
    """Joining the same course twice does not create a duplicate enrolment."""
    teacher_id = make_user("teacher3", role="teacher")
    student_id = make_user("student3", role="student")
    course_id = make_course(teacher_id)
    login_as("student3")
    client.post("/courses/{}/join".format(course_id), follow_redirects=True)
    client.post("/courses/{}/join".format(course_id), follow_redirects=True)
    with app.app_context():
        count = Enrollment.query.filter_by(
            student_id=student_id, course_id=course_id
        ).count()
        assert count == 1


def test_student_can_leave_course(client, make_user, make_course, login_as, app):
    """A student who has joined a course can leave it again."""
    teacher_id = make_user("teacher4", role="teacher")
    student_id = make_user("student4", role="student")
    course_id = make_course(teacher_id)
    login_as("student4")
    client.post("/courses/{}/join".format(course_id), follow_redirects=True)
    client.post("/courses/{}/leave".format(course_id), follow_redirects=True)
    with app.app_context():
        enrollment = Enrollment.query.filter_by(
            student_id=student_id, course_id=course_id
        ).first()
        assert enrollment is None


def test_course_detail_page_loads(client, make_user, make_course):
    """The public course detail page renders and shows the course title."""
    teacher_id = make_user("teacher5", role="teacher")
    course_id = make_course(teacher_id, title="Web Design 101")
    response = client.get("/courses/{}".format(course_id))
    assert response.status_code == 200
    assert b"Web Design 101" in response.data
