from flask import Flask, render_template
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
# Connection string mongodb://localhost:27017/
client = MongoClient("mongodb://mongodb:27017/")
database = client["awesome"]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


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
