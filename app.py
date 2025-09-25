from flask import Flask, render_template, request, redirect, session, url_for
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

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

@app.route("/signup", methods=["GET", "POST"])
def signup():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        if username in users:
            msg = "Username already exists."
        else:
            hashed_pw = generate_password_hash(password)
            users[username] = {"password": hashed_pw, "role": role}
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
            q = request.form["question"]
            # Simple AI assistant mockup
            ai_response = f"AI Assistant: Let's think about '{q}' together!"
            interactions.append({"question": q, "response": ai_response, "user": session["username"]})
            save_json(INTERACTIONS_FILE, interactions)
    return render_template(
        "index.html",
        homeworks=homeworks,
        ai_response=ai_response,
        interactions=interactions,
        username=session["username"],
        role=session["role"]
    )

if __name__ == "__main__":
    app.run(debug=True)