from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import or_
from werkzeug.security import check_password_hash
from database import db, User, Course, Submission
from werkzeug.security import generate_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kidcode.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-key"

db.init_app(app)


@app.route("/")
def home():
    courses = Course.query.limit(3).all()
    return render_template("index.html", courses=courses)


@app.route("/courses")
def courses_page():
    courses = Course.query.all()
    return render_template("courses.html", courses=courses)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        identifier = request.form.get("email")
        password = request.form.get("password")

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
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        role = request.form.get("role")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

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
            return redirect(url_for("login"))

    return render_template("register.html", error=error)


@app.route("/showcase")
def showcase():
    featured_submissions = Submission.query.filter_by(is_featured=True).all()
    return render_template("showcase.html", submissions=featured_submissions)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)