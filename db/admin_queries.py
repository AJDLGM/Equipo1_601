from db.database import get_connection


def get_all_users():

    con = get_connection()
    cur = con.cursor()

    cur.execute("SELECT username, role FROM users")

    users = cur.fetchall()

    con.close()

    return users


def update_user_role(username, role):

    con = get_connection()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET role=? WHERE username=?",
        (role, username)
    )

    con.commit()
    con.close()


def get_logs():

    con = get_connection()
    cur = con.cursor()

    cur.execute(
        "SELECT user, action, timestamp FROM logs ORDER BY id DESC"
    )

    logs = cur.fetchall()

    con.close()

    return logs