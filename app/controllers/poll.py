import uuid
import database
from errors import UserError, InternalError

class PollController:

    def __init__(self, connection, user_controller) -> None:
        self.connection = connection.db
        self.user_controller = user_controller


class PollControllerMongo(PollController):


    def __init__(self, connection, user_controller) -> None:
        super().__init__(connection, user_controller)

    def create_poll(self, author, options, title, description):
        if not self.user_controller.get_user(id=author):
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
            self.connection.db["Poll"].insert_one({
                "id": str(new_id),
                "title": title,
                "description": description,
                "author": str(author),
                "options": insert_options
            })
        except Exception as e:
            raise e

        return new_id

    def get_poll(self, **kwargs):
        try:
            poll = self.connection.db["Poll"].find_one({"id": str(kwargs["id"])})
        except Exception as e:
            raise e
        
        if not poll:
            return False

        options = []

        for option in poll["options"]:
            options.append(database.models.Option(option["id"], option["text"], option["votes"]))

        return database.models.Poll(poll["id"], poll["title"], poll["description"], poll["author"], options)


    def get_polls(self, **kwargs):
        if kwargs.get("author"):
            polls = self.connection.db["Poll"].find({"author": str(kwargs["author"])})

        polls_list = []

        for poll in polls:
            options = []

            for option in poll["options"]:
                options.append(database.models.Option(option["id"], option["text"], option["votes"]))

            polls_list.append(database.models.Poll(poll["id"], poll["title"], poll["description"], poll["author"], options))

        return polls_list
    
    def get_all(self):
        polls = self.connection.db["Poll"].find()

        polls_list = []

        for poll in polls:
            options = []

            for option in poll["options"]:
                options.append(database.models.Option(option["id"], option["text"], option["votes"]))

            polls_list.append(database.models.Poll(poll["id"], poll["title"], poll["description"], poll["author"], options))

        return polls_list

    def increment_option(self, id):
        try:
            self.connection.db["Poll"].update_one({
                "options.id": str(id)
            }, {
                "$inc": {
                    "options.$.votes": 1
                }
            })
            return True
        except Exception as e:
            return False

    def delete_poll(self, id):
        if not isinstance(id, uuid.UUID) and isinstance(id, str):
            id = uuid.UUID(id)

        polls = self.connection.db["Poll"].delete_one({"id": str(id)})
        return polls.acknowledged

class PollControllerMongoReferenced(PollControllerMongo):

    def __init__(self, connection, user_controller) -> None:
        super().__init__(connection, user_controller)

    def create_poll(self, author, options, title, description):
        if not self.user_controller.get_user(id=author):
            raise UserError("Author must be a valid user.")
        
        if len(title) > 16 or len(title) < 3:
            raise UserError("Title must be between 3 and 16 characters long.")

        if len(description) > 120:
            raise UserError("Description must not exceed the 120 characters limit.")

        if len(options) > 31 or len(options) < 2:
            raise UserError("Must not provide more than 31 options.")
            
        try:
            new_id = uuid.uuid4()

            poll_data = {
                "id": str(new_id),
                "title": title,
                "description": description,
                "author": str(author)
            }

            self.connection.db["Poll"].insert_one(poll_data)

            option_documents = []

            for option in options:
                option_data = {
                    "id": str(uuid.uuid4()),
                    "text": option,
                    "votes": 0,
                    "poll_id": str(new_id)
                }
                option_documents.append(option_data)

            self.connection.db["PollOption"].insert_many(option_documents)

            return new_id

        except Exception as e:
            raise e

    def get_poll(self, **kwargs):
        poll_id = kwargs.get("id")
        poll = self.connection.db["Poll"].find_one({"id": str(poll_id)})

        if not poll:
            return None

        options = self.connection.db["PollOption"].find({"poll_id": str(poll_id)})

        poll_options = []

        for option in options:
            poll_options.append(database.models.Option(option["id"], option["text"], option["votes"]))

        return database.models.Poll(poll["id"], poll["title"], poll["description"], poll["author"], poll_options)

    def get_polls(self, **kwargs):
        if kwargs.get("author"):
            polls = self.connection.db["Poll"].find({"author": str(kwargs["author"])})

        polls_list = []

        for poll in polls:
            options = []

            poll_options = self.connection.db["PollOption"].find({"poll_id": str(poll["id"])})

            for option in poll_options:
                options.append(database.models.Option(option["id"], option["text"], option["votes"]))

            polls_list.append(database.models.Poll(poll["id"], poll["title"], poll["description"], poll["author"], options))

        return polls_list

    def get_all(self):
            polls = self.connection.db["Poll"].find()

            polls_list = []

            for poll in polls:
                options = []

                poll_options = self.connection.db["PollOption"].find({"poll_id": str(poll["id"])})

                for option in poll_options:
                    options.append(option["id"])

                polls_list.append(database.models.Poll(poll["id"], poll["title"], poll["description"], poll["author"], options))

            return polls_list
    
    def increment_option(self, id):
        try:
            self.connection.db["PollOption"].update_one({
                "id": str(id)
            }, {
                "$inc": {
                    "votes": 1
                }
            })
            return True
        except Exception as e:
            return False

    def delete_poll(self, id):
        if not isinstance(id, uuid.UUID) and isinstance(id, str):
            id = uuid.UUID(id)

        poll = self.connection.db["Poll"].find_one({"id": str(id)})

        if not poll:
            return False

        self.connection.db["Poll"].delete_one({"id": str(id)})
        self.connection.db["PollOption"].delete_many({"poll_id": str(id)})

        return True


class PollControllerSql(PollController):

    def __init__(self, connection, user_controller) -> None:
        super().__init__(connection, user_controller)

    def create_poll(self, author, options, title, description):
        if not self.user_controller.get_user(id=author):
            raise UserError("Author must be a valid user.")
        
        if len(title) > 16 or len(title) < 3:
            raise UserError("Title must be between 3 and 16 characters long.")

        if len(description) > 120:
            raise UserError("Description must not exceed the 120 characters limit.")

        if len(options) > 31 or len(options) < 2:
            raise UserError("Must not provide more than 31 options.")
            
        cur = self.connection.cursor()

        insert_options = []

        for option in options:
            if not bool(option.strip()):
                raise UserError("Options contain invalid symbols.")

            insert_options.append({"id": str(uuid.uuid4()), "text": option, "votes": 0})

        try:
            new_id = uuid.uuid4()
            
            cur.execute("""
                INSERT INTO polls (id, title, description, author)
                VALUES (%s, %s, %s, %s)
            """, (str(new_id), title, description, str(author)))

            for option in insert_options:
                cur.execute("""
                    INSERT INTO poll_options (id, poll_id, option_text, votes)
                    VALUES (%s, %s, %s, %s)
                """, (str(option["id"]), str(new_id), option["text"], option["votes"]))

            self.connection.commit()
        except Exception as e:
            raise InternalError(e)
        finally:
            cur.close()

        return new_id

    def get_poll(self, **kwargs):
        cur = self.connection.cursor()

        try:
            cur.execute("""
                SELECT * FROM polls WHERE id = %s
            """, (str(kwargs["id"]),))
            poll_data = cur.fetchone()

            if not poll_data:
                return False

            cur.execute("""
                SELECT id, option_text, votes FROM poll_options WHERE poll_id = %s
            """, (str(kwargs["id"]),))
            options_data = cur.fetchall()

            options = [database.models.Option(option[0], option[1], option[2]) for option in options_data]

        except Exception as e:
            raise InternalError(e)
        finally:
            cur.close()

        return database.models.Poll(poll_data[0], poll_data[1], poll_data[2], poll_data[3], options)

    def get_polls(self, **kwargs):
        cur = self.connection.cursor()

        try:
            if kwargs.get("author"):
                cur.execute("""
                    SELECT * FROM polls WHERE author = %s
                """, (str(kwargs["author"]),))
            else:
                cur.execute("""
                    SELECT * FROM polls
                """)

            polls_data = cur.fetchall()

            polls_list = []

            for poll_data in polls_data:
                cur.execute("""
                    SELECT * FROM poll_options WHERE poll_id = %s
                """, (str(poll_data[0]),))
                options_data = cur.fetchall()

                options = [database.models.Option(option[1], option[2], option[3]) for option in options_data]

                polls_list.append(database.models.Poll(poll_data[0], poll_data[1], poll_data[2], poll_data[3], options))

        except Exception as e:
            raise InternalError(e)
        finally:
            cur.close()

        return polls_list
    
    def get_all(self):
        cur = self.connection.cursor()

        try:
            cur.execute("""
                SELECT * FROM polls
            """)

            polls_data = cur.fetchall()

            polls_list = []

            for poll_data in polls_data:
                cur.execute("""
                    SELECT * FROM poll_options WHERE poll_id = %s
                """, (str(poll_data[0]),))
                options_data = cur.fetchall()

                options = [database.models.Option(option[1], option[2], option[3]) for option in options_data]

                polls_list.append(database.models.Poll(poll_data[0], poll_data[1], poll_data[2], poll_data[3], options))

        except Exception as e:
            raise InternalError(e)
        finally:
            cur.close()

        return polls_list

    def increment_option(self, id):
        cur = self.connection.cursor()

        try:
            cur.execute("""
                UPDATE poll_options SET votes = votes + 1 WHERE id = %s
            """, (str(id),))

            self.connection.commit()
        except Exception as e:
            raise InternalError(e)
        finally:
            cur.close()

        return True

    def delete_poll(self, id):
        cur = self.connection.cursor()

        try:
            cur.execute("""
                DELETE FROM poll_options WHERE poll_id = %s
            """, (str(id),))

            cur.execute("""
                DELETE FROM polls WHERE id = %s
            """, (str(id),))

            self.connection.commit()
        except Exception as e:
            raise InternalError(e)
        finally:
            cur.close()

        return True
