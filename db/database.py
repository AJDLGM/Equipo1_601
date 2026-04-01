import sqlite3

def get_connection():
    return sqlite3.connect("sistema.db")

def create_tables():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash BLOB,
        salt BLOB,
        role TEXT
    )
    """)

    con.commit()
    con.close()