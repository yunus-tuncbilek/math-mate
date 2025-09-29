from flask import Flask, render_template, request, redirect, session, url_for
import json
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from respond import get_ai_response
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

USERS_FILE = "users.json"
HOMEWORKS_FILE = "homeworks.json"
INTERACTIONS_FILE = "interactions.json"

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

users = load_json(USERS_FILE, {})  # username: {password, role}
homeworks = load_json(HOMEWORKS_FILE, [])
interactions = load_json(INTERACTIONS_FILE, [])

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    user = users.get(username)
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
        email = request.form["email"]
        role = request.form["role"]
        if username in users:
            msg = "Username already exists."
        else:
            hashed_pw = generate_password_hash(password)
            users[username] = {"password": hashed_pw, "role": role, "email": email}
            save_json(USERS_FILE, users)
            msg = "Account created. Please log in."
            return redirect(url_for("login"))
    return render_template("signup.html", msg=msg)

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users.get(username)
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            session["role"] = user["role"]
            return redirect(url_for("index"))
        else:
            msg = "Invalid credentials."
    return render_template("login.html", msg=msg)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    ai_response = ""
    global homeworks, interactions
    homeworks = load_json(HOMEWORKS_FILE, [])
    interactions = load_json(INTERACTIONS_FILE, [])
    if request.method == "POST":
        if session["role"] == "teacher" and "delete_hw_index" in request.form:
            idx = int(request.form["delete_hw_index"])
            if 0 <= idx < len(homeworks):
                del homeworks[idx]
                save_json(HOMEWORKS_FILE, homeworks)
        if session["role"] == "teacher" and "homework" in request.form:
            hw_text = request.form["homework"]
            title = request.form.get("title", "")
            class_name = request.form.get("class_name", "")
            teacher_name = session["username"]
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
                "student": session.get("username"),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "messages": list(session["messages"])
            }
            interactions.append(interaction_entry)
            save_json(INTERACTIONS_FILE, interactions)
            return redirect(url_for("chat"))

    # Only show interactions to teachers or the same student
    visible_interactions = [
        i for i in interactions
        if session.get("role") == "teacher" or i.get("student") == session.get("username")
    ]

    return render_template(
        "index.html",
        homeworks=homeworks,
        ai_response=ai_response,
        interactions=visible_interactions,
        username=session["username"],
        role=session["role"]
    )

@app.route("/chat", methods=["GET", "POST"])
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
                    "student": session.get("username"),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "messages": list(session["messages"])
                })
        else:
            # no interaction_id -> create one and append
            interaction_id = str(uuid.uuid4())
            session["interaction_id"] = interaction_id
            interactions.append({
                "id": interaction_id,
                "student": session.get("username"),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "messages": list(session["messages"])
            })

        save_json(INTERACTIONS_FILE, interactions)

    return render_template("chat.html", messages=session["messages"])

if __name__ == "__main__":
    app.run(debug=True)