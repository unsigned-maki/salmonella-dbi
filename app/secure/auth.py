import os
import jwt
from .hash import hash_str
from database.models.user import User

JWT_SECRET = os.getenv("JWT_SECRET")

class Auth:

    def __init__(self, user, logger):
        self.user = user
        self.logger = logger

    def authenticate_user(self, name, password, tmp):
        if usr := self.user.get_user(name=name):
            if str(hash_str(password)) == str(usr.password):
                return jwt.encode({"user": str(usr.id)}, JWT_SECRET, algorithm="HS256")
            else:
                return False
        else:
            return False

    def is_authenticated(self, session):
        try:
            decoded = jwt.decode(session.get("token", ""), JWT_SECRET, algorithms="HS256")
            return isinstance(self.user.get_user(id=decoded["user"]), User)
        except:
            return False

    def get_user(self, session):
        if self.is_authenticated(session):
            return self.user.get_user(id=jwt.decode(session.get("token", ""), JWT_SECRET, algorithms="HS256")["user"])
