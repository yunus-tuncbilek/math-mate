from flask import Flask, render_template, request, redirect, session, url_for
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from respond import get_ai_response

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
    if request.method == "POST":
        if session["role"] == "teacher" and "homework" in request.form:
            hw = request.form["homework"]
            homeworks.append(hw)
            save_json(HOMEWORKS_FILE, homeworks)
        if "question" in request.form:
            question = request.form["question"]
            # Start chat with initial question
            session["messages"] = [{"role": "user", "text": question},
                                   {"role": "ai", "text": get_ai_response(question, "")}]
            return redirect(url_for("chat"))
    return render_template(
        "index.html",
        homeworks=homeworks,
        ai_response=ai_response,
        interactions=interactions,
        username=session["username"],
        role=session["role"]
    )

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "messages" not in session:
        session["messages"] = []
    if request.method == "POST":
        user_message = request.form["message"]
        session["messages"].append({"role": "user", "text": user_message})
        ai_reply = get_ai_response(user_message, session["messages"][:-1])
        session["messages"].append({"role": "ai", "text": ai_reply})
    return render_template("chat.html", messages=session["messages"])

if __name__ == "__main__":
    app.run(debug=True)