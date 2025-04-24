from flask_login import UserMixin


class User(UserMixin):
    """User class"""

    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
