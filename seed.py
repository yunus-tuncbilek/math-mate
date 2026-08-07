"""Seed the database from the legacy ``sample_data/*.json`` files.

Idempotent: running it again after the DB is already populated is a no-op.
Run standalone (`python seed.py`) or via Flask (`flask seed`). The Dockerfile
runs migrations first, then this, so a fresh container has realistic data.

Mapping from the old JSON shape to the new schema:
  users.json         -> User        (login username becomes ``name``; email kept)
  homeworks.json     -> Class + Assignment (one Class per distinct teacher+name)
  interactions.json  -> ChatSession + ChatMessage ("ai" role -> "assistant")
  rag/data/lectures  -> Resource    (a sample lecture-notes resource per class)
"""
from datetime import datetime

from app import app  # noqa: E402  (import creates the Flask app + config)
from app_utils import load_json, generate_invite_code
from extensions import db
from models import (
    User,
    Class,
    ClassStudent,
    Assignment,
    Resource,
    ChatSession,
    ChatMessage,
)

SAMPLE_DIR = "sample_data"

# A private teacher guidance note attached to seeded assignments so the
# guidance_note pathway has realistic data to exercise. NEVER shown to students.
SAMPLE_GUIDANCE = (
    "Do not reveal final answers. Nudge with hints and leading questions, and "
    "stay encouraging even if the student is struggling."
)


def _parse_dt(value, fallback=None):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    return fallback or datetime.utcnow()


def seed():
    if User.query.first():
        print("Database already seeded — skipping.")
        return

    users_json = load_json(SAMPLE_DIR, "users.json", {})
    homeworks_json = load_json(SAMPLE_DIR, "homeworks.json", [])
    interactions_json = load_json(SAMPLE_DIR, "interactions.json", [])

    # ---- Users ----
    # The old JSON keyed users by username; email is kept, username -> name.
    users_by_username = {}
    for username, info in users_json.items():
        user = User(
            email=(info.get("email") or f"{username}@example.com").strip().lower(),
            name=username,
            password_hash=info["password"],  # already a valid werkzeug scrypt hash
            role=info.get("role", "student"),
        )
        db.session.add(user)
        users_by_username[username] = user
    db.session.flush()  # assign ids

    # ---- Classes ----
    # Old homeworks reference a teacher + free-text class name. Create one Class
    # per distinct (teacher, class name) pair, owned by that teacher.
    classes_by_key = {}
    for hw in homeworks_json:
        teacher = users_by_username.get(hw.get("teacher"))
        if not teacher:
            continue
        key = (teacher.id, hw.get("class", "Untitled Class"))
        if key not in classes_by_key:
            klass = Class(
                teacher_id=teacher.id,
                name=hw.get("class", "Untitled Class"),
                invite_code=generate_invite_code(),
            )
            db.session.add(klass)
            classes_by_key[key] = klass
    db.session.flush()

    # ---- Enroll students ----
    # The interactions come from students working on the primary class, so enroll
    # every seeded student into every seeded class for a realistic dev dataset.
    student_users = [u for u in users_by_username.values() if u.role == "student"]
    for klass in classes_by_key.values():
        for student in student_users:
            db.session.add(ClassStudent(class_id=klass.id, student_id=student.id))
    db.session.flush()

    # ---- Assignments ----
    assignments_by_title = {}
    for hw in homeworks_json:
        teacher = users_by_username.get(hw.get("teacher"))
        if not teacher:
            continue
        klass = classes_by_key[(teacher.id, hw.get("class", "Untitled Class"))]
        assignment = Assignment(
            class_id=klass.id,
            title=hw.get("title", "Untitled"),
            description=hw.get("content", ""),
            guidance_note=SAMPLE_GUIDANCE,
            created_at=_parse_dt(hw.get("upload_time")),
        )
        db.session.add(assignment)
        assignments_by_title[assignment.title] = assignment
    db.session.flush()

    # ---- Resources (sample lecture notes per class) ----
    for klass in classes_by_key.values():
        db.session.add(
            Resource(
                class_id=klass.id,
                title="Lecture notes (sample)",
                file_path="rag/data/lectures.txt",
            )
        )

    # ---- Chat sessions + messages (from interactions.json) ----
    for it in interactions_json:
        student = users_by_username.get(it.get("student"))
        if not student:
            continue
        created = _parse_dt(it.get("date"))
        chat_session = ChatSession(student_id=student.id, created_at=created)
        db.session.add(chat_session)
        db.session.flush()
        for msg in it.get("messages", []):
            role = "assistant" if msg.get("role") == "ai" else "user"
            db.session.add(
                ChatMessage(
                    session_id=chat_session.id,
                    role=role,
                    content=msg.get("text", ""),
                    created_at=created,
                )
            )

    db.session.commit()
    print(
        f"Seeded: {len(users_by_username)} users, {len(classes_by_key)} classes, "
        f"{len(assignments_by_title)} assignments, "
        f"{len(interactions_json)} chat sessions."
    )


@app.cli.command("seed")
def seed_command():
    """`flask seed` — populate the DB from sample_data/."""
    seed()


if __name__ == "__main__":
    with app.app_context():
        seed()
