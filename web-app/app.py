from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from user import User

from datetime import datetime
import random
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
# Connection string mongodb://localhost:27017/
client = MongoClient("mongodb://mongodb:27017/")
database = client["awesome"]

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    user_data = database["users"].find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data["_id"], user_data["username"], user_data["password"])
    return None


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", user=current_user)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = database["users"].find_one({"username": username})
        if user:
            flash("Username already exists", "warning")
            return redirect(url_for("signup"))
        user = {
            "username": username,
            "password": generate_password_hash(password),
            "avatar": "https://api.dicebear.com/9.x/bottts-neutral/svg?size=200&radius=10&eyes=eva&mouth=grill02&backgroundColor=1e88e5",
        }
        user = database["users"].insert_one(user)
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    user_data = database["users"].find_one({"username": username})

    if not user_data:
        flash("Username not found", "danger")
        return redirect(url_for("login"))

    if not check_password_hash(user_data["password"], password):
        flash("Incorrect password", "danger")
        return redirect(url_for("login"))

    login_user(User(user_data["_id"], user_data["username"], user_data["password"]))

    return redirect(url_for("index"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    query = request.args.get("q", "").strip().lower()
    cursor = database["polls"].find({"owner": ObjectId(current_user.id)})
    polls = list(cursor)

    if query:
        polls = [
            poll
            for poll in polls
            if query in poll["question"].lower()
            or any(query in opt["text"].lower() for opt in poll["options"])
        ]

    user_data = database["users"].find_one({"username": current_user.username})

    return render_template(
        "profile.html",
        user=current_user,
        polls=polls,
        query=query,
        avatar_url=user_data["avatar"],
    )


@app.route("/delete_poll/<poll_id>", methods=["GET"])
@login_required
def delete_poll(poll_id):
    poll = database["polls"].find_one({"_id": str(poll_id)})
    if poll and poll["owner"] == current_user.id:
        database["polls"].delete_one({"_id": str(poll_id)})
    return redirect(url_for("profile"))


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/create", methods=["GET", "POST"])
def create_poll():
    if request.method == "POST":
        question = request.form.get("question")
        options = request.form.getlist("options")

        while True:
            poll_id = str(random.randint(100000, 999999))
            if not database["polls"].find_one({"_id": poll_id}):
                break

        owner = 0
        if current_user.is_authenticated:
            owner = current_user.id

        poll = {
            "_id": poll_id,
            "owner": owner,
            "question": question,
            "options": [{"text": opt, "votes": 0} for opt in options],
            "created_at": datetime.now(),
        }

        database["polls"].insert_one(poll)
        return redirect(url_for("poll_created", poll_id=poll_id))

    return render_template("create.html")


@app.route("/created/<poll_id>", methods=["GET"])
def poll_created(poll_id):
    poll = database["polls"].find_one({"_id": poll_id})
    if not poll:
        return "Poll not found", 404
    return render_template("created.html", poll=poll)


@app.route("/poll/<poll_id>", methods=["GET", "POST"])
def view_poll(poll_id):
    poll = database["polls"].find_one({"_id": poll_id})
    if not poll:
        flash(
            "Poll not found. The poll may have been deleted or the ID is incorrect.",
            "danger",
        )
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            option_index = int(request.form.get("option"))
            if 0 <= option_index < len(poll["options"]):
                database["polls"].update_one(
                    {"_id": poll_id},
                    {"$inc": {f"options.{option_index}.votes": 1}},
                )
            else:
                flash("Invalid vote option selected.", "danger")
                return redirect(url_for("view_poll", poll_id=poll_id))
        except (ValueError, TypeError):
            flash("Invalid vote format.", "danger")
            return redirect(url_for("view_poll", poll_id=poll_id))

        return redirect(url_for("poll_results", poll_id=poll_id))

    return render_template("poll.html", poll=poll)


@app.route("/poll/<poll_id>/results", methods=["GET"])
def poll_results(poll_id):
    poll = database["polls"].find_one({"_id": poll_id})
    if not poll:
        return "Poll not found", 404
    return render_template("results.html", poll=poll)


@app.route("/avatar", methods=["POST"])
def avatar():
    avatar_url = request.form.get("avatar_url")
    username = request.form.get("username")
    try:
        database["users"].update_one(
            {"username": username}, {"$set": {"avatar": avatar_url}}
        )
        return redirect(url_for("profile"))
    except Exception as e:
        return redirect(url_for("index"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
