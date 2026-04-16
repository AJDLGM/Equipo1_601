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
        role TEXT,
        status TEXT DEFAULT 'active'
    )
    """)

    # Migración: agregar columna status si no existe (bases de datos previas)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
    except Exception:
        pass

    cur.execute("""
    CREATE TABLE IF NOT EXISTS revoked_certs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        reason TEXT,
        revoked_at TEXT,
        revoked_by TEXT
    )
    """)

    con.commit()
    con.close()