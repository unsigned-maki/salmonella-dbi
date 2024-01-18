import uuid
import database
from . import user_mongo

def create_poll(author, options, title, description):
    if not user_mongo.get_user(id=author):
        raise Exception("Author must be a valid user.")
    
    if len(title) > 16 or len(title) < 3:
        raise Exception("Title must be between 3 and 16 characters long.")

    if len(description) > 120:
        raise Exception("Description must not exceed the 120 characters limit.")

    if len(options) > 31 or len(options) < 2:
        raise Exception("Must not provide more than 31 options.")

    insert_options = []

    for option in options:
        if not bool(option.strip()):
            raise Exception("Options contain invalid symbols.")

        insert_options.append({"id": str(uuid.uuid4()), "text": option, "votes": 0})

    try:
        new_id = uuid.uuid4() 
        database.db["Poll"].insert_one({
            "id": str(new_id),
            "title": title,
            "description": description,
            "author": str(author),
            "options": insert_options
        })
    except Exception as e:
        raise e

    return new_id


def get_poll(**kwargs):
    try:
        poll = database.db["Poll"].find_one({"id": str(kwargs["id"])})
    except Exception as e:
        raise e
    
    if not poll:
        return False

    options = []

    for option in poll["options"]:
        options.append(database.models.Option(option["id"], option["text"], option["votes"]))

    return database.models.Poll(poll["id"], poll["title"], poll["description"], poll["author"], options)


def get_polls(**kwargs):
    if kwargs.get("author"):
        polls = database.db["Poll"].find({"author": str(kwargs["author"])})

    polls_list = []

    for poll in polls:
        options = []

        for option in poll["options"]:
            option.append(database.models.Option(option["id"], option["text"], option["votes"]))

        polls_list.append(database.models.Poll(poll["id"], poll["title"], poll["description"], poll["author"], options))

    return polls_list

def increment_option(id):
    try:
        database.db["Poll"].update_one({
            "options.id": str(id)
        }, {
            "$inc": {
                "options.$.votes": 1
            }
        })
        return True
    except Exception as e:
        return False


def delete_poll(id):
    if not isinstance(id, uuid.UUID) and isinstance(id, str):
        id = uuid.UUID(id)

    polls = database.db["Poll"].delete_one({"id": str(id)})

    if not polls.count():
        return False

    polls[0].delete()
    return True
