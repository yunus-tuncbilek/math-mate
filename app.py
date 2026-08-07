import os
import time
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    abort,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import (
    login_user,
    login_required,
    logout_user,
    current_user,
)

from config import Config
from extensions import db, migrate, login_manager
from models import User, Class, Assignment, Resource, ChatSession, ChatMessage
import app_utils
from respond import get_ai_response, closest_chunk_from_rag

app = Flask(__name__)
app.config.from_object(Config)

if not app.config["SECRET_KEY"]:
    raise ValueError("secret_key environment variable not set")

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in app.config["ALLOWED_EXT"]


# --------------------------------------------------------------------------- #
# Role-based access control (enforced server-side on every protected route)
# --------------------------------------------------------------------------- #
def teacher_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_teacher:
            abort(403)
        return f(*args, **kwargs)

    return wrapper


def student_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_student:
            abort(403)
        return f(*args, **kwargs)

    return wrapper


def _serialize_session(chat_session):
    """Template-safe view of a chat session (never touches guidance_note)."""
    return {
        "id": chat_session.id,
        "student": chat_session.student.name if chat_session.student else "unknown",
        "date": chat_session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "messages": [
            {"role": m.role, "text": m.content} for m in chat_session.messages
        ],
    }


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        user = app_utils.get_user_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # Redirect based on role.
            if user.is_teacher:
                return redirect(url_for("index"))
            return redirect(url_for("index"))
        msg = "Invalid credentials."
    return render_template("login.html", msg=msg)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    msg = ""
    # Pre-fill invite code from a link like /signup?code=ABC123
    prefill_code = request.args.get("code", "")
    if request.method == "POST":
        role = request.form.get("role", "student")
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")

        if not email or not name or not password:
            msg = "Email, name and password are all required."
            return render_template("signup.html", msg=msg, prefill_code=prefill_code)

        if app_utils.get_user_by_email(email):
            msg = "An account with that email already exists."
            return render_template("signup.html", msg=msg, prefill_code=prefill_code)

        if role == "teacher":
            user = app_utils.create_user(email, name, password, "teacher")
            login_user(user)
            # Prompt the teacher to create their first class.
            return redirect(url_for("create_class"))

        # ---- Student path: requires a valid invite code up front ----
        code = request.form.get("invite_code", "").strip()
        klass = app_utils.get_class_by_invite_code(code)
        if not klass:
            msg = "That class invite code is invalid or expired. Please check with your teacher."
            return render_template("signup.html", msg=msg, prefill_code=code)

        user = app_utils.create_user(email, name, password, "student")
        app_utils.enroll_student(klass, user)
        login_user(user)
        return redirect(url_for("index"))

    return render_template("signup.html", msg=msg, prefill_code=prefill_code)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("chat_session_id", None)
    return redirect(url_for("login"))


# --------------------------------------------------------------------------- #
# Classes (teacher)
# --------------------------------------------------------------------------- #
@app.route("/classes/new", methods=["GET", "POST"])
@teacher_required
def create_class():
    created = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            created = app_utils.create_class(current_user, name)
            flash(f"Class '{created.name}' created. Invite code: {created.invite_code}")
    return render_template("create_class.html", created=created)


@app.route("/classes/<int:class_id>/join_student", methods=["POST"])
@teacher_required
def invite_existing_student(class_id):
    """Enroll an already-registered student (by email) into one of my classes.

    Supports the 'a single email may be invited to multiple classes' case.
    """
    klass = Class.query.get_or_404(class_id)
    if klass.teacher_id != current_user.id:
        abort(403)
    email = request.form.get("email", "")
    student = app_utils.get_user_by_email(email)
    if not student or not student.is_student:
        flash("No student account found for that email.")
    elif app_utils.enroll_student(klass, student):
        flash(f"{student.name} added to {klass.name}.")
    else:
        flash(f"{student.name} is already in {klass.name}.")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
# Landing page (role-aware)
# --------------------------------------------------------------------------- #
@app.route("/", methods=["GET"])
@login_required
def index():
    assignments = app_utils.assignments_for_user(current_user)
    resources = app_utils.resources_for_user(current_user)
    sessions = app_utils.chat_sessions_visible_to(current_user)

    if current_user.is_teacher:
        # Teacher payload MAY include the private guidance_note.
        assignment_data = [a.to_dict(include_guidance=True) for a in assignments]
        classes = current_user.classes_taught
    else:
        # Student payload NEVER includes guidance_note (stripped at the source).
        assignment_data = [a.public_dict() for a in assignments]
        classes = [e.klass for e in current_user.enrollments]

    return render_template(
        "index.html",
        role=current_user.role,
        username=current_user.name,
        classes=classes,
        assignments=assignment_data,
        resources=resources,
        interactions=[_serialize_session(s) for s in sessions],
    )


# --------------------------------------------------------------------------- #
# Assignments (teacher-only writes, with ownership checks)
# --------------------------------------------------------------------------- #
@app.route("/assignments/create", methods=["POST"])
@teacher_required
def create_assignment():
    class_id = request.form.get("class_id", type=int)
    klass = Class.query.get(class_id) if class_id else None
    # Ownership: the class must belong to the current teacher.
    if not klass or klass.teacher_id != current_user.id:
        abort(403)

    due_raw = request.form.get("due_date", "").strip()
    due_date = None
    if due_raw:
        try:
            due_date = datetime.strptime(due_raw, "%Y-%m-%d")
        except ValueError:
            due_date = None

    assignment = Assignment(
        class_id=klass.id,
        title=request.form.get("title", "").strip(),
        description=request.form.get("description", "").strip(),
        guidance_note=request.form.get("guidance_note", "").strip() or None,
        due_date=due_date,
    )
    db.session.add(assignment)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@teacher_required
def delete_assignment(assignment_id):
    assignment = app_utils.get_assignment_for_teacher(assignment_id, current_user)
    if not assignment:
        abort(403)
    db.session.delete(assignment)
    db.session.commit()
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
# Resources (lecture notes / PDFs) — teacher-only upload
# --------------------------------------------------------------------------- #
@app.route("/resources/upload", methods=["POST"])
@teacher_required
def upload_resource():
    class_id = request.form.get("class_id", type=int)
    klass = Class.query.get(class_id) if class_id else None
    if not klass or klass.teacher_id != current_user.id:
        abort(403)

    file = request.files.get("pdf")
    title = request.form.get("title", "").strip()
    if not file or file.filename == "" or not allowed_file(file.filename):
        flash("Please choose a PDF file.")
        return redirect(url_for("index"))

    filename = secure_filename(f"{int(time.time())}_{file.filename}")
    dest_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(dest_path)

    resource = Resource(
        class_id=klass.id,
        title=title or file.filename,
        file_path=os.path.join("uploads", filename),  # served from /static
    )
    db.session.add(resource)
    db.session.commit()
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
# AI chat (student)
# --------------------------------------------------------------------------- #
def _homework_context_for_student():
    """Public assignment text a student may use as AI context (no guidance)."""
    assignments = app_utils.assignments_for_user(current_user)
    return "\n".join(
        f"{a.title}: {a.description or ''}" for a in assignments
    )


@app.route("/ask", methods=["POST"])
@student_required
def ask():
    question = request.form.get("question", "").strip()
    if not question:
        return redirect(url_for("index"))

    assignment_id = request.form.get("assignment_id", type=int)
    guidance = ""
    if assignment_id:
        # Only honour an assignment the student is actually enrolled for.
        allowed_ids = {a.id for a in app_utils.assignments_for_user(current_user)}
        if assignment_id in allowed_ids:
            assignment = Assignment.query.get(assignment_id)
            guidance = assignment.guidance_note or ""  # private -> prompt only
        else:
            assignment_id = None

    closest_lecture = closest_chunk_from_rag(question)
    homework_ctx = _homework_context_for_student()
    ai_reply = get_ai_response(
        question, "", homework_ctx, lecture=closest_lecture, guidance=guidance
    )

    chat_session = app_utils.create_chat_session(current_user, assignment_id)
    app_utils.add_message(chat_session, "user", question)
    app_utils.add_message(chat_session, "assistant", ai_reply)
    session["chat_session_id"] = chat_session.id
    return redirect(url_for("chat"))


@app.route("/chat", methods=["GET", "POST"])
@student_required
def chat():
    chat_session_id = session.get("chat_session_id")
    chat_session = ChatSession.query.get(chat_session_id) if chat_session_id else None

    # A student may only ever access their own session.
    if chat_session and chat_session.student_id != current_user.id:
        abort(403)

    if request.method == "POST" and chat_session:
        user_message = request.form.get("message", "").strip()
        if user_message:
            history = "\n".join(
                f"{m.role}: {m.content}" for m in chat_session.messages
            )
            guidance = (
                chat_session.assignment.guidance_note
                if chat_session.assignment
                else ""
            ) or ""
            closest_lecture = closest_chunk_from_rag(user_message)
            ai_reply = get_ai_response(
                user_message,
                history,
                _homework_context_for_student(),
                lecture=closest_lecture,
                guidance=guidance,
            )
            app_utils.add_message(chat_session, "user", user_message)
            app_utils.add_message(chat_session, "assistant", ai_reply)

    messages = (
        [{"role": m.role, "text": m.content} for m in chat_session.messages]
        if chat_session
        else []
    )
    return render_template("chat.html", messages=messages)


# --------------------------------------------------------------------------- #
# Profile
# --------------------------------------------------------------------------- #
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    msg = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if email and email != current_user.email:
            if app_utils.get_user_by_email(email):
                msg = "That email is already in use."
            else:
                current_user.email = email
        if password:
            current_user.password_hash = generate_password_hash(password)
        if not msg:
            db.session.commit()
            msg = "Profile updated successfully."
    return render_template("profile.html", user=current_user, msg=msg)


if __name__ == "__main__":
    app.run(debug=True)
