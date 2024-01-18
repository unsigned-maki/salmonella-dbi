import uuid
import database
from secure.hash import hash_str
from errors import UserError, InternalError

class UserController:

    def __init__(self, connection) -> None:
        self.connection = connection.db


class UserControllerMongo(UserController):


    def __init__(self, connection) -> None:
        super().__init__(connection)

    def create_user(self, name, password, confirm):
        if self.get_user(name=name):
            raise UserError(f"User {name} already exists.")

        if len(name) < 3 or len(name) > 20:
            raise UserError("Name must be between 3 and 20 characters long.")

        if len(password) < 8:
            raise UserError("Password must be at least 8 characters long.")

        if " " in password:
            raise UserError("Password must not contain spaces.")

        if any(i in name for i in [" ", "'", "+", ",", "<", ">", ".", "/", "\\", "\""]):
            raise UserError("Name contains invalid symbols.")

        if password != confirm:
            raise UserError("Passwords do not match.")

        try:
            new_id = uuid.uuid4()
            self.connection["User"].insert_one({
                "id": str(new_id),
                "name": name,
                "password": hash_str(password)
            })
        except Exception as e:
            raise e

        return new_id

    def get_user(self, **kwargs):
        user = None

        try:
            if kwargs.get("id"):
                user = self.connection["User"].find_one({"id": str(kwargs["id"])})
            elif kwargs.get("name"):
                user = self.connection["User"].find_one({"name": str(kwargs["name"])})
            elif kwargs.get("password"):
                user = self.connection["User"].find_one({"password": str(kwargs["password"])})
        except Exception as e:
            raise e
        
        if not user:
            return False

        return database.models.User(user["id"], user["name"], user["password"])

    def get_user_password(self, user_id):
        found = self.connection["User"].find_one({"id": str(user_id)}, {"password": 1, "_id": 0})
        
        if found:
            return found["password"]
        else:
            return None

    def search_users(self, string):
        result = self.connection["User"].find({"name": {"$regex": string}}, {"name": 1, "_id": 0}).sort({"name": 1})
        return list(result)
        
    def delete_user(self, id):
        return self.connection["User"].delete_one({"id": str(id)}).acknowledged

    def update_user_password(self, id, new, confirm):
        if len(new) < 8:
            raise UserError("Password must be at least 8 characters long.")

        if " " in new:
            raise UserError("Invalid username or password.")

        if new != confirm:
            raise UserError("Passwords do not match.")

        return self.connection["User"].update_one({
            "id": str(id)
        }, {
            "$set": {
                "password": hash_str(new)
            }
        }).acknowledged


class UserControllerMongoAggregate(UserControllerMongo):

    def __init__(self, connection):
        super().__init__(connection)

    def search_users(self, string):
        result = self.connection["User"].aggregate([
            {
                "$match": {
                    "name": {
                        "$regex": string
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "name": 1
                }
            },
            {
                "$sort": {
                    "name": 1
                }
            }
        ])
        return list(result)


class UserControllerSql(UserController):

    def __init__(self, connection):
        super().__init__(connection)

    def create_user(self, name, password, confirm):
        if self.get_user(name=name):
            raise UserError(f"User {name} already exists.")

        if len(name) < 3 or len(name) > 20:
            raise UserError("Name must be between 3 and 20 characters long.")

        if len(password) < 8:
            raise UserError("Password must be at least 8 characters long.")

        if " " in password:
            raise UserError("Password must not contain spaces.")

        invalid_symbols = [" ", "'", "+", ",", "<", ">", ".", "/", "\\", "\""]
        if any(i in name for i in invalid_symbols):
            raise UserError("Name contains invalid symbols.")

        cur = self.connection.cursor()

        try:
            new_id = uuid.uuid4()
            hashed_password = str(hash_str(password))

            cur.execute("""
                INSERT INTO users (id, name, password)
                VALUES (%s, %s, %s)
            """, (str(new_id), name, hashed_password))

            self.connection.commit()
        except Exception as e:
            raise InternalError(e)
        finally:
            cur.close()

        if self.get_user(id=new_id):
            return new_id
        else:
            ValueError("User was not created.")

    def get_user(self, **kwargs):
        cur = self.connection.cursor()

        user_data = None

        try:
            if kwargs.get("id"):
                cur.execute("""
                    SELECT * FROM users WHERE id = %s
                """, (str(kwargs["id"]),))
            elif kwargs.get("name"):
                cur.execute("""
                    SELECT * FROM users WHERE "name" = %s
                """, (str(kwargs["name"]),))
            elif kwargs.get("password"):
                cur.execute("""
                    SELECT * FROM users WHERE password = %s
                """, (str(kwargs["password"]),))

            user_data = cur.fetchone()

        except Exception as e:
            raise e
        finally:
            cur.close()

        if not user_data:
            return None

        return database.models.User(user_data[0], user_data[1], user_data[2])
    
    def get_user_password(self, user_id):
        cur = self.connection.cursor()

        try:
            cur.execute("""
                SELECT password FROM users WHERE id = %s
            """, (str(user_id),))

            password = cur.fetchone()
        except Exception as e:
            raise e
        finally:
            cur.close()

        if not password:
            return None

        return password[0]
    
    def search_users(self, string):
        cur = self.connection.cursor()

        try:
            cur.execute("""
                SELECT name FROM users WHERE name LIKE %s
            """, (f"%{string}%",))

            users = cur.fetchall()
        except Exception as e:
            raise e
        finally:
            cur.close()

        return users

    def delete_user(self, id):
        cur = self.connection.cursor()

        try:
            cur.execute("""
                DELETE FROM users WHERE id = %s
            """, (str(id),))

            self.connection.commit()
        except Exception as e:
            return False
        finally:
            cur.close()

        return True

    def update_user_password(self,  id, new, confirm):
        cur = self.connection.cursor()

        try:
            hashed_password = hash_str(new)

            cur.execute("""
                UPDATE users SET password = %s WHERE id = %s
            """, (hashed_password, str(id)))

            self.connection.commit()
        except Exception as e:
            raise e
        finally:
            cur.close()

        return True
