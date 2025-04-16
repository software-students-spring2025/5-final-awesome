from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
# Connection string mongodb://localhost:27017/
client = MongoClient("mongodb://mongodb:27017/")
database = client["awesome"]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create_poll():
    if request.method == "POST":
        question = request.form.get("question")
        options = request.form.getlist("options")
        poll_id = request.form.get("poll_id")


         # Check for duplicate ID
        if database["polls"].find_one({"_id": poll_id}):
            # Re-render the form with an error message
            return render_template("create.html", error="Poll ID already exists. Please use a different one."), 400
        poll = {
            "_id": poll_id,
            "question": question,
            "options": [{"text": opt, "votes": 0} for opt in options],
            "created_at": datetime.utcnow(),
        }

        database["polls"].insert_one(poll)
        return redirect(url_for("view_poll", poll_id=poll_id))

    return render_template("create.html")


@app.route("/poll/<poll_id>", methods=["GET", "POST"])
def view_poll(poll_id):
    poll = database["polls"].find_one({"_id": poll_id})
    if not poll:
        return "Poll not found", 404

    if request.method == "POST":
        option_index = int(request.form.get("option"))
        if 0 <= option_index < len(poll["options"]):
            database["polls"].update_one(
                {
                    "_id": poll_id,
                    "options." + str(option_index) + ".votes": {"$exists": True},
                },
                {"$inc": {"options." + str(option_index) + ".votes": 1}},
            )
            return redirect(url_for("view_poll", poll_id=poll_id))

    return render_template("poll.html", poll=poll)


@app.route("/poll/<poll_id>/edit", methods=["GET", "POST"])
def edit_poll(poll_id):
    poll = database["polls"].find_one({"_id": poll_id})
    if not poll:
        return "Poll not found", 404

    if request.method == "POST":
        question = request.form.get("question")
        options = request.form.getlist("options")

        if not question or not options:
            return "Missing question or options", 400

        database["polls"].update_one(
            {"_id": poll_id},
            {
                "$set": {
                    "question": question,
                    "options": [{"text": opt, "votes": 0} for opt in options],
                }
            },
        )
        return redirect(url_for("view_poll", poll_id=poll_id))

    return render_template("edit.html", poll=poll)


@app.route("/database_test", methods=["GET"])
def database_test():
    """Access this url to add an arbitsrary entry to the database"""
    user = {
        "username": "sb",
        "password": generate_password_hash("sb"),
    }
    database["users"].insert_one(user)
    return "sb inserted", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
