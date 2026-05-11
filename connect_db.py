import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from database import db, User, Course, Assignment, Submission

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kidcode.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-for-local-only")

db.init_app(app)
csrf = CSRFProtect(app)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def teacher_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if session.get("role") != "teacher":
            flash("Only teachers can do that.", "error")
            return redirect(url_for("courses_page"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


@app.route("/")
def home():
    courses = Course.query.limit(3).all()
    return render_template("index.html", courses=courses)


@app.route("/courses")
def courses_page():
    courses = Course.query.all()
    return render_template("courses.html", courses=courses)

@app.route("/courses/<int:course_id>")
def course_details(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template(
        "course_detail.html",
        course=course,
        lessons=[],
        assignments=[],
        resources=[],
        is_owner=(session.get("user_id") == course.teacher_id),
    )

@app.route("/courses/new", methods=["GET", "POST"])
@teacher_required
def course_new():
    errors = []
    title = ""
    description = ""

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()

        if not title:
            errors.append("Title is required.")
        elif len(title) > 120:
            errors.append("Title must be 120 characters or fewer.")

        if not description:
            errors.append("Description is required.")

        if not errors:
            course = Course(
                title=title,
                description=description,
                teacher_id=session["user_id"],
            )
            db.session.add(course)
            db.session.commit()
            flash(f"Course '{course.title}' created.", "success")
            return redirect(url_for("courses_page"))

    return render_template(
        "course_new.html",
        errors=errors,
        title=title,
        description=description,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        identifier = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("home"))
        else:
            error = "Invalid username/email or password."

    return render_template("login.html", error=error)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        user = User.query.filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()

        if not identifier or not new_password or not confirm_password:
            error = "Please fill in all fields."
        elif user is None:
            error = "No account found with that username or email."
        elif len(new_password) < 8:
            error = "Password must be at least 8 characters long."
        elif new_password != confirm_password:
            error = "Passwords do not match."
        elif check_password_hash(user.password_hash, new_password):
            error = "New password must be different from your old password."
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Password reset successful. Please log in with your new password.", "success")
            return redirect(url_for("login"))

    return render_template("forgot_password.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        role = request.form.get("role")
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not username or not email or not role or not password or not confirm:
            error = "Please fill in all fields."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        elif User.query.filter_by(username=username).first():
            error = "Username already exists."
        elif User.query.filter_by(email=email).first():
            error = "Email already exists."
        else:
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("register.html", error=error)


@app.route("/showcase")
def showcase():
    featured_submissions = Submission.query.filter_by(is_featured=True).all()
    return render_template("showcase.html", submissions=featured_submissions)


@app.route("/profile")
@login_required
def profile():
    user = current_user()
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    if user.role == "teacher":
        courses = Course.query.filter_by(teacher_id=user.id).order_by(Course.created_at.desc()).all()
        course_ids = [c.id for c in courses]

        assignments = []
        submissions_to_review = []
        if course_ids:
            assignments = (
                Assignment.query.filter(Assignment.course_id.in_(course_ids))
                .order_by(Assignment.created_at.desc())
                .all()
            )
            assignment_ids = [a.id for a in assignments]
            if assignment_ids:
                submissions_to_review = (
                    Submission.query.filter(Submission.assignment_id.in_(assignment_ids))
                    .order_by(Submission.created_at.desc())
                    .all()
                )

        return render_template(
            "teacher_profile.html",
            user=user,
            courses=courses,
            assignments=assignments,
            submissions_to_review=submissions_to_review,
        )

    my_submissions = (
        Submission.query.filter_by(student_id=user.id)
        .order_by(Submission.created_at.desc())
        .all()
    )
    featured = [s for s in my_submissions if s.is_featured]
    available_assignments = (
        Assignment.query.order_by(Assignment.due_date.is_(None), Assignment.due_date.asc()).all()
    )

    return render_template(
        "student_profile.html",
        user=user,
        submissions=my_submissions,
        featured=featured,
        assignments=available_assignments,
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    user = current_user()
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    errors = []

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        current_password = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not username or not email:
            errors.append("Username and email cannot be empty.")

        if username and username != user.username:
            clash = User.query.filter(User.username == username, User.id != user.id).first()
            if clash:
                errors.append("Username already in use.")

        if email and email != user.email:
            clash = User.query.filter(User.email == email, User.id != user.id).first()
            if clash:
                errors.append("Email already in use.")

        wants_password_change = any([current_password, new_password, confirm_password])
        if wants_password_change:
            if not check_password_hash(user.password_hash, current_password):
                errors.append("Current password is incorrect.")
            if len(new_password) < 8:
                errors.append("New password must be at least 8 characters long.")
            if new_password != confirm_password:
                errors.append("New passwords do not match.")
            if check_password_hash(user.password_hash, new_password):
                errors.append("New password must be different from your current password.")

        if not errors:
            user.username = username
            user.email = email
            if wants_password_change:
                user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            session["username"] = user.username
            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))

    return render_template("profile_edit.html", user=user, errors=errors)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)