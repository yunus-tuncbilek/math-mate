"""SQLAlchemy models for Math-Mate.

Replaces the old ``sample_data/*.json`` / ``data/*.json`` storage.

SECURITY NOTE — ``Assignment.guidance_note``:
    ``guidance_note`` is the teacher's *private* instruction to the AI (e.g.
    "don't reveal answers, be encouraging"). It must NEVER reach a student.
    Never render it in a student-facing template and never include it in an API
    payload returned to a student. Use ``Assignment.to_dict(include_guidance=...)``
    and default ``include_guidance`` to False; only pass True for teacher-owned
    views. There is a test-friendly guard: ``public_dict()`` can never leak it.
"""
from datetime import datetime

from flask_login import UserMixin

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "student" | "teacher"
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # A teacher owns many classes.
    classes_taught = db.relationship(
        "Class", back_populates="teacher", cascade="all, delete-orphan"
    )
    # A student's enrollments (join rows). One email can be in many classes.
    enrollments = db.relationship(
        "ClassStudent", back_populates="student", cascade="all, delete-orphan"
    )
    chat_sessions = db.relationship(
        "ChatSession", back_populates="student", cascade="all, delete-orphan"
    )

    @property
    def is_teacher(self):
        return self.role == "teacher"

    @property
    def is_student(self):
        return self.role == "student"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    name = db.Column(db.String(255), nullable=False)
    invite_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    teacher = db.relationship("User", back_populates="classes_taught")
    student_links = db.relationship(
        "ClassStudent", back_populates="klass", cascade="all, delete-orphan"
    )
    assignments = db.relationship(
        "Assignment", back_populates="klass", cascade="all, delete-orphan"
    )
    resources = db.relationship(
        "Resource", back_populates="klass", cascade="all, delete-orphan"
    )

    @property
    def students(self):
        return [link.student for link in self.student_links]

    def __repr__(self):
        return f"<Class {self.name!r} invite={self.invite_code}>"


class ClassStudent(db.Model):
    """Join table linking students to classes (many-to-many).

    A single student (email) may belong to many classes; a class has many
    students. Enrollment happens when a student signs up with a class invite
    code.
    """

    __tablename__ = "class_students"
    __table_args__ = (
        db.UniqueConstraint("class_id", "student_id", name="uq_class_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    klass = db.relationship("Class", back_populates="student_links")
    student = db.relationship("User", back_populates="enrollments")


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # PRIVATE — teacher-only. Never expose to a student. See module docstring.
    guidance_note = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    klass = db.relationship("Class", back_populates="assignments")

    def to_dict(self, include_guidance=False):
        """Serialize the assignment.

        ``include_guidance`` MUST stay False for anything a student can see.
        Only pass True in teacher-authenticated contexts.
        """
        data = {
            "id": self.id,
            "class_id": self.class_id,
            "class_name": self.klass.name if self.klass else None,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_guidance:
            data["guidance_note"] = self.guidance_note
        return data

    def public_dict(self):
        """Guaranteed student-safe serialization (never contains guidance_note)."""
        return self.to_dict(include_guidance=False)

    def __repr__(self):
        return f"<Assignment {self.title!r}>"


class Resource(db.Model):
    """Lecture notes / PDFs per class. Distinct from homework assignments."""

    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    klass = db.relationship("Class", back_populates="resources")

    def __repr__(self):
        return f"<Resource {self.title!r}>"


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("assignments.id"), nullable=True, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("User", back_populates="chat_sessions")
    assignment = db.relationship("Assignment")
    messages = db.relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    feedback_entries = db.relationship(
        "Feedback", back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role = db.Column(db.String(20), nullable=False)  # "user" | "assistant"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    session = db.relationship("ChatSession", back_populates="messages")


class Feedback(db.Model):
    """Student feedback on an AI chat session. Table built now; UI comes later."""

    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    chat_session_id = db.Column(
        db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    rating = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    session = db.relationship("ChatSession", back_populates="feedback_entries")
