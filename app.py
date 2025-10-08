from flask import Flask, render_template, request, redirect, session, url_for
import json
import os
import uuid
import time
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from respond import get_ai_response
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from datetime import datetime

app = Flask(__name__)
secret_key = os.getenv("secret_key")
if not secret_key:
    raise ValueError("secret_key environment variable not set")
app.secret_key = secret_key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Simple User class backed by users.json
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        # Load latest users.json each time to avoid stale data across processes
        try:
            users = load_json(USERS_FILE, {})
        except Exception:
            raise ValueError("Failed to load users data")
            # fallback to in-memory dict if loader not available yet
        self.user = users.get(username, {})

        self.role = self.user.get("role")
        self.email = self.user.get("email")

    # Flask-Login uses get_id() from UserMixin which returns self.id


# user loader must be set after users is loaded (users is defined below)
# we'll set a loader function later after users variable is available
USERS_FILE = "users.json"
HOMEWORKS_FILE = "homeworks.json"
INTERACTIONS_FILE = "interactions.json"

# upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXT = {".pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return default
    return default

def save_json(filename, data):
    # atomic write to avoid corruption from concurrent processes
    tmp = filename + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, filename)

def allowed_file(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXT

users = load_json(USERS_FILE, {})  # username: {password, role}
homeworks = load_json(HOMEWORKS_FILE, [])
interactions = load_json(INTERACTIONS_FILE, [])

# register user loader now that users file exists
@login_manager.user_loader
def load_user(user_id):
    # reload users each time to avoid stale in-memory copy on multi-process hosts
    users_local = load_json(USERS_FILE, {})
    if user_id in users_local:
        # return fresh User instance that reads from the latest users file
        return User(user_id)
    return None

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    username = current_user.get_id()
    user = users.get(username, {})
    msg = ""
    if request.method == "POST":
        # Allow user to update email and password
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        if email:
            user["email"] = email
        if password:
            user["password"] = generate_password_hash(password)
        users[username] = user
        save_json(USERS_FILE, users)
        msg = "Profile updated successfully."
    return render_template("profile.html", user=user, username=username, msg=msg)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form.get("email", "")
        role = request.form.get("role", "student")
        if username in users:
            msg = "Username already exists."
        else:
            hashed_pw = generate_password_hash(password)
            users[username] = {"password": hashed_pw, "role": role, "email": email}
            save_json(USERS_FILE, users)
            msg = "Account created. Please log in."
            return redirect(url_for("login"))
    print(USERS_FILE, users)
    return render_template("signup.html", msg=msg)

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        # reload users to ensure latest credentials are checked
        users_local = load_json(USERS_FILE, {})
        username = request.form["username"]
        password = request.form["password"]
        
        user = users_local.get(username)

        if user and check_password_hash(user["password"], password):
            user_obj = User(username)
            login_user(user_obj)
            return redirect(url_for("index"))
        else:
            msg = "Invalid credentials."
    return render_template("login.html", msg=msg)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    # clear conversation state stored in session
    session.pop("messages", None)
    session.pop("interaction_id", None)
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    ai_response = ""
    global homeworks, interactions
    homeworks = load_json(HOMEWORKS_FILE, [])
    interactions = load_json(INTERACTIONS_FILE, [])
    if request.method == "POST":
        if current_user.role == "teacher" and "delete_hw_index" in request.form:
            idx = int(request.form["delete_hw_index"])
            if 0 <= idx < len(homeworks):
                del homeworks[idx]
                save_json(HOMEWORKS_FILE, homeworks)
        if current_user.role == "teacher" and "homework" in request.form:
            hw_text = request.form["homework"]
            title = request.form.get("title", "")
            class_name = request.form.get("class_name", "")
            # use current_user rather than session to get reliable username
            teacher_name = current_user.get_id()
            upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            homework_entry = {
                "teacher": teacher_name,
                "class": class_name,
                "upload_time": upload_time,
                "title": title,
                "content": hw_text
            }
            homeworks.append(homework_entry)
            save_json(HOMEWORKS_FILE, homeworks)
        if "question" in request.form:
            question = request.form["question"]
            homeworks = load_json(HOMEWORKS_FILE, [])
            # start a new conversation and create a single interaction entry
            session["messages"] = [
                {"role": "user", "text": question},
                {"role": "ai", "text": get_ai_response(question, "", homeworks)}
            ]
            # create a persistent interaction record and store its id in session
            interaction_id = str(uuid.uuid4())
            session["interaction_id"] = interaction_id
            interaction_entry = {
                "id": interaction_id,
                "student": current_user.get_id(),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "messages": list(session["messages"])
            }
            interactions.append(interaction_entry)
            save_json(INTERACTIONS_FILE, interactions)
            return redirect(url_for("chat"))

    # Only show interactions to teachers or the same student
    visible_interactions = [
        i for i in interactions
        if current_user.role == "teacher" or i.get("student") == current_user.get_id()
    ]

    users = load_json(USERS_FILE, {})

    return render_template(
        "index.html",
        homeworks=homeworks,
        ai_response=ai_response,
        interactions=visible_interactions,
        username=current_user.get_id(),
        role=current_user.role,
        users=users
    )

@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    global homeworks, interactions
    homeworks = load_json(HOMEWORKS_FILE, [])
    interactions = load_json(INTERACTIONS_FILE, [])
    if "messages" not in session:
        session["messages"] = []
    if request.method == "POST":
        user_message = request.form["message"]
        session["messages"].append({"role": "user", "text": user_message})
        history = session["messages"][:-1]
        ai_reply = get_ai_response(user_message, history, homeworks)
        session["messages"].append({"role": "ai", "text": ai_reply})
        session.modified = True

        # Update the single interaction entry for this chat instead of appending a new one
        interaction_id = session.get("interaction_id")
        if interaction_id:
            # find and update existing interaction
            for it in interactions:
                if it.get("id") == interaction_id:
                    it["messages"] = list(session["messages"])
                    it["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            else:
                # fallback: create new interaction if not found
                interactions.append({
                    "id": interaction_id,
                    "student": current_user.get_id(),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "messages": list(session["messages"])
                })
        else:
            # no interaction_id -> create one and append
            interaction_id = str(uuid.uuid4())
            session["interaction_id"] = interaction_id
            interactions.append({
                "id": interaction_id,
                "student": current_user.get_id(),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "messages": list(session["messages"])
            })

        save_json(INTERACTIONS_FILE, interactions)

    return render_template("chat.html", messages=session["messages"])

@app.route("/upload_homework", methods=["POST"])
@login_required
def upload_homework():
    # only teachers may upload
    if getattr(current_user, "role", None) != "teacher":
        return "Forbidden", 403

    file = request.files.get("pdf")
    title = request.form.get("title", "").strip()
    class_name = request.form.get("class_name", "").strip()

    if not file or file.filename == "" or not allowed_file(file.filename):
        return redirect(url_for("index"))

    filename = secure_filename(f"{int(time.time())}_{file.filename}")
    dest_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(dest_path)

    # append metadata to homeworks.json
    homeworks = load_json(HOMEWORKS_FILE, [])
    hw_entry = {
        "teacher": current_user.get_id(),
        "class": class_name,
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "file": os.path.join("uploads", filename)
    }
    homeworks.append(hw_entry)
    save_json(HOMEWORKS_FILE, homeworks)

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)