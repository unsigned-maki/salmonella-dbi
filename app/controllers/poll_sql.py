import uuid
import database
import psycopg2
from . import user_sql as user
from errors import UserError, InternalError

def create_poll(author, options, title, description):
    if not user.get_user(id=author):
        raise UserError("Author must be a valid user.")
    
    if len(title) > 16 or len(title) < 3:
        raise UserError("Title must be between 3 and 16 characters long.")

    if len(description) > 120:
        raise UserError("Description must not exceed the 120 characters limit.")

    if len(options) > 31 or len(options) < 2:
        raise UserError("Must not provide more than 31 options.")
        
    cur = database.conn.cursor()

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

        database.conn.commit()
    except Exception as e:
        raise InternalError(e)
    finally:
        cur.close()

    return new_id

def get_poll(**kwargs):
    cur = database.conn.cursor()

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

def get_polls(**kwargs):
    cur = database.conn.cursor()

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

def increment_option(id):
    cur = database.conn.cursor()

    try:
        cur.execute("""
            UPDATE poll_options SET votes = votes + 1 WHERE id = %s
        """, (str(id),))

        database.conn.commit()
    except Exception as e:
        raise InternalError(e)
    finally:
        cur.close()

    return True

def delete_poll(id):
    cur = database.conn.cursor()

    try:
        cur.execute("""
            DELETE FROM poll_options WHERE poll_id = %s
        """, (str(id),))

        cur.execute("""
            DELETE FROM polls WHERE id = %s
        """, (str(id),))

        database.conn.commit()
    except Exception as e:
        raise InternalError(e)
    finally:
        cur.close()

    return True
