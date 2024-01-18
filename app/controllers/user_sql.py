import uuid
import psycopg2
import database
from secure.hash import hash_str

def create_user(name, password, confirm):
    if get_user(name=name):
        raise Exception(f"User {name} already exists.")

    if len(name) < 3 or len(name) > 12:
        raise ValueError("Name must be between 3 and 12 characters long.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    if " " in password:
        raise ValueError("Password must not contain spaces.")

    invalid_symbols = [" ", "'", "+", ",", "<", ">", ".", "/", "\\", "\""]
    if any(i in name for i in invalid_symbols):
        raise ValueError("Name contains invalid symbols.")

    if password != confirm:
        raise ValueError("Passwords do not match.")

    cur = database.conn.cursor()

    try:
        new_id = uuid.uuid4()
        hashed_password = str(hash_str(password))

        cur.execute("""
            INSERT INTO users (id, name, password)
            VALUES (%s, %s, %s)
        """, (str(new_id), name, hashed_password))

        database.conn.commit()
    except psycopg2.Error as e:
        raise e
    finally:
        cur.close()

    if get_user(id=new_id):
        return new_id
    else:
        ValueError("User was not created.")

def get_user(**kwargs):
    cur = database.conn.cursor()

    try:
        if kwargs.get("id"):
            cur.execute("""
                SELECT * FROM users WHERE id = %s
            """, (str(kwargs["id"]),))
        elif kwargs.get("name"):
            cur.execute("""
                SELECT * FROM users WHERE "name" = %s
            """, (str(kwargs["name"]),))

        user_data = cur.fetchone()

    except Exception as e:
        raise e
    finally:
        cur.close()

    if not user_data:
        return None

    return database.models.User(user_data[0], user_data[1], user_data[2])

def delete_user(id):
    cur = database.conn.cursor()

    try:
        cur.execute("""
            DELETE FROM users WHERE id = %s
        """, (str(uuid.UUID(id)),))

        database.conn.commit()
    except psycopg2.Error as e:
        return False
    finally:
        cur.close()

    return True

def update_user_password(id, new, confirm):
    cur = database.conn.cursor()

    try:
        hashed_password = hash_str(new)

        cur.execute("""
            UPDATE users SET password = %s WHERE id = %s
        """, (hashed_password, str(uuid.UUID(id))))

        database.conn.commit()
    except psycopg2.Error as e:
        raise e
    finally:
        cur.close()

    return True
