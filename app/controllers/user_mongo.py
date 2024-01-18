import uuid
import database
from secure.hash import hash_str


def create_user(name, password, confirm):
    if get_user(name=name):
        raise Exception(f"User {name} already exists.")

    if len(name) < 3 or len(name) > 12:
        raise Exception("Name must be between 3 and 12 characters long.")

    if len(password) < 8:
        raise Exception("Password must be at least 8 characters long.")

    if " " in password:
        raise Exception("Password must not contain spaces.")

    if any(i in name for i in [" ", "'", "+", ",", "<", ">", ".", "/", "\\", "\""]):
        raise Exception("Name contains invalid symbols.")

    if password != confirm:
        raise Exception("Passwords do not match.")

    try:
        new_id = uuid.uuid4()
        database.db["User"].insert_one({
            "id": str(new_id),
            "name": name,
            "password": hash_str(password)
        })
    except Exception as e:
        raise e

    return new_id


def get_user(**kwargs):
    try:
        if kwargs.get("id"):
            user = database.db["User"].find_one({"id": str(kwargs["id"])})
        elif kwargs.get("name"):
            user = database.db["User"].find_one({"name": str(kwargs["name"])})
    except Exception as e:
        raise e
    
    if not user:
        return False

    return database.models.User(user["id"], user["name"], user["password"])


def delete_user(id):
    return database.db["User"].delete_one({"id": id}).acknowledged


def update_user_password(id, new, confirm):
    if len(new) < 8:
        raise Exception("Password must be at least 8 characters long.")

    if " " in new:
        raise Exception("Invalid username or password.")

    if new != confirm:
        raise Exception("Passwords do not match.")

    database.db["User"].update_one({
        "id": id
    }, {
        "$set": {
            "password": hash_str(new)
        }
    }).acknowledged
