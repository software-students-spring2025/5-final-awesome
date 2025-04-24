from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
# Connection string mongodb://localhost:27017/
client = MongoClient("mongodb://mongodb:27017/")
database = client["awesome"]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        print(f"From sign_up frontend: {username}, {password}")
    return render_template("signup.html")


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        print(f"From log_in frontend: {username}, {password}")
    return render_template("login.html")


@app.route("/create", methods=["GET", "POST"])
def create_poll():
    if request.method == "POST":
        question = request.form.get("question")
        options = request.form.getlist("options")

        # Basic validation
        if not question or not options or len(options) < 1 or len(options) > 4:
            return "Please enter a question and between 1 to 4 options.", 400

        while True:
            poll_id = str(random.randint(100000, 999999))
            if not database["polls"].find_one({"_id": poll_id}):
                break

        poll = {
            "_id": poll_id,
            "question": question,
            "options": [{"text": opt, "votes": 0} for opt in options],
            "created_at": datetime.utcnow(),
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


@app.route("/created/<poll_id>/edit", methods=["GET", "POST"])
def edit_poll(poll_id):
    poll = database["polls"].find_one({"_id": poll_id})
    if not poll:
        return "Poll not found", 404

    if request.method == "POST":
        question = request.form.get("question")
        options = request.form.getlist("options")

        if not question or not options or len(options) < 1 or len(options) > 4:
            return "Please enter a valid question and 1-4 options", 400

        database["polls"].update_one(
            {"_id": poll_id},
            {
                "$set": {
                    "question": question,
                    "options": [{"text": opt, "votes": 0} for opt in options],
                }
            },
        )
        return redirect(url_for("poll_created", poll_id=poll_id))

    return render_template("edit.html", poll=poll)


@app.route("/poll/<poll_id>", methods=["GET", "POST"])
def view_poll(poll_id):
    poll = database["polls"].find_one({"_id": poll_id})
    if not poll:
        return "Poll not found", 404

    if request.method == "POST":
        try:
            option_index = int(request.form.get("option"))
            if 0 <= option_index < len(poll["options"]):
                database["polls"].update_one(
                    {"_id": poll_id},
                    {"$inc": {f"options.{option_index}.votes": 1}},
                )
        except (ValueError, TypeError):
            return "Invalid vote", 400

        return redirect(url_for("poll_results", poll_id=poll_id))

    return render_template("poll.html", poll=poll)


@app.route("/poll/<poll_id>/results", methods=["GET"])
def poll_results(poll_id):
    poll = database["polls"].find_one({"_id": poll_id})
    if not poll:
        return "Poll not found", 404
    return render_template("results.html", poll=poll)


@app.route("/database_test", methods=["GET"])
def database_test():
    """Access this url to add an arbitsrary entry to the database"""
    user = {
        "username": "sb",
        "password": generate_password_hash("sb"),
    }
    database["users"].insert_one(user)
    return "sb inserted", 200

@app.route("/avatar", methods=["GET"])
def avatar():
    return render_template("avatar.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
