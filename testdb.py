from flask import Flask
from database import db, User, Course
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kidcode.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    teacher = User(
        username="teacher1",
        email="teacher1@example.com",
        password_hash=generate_password_hash("password123"),
        role="teacher"
    )

    student = User(
        username="student1",
        email="student1@example.com",
        password_hash=generate_password_hash("password123"),
        role="student"
    )

    db.session.add(teacher)
    db.session.add(student)
    db.session.commit()

    course = Course(
        title="Scratch Basics",
        description="An introductory course for kids to learn Scratch.",
        teacher_id=teacher.id
    )

    db.session.add(course)
    db.session.commit()

    print("Sample data inserted successfully.")