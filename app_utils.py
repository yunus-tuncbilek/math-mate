"""Data-access helpers.

The JSON helpers (``load_json`` / ``save_json``) are retained because the seed
script (``seed.py``) still reads the legacy ``sample_data/*.json`` files. All
application reads/writes now go through the SQLAlchemy helpers below.
"""
import json
import os
import secrets
import string

from werkzeug.security import generate_password_hash

from extensions import db
from models import (
    User,
    Class,
    ClassStudent,
    Assignment,
    Resource,
    ChatSession,
    ChatMessage,
    Feedback,
)


# --------------------------------------------------------------------------- #
# Legacy JSON helpers (used only by the seed / migration script)
# --------------------------------------------------------------------------- #
def load_json(folder, filename, default=""):
    full_path = os.path.join(folder, filename)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return default
    return default


def save_json(folder, filename, data=""):
    # atomic write to avoid corruption from concurrent processes
    full_path = os.path.join(folder, filename)
    tmp = full_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, full_path)


# --------------------------------------------------------------------------- #
# Users / auth
# --------------------------------------------------------------------------- #
def get_user_by_email(email):
    if not email:
        return None
    return User.query.filter_by(email=email.strip().lower()).first()


def create_user(email, name, password, role):
    user = User(
        email=email.strip().lower(),
        name=name.strip(),
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


# --------------------------------------------------------------------------- #
# Classes / enrollment
# --------------------------------------------------------------------------- #
def generate_invite_code(length=6):
    """Return a short, unambiguous, unique invite code."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no easily-confused chars
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        if not Class.query.filter_by(invite_code=code).first():
            return code


def create_class(teacher, name):
    klass = Class(teacher_id=teacher.id, name=name.strip(), invite_code=generate_invite_code())
    db.session.add(klass)
    db.session.commit()
    return klass


def get_class_by_invite_code(code):
    if not code:
        return None
    return Class.query.filter_by(invite_code=code.strip().upper()).first()


def enroll_student(klass, student):
    """Link a student to a class. Returns True if newly enrolled, False if already."""
    existing = ClassStudent.query.filter_by(
        class_id=klass.id, student_id=student.id
    ).first()
    if existing:
        return False
    db.session.add(ClassStudent(class_id=klass.id, student_id=student.id))
    db.session.commit()
    return True


def class_ids_for_student(student):
    return [e.class_id for e in student.enrollments]


def class_ids_for_teacher(teacher):
    return [c.id for c in teacher.classes_taught]


# --------------------------------------------------------------------------- #
# Assignments / resources scoped by role
# --------------------------------------------------------------------------- #
def assignments_for_user(user):
    """Assignments the user is allowed to see (as ORM objects).

    Teacher: assignments in classes they own.
    Student: assignments in classes they're enrolled in.
    """
    if user.is_teacher:
        ids = class_ids_for_teacher(user)
    else:
        ids = class_ids_for_student(user)
    if not ids:
        return []
    return (
        Assignment.query.filter(Assignment.class_id.in_(ids))
        .order_by(Assignment.created_at.desc())
        .all()
    )


def get_assignment_for_teacher(assignment_id, teacher):
    """Fetch an assignment only if it belongs to a class this teacher owns."""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return None
    if assignment.klass.teacher_id != teacher.id:
        return None
    return assignment


def resources_for_user(user):
    if user.is_teacher:
        ids = class_ids_for_teacher(user)
    else:
        ids = class_ids_for_student(user)
    if not ids:
        return []
    return (
        Resource.query.filter(Resource.class_id.in_(ids))
        .order_by(Resource.uploaded_at.desc())
        .all()
    )


# --------------------------------------------------------------------------- #
# Chat sessions
# --------------------------------------------------------------------------- #
def create_chat_session(student, assignment_id=None):
    cs = ChatSession(student_id=student.id, assignment_id=assignment_id)
    db.session.add(cs)
    db.session.commit()
    return cs


def add_message(session_obj, role, content):
    msg = ChatMessage(session_id=session_obj.id, role=role, content=content)
    db.session.add(msg)
    db.session.commit()
    return msg


def chat_sessions_visible_to(user):
    """Chat sessions the user may view.

    Teacher: sessions of students enrolled in any class they teach.
    Student: only their own sessions.
    """
    if user.is_teacher:
        class_ids = class_ids_for_teacher(user)
        if not class_ids:
            return []
        student_ids = [
            link.student_id
            for link in ClassStudent.query.filter(
                ClassStudent.class_id.in_(class_ids)
            ).all()
        ]
        if not student_ids:
            return []
        return (
            ChatSession.query.filter(ChatSession.student_id.in_(set(student_ids)))
            .order_by(ChatSession.created_at.desc())
            .all()
        )
    return (
        ChatSession.query.filter_by(student_id=user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )


# --------------------------------------------------------------------------- #
# Feedback (student ratings on AI help — powers the RLHF-lite loop)
# --------------------------------------------------------------------------- #
def get_feedback_for_session(chat_session):
    """Return the (single) feedback row for a session, or None."""
    return Feedback.query.filter_by(chat_session_id=chat_session.id).first()


def save_feedback(chat_session, rating, comment=None):
    """Create or update the student's feedback for a chat session.

    One feedback row per session: submitting again updates the existing row
    rather than piling up duplicates.
    """
    comment = (comment or "").strip() or None
    entry = get_feedback_for_session(chat_session)
    if entry is None:
        entry = Feedback(chat_session_id=chat_session.id)
        db.session.add(entry)
    entry.rating = rating
    entry.comment = comment
    db.session.commit()
    return entry
