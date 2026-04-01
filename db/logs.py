from db.database import get_connection
from datetime import datetime

def log_action(user, action):
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        timestamp TEXT
    )
    """)

    cur.execute(
        "INSERT INTO logs (user, action, timestamp) VALUES (?, ?, ?)",
        (user, action, datetime.utcnow().isoformat())
    )

    con.commit()
    con.close()