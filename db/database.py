import sqlite3
import os
from config.paths import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
        username TEXT PRIMARY KEY,
        private_key BLOB,
        public_key  BLOB,
        cert_json   TEXT
    )
    """)

    con.commit()
    _migrate_files_to_db(cur, con)
    con.close()


def _migrate_files_to_db(cur, con):
    """Copia claves y certificados de archivos existentes a la BD (una sola vez)."""
    import json
    try:
        from config.paths import USERS_DIR
    except ImportError:
        return

    if not os.path.exists(USERS_DIR):
        return

    for username in os.listdir(USERS_DIR):
        user_dir = os.path.join(USERS_DIR, username)
        if not os.path.isdir(user_dir):
            continue

        priv_path = os.path.join(user_dir, "keys",         f"{username}_private.pem")
        pub_path  = os.path.join(user_dir, "keys",         f"{username}_public.pem")
        cert_path = os.path.join(user_dir, "certificates", f"{username}_cert.json")

        cur.execute("SELECT private_key, public_key, cert_json FROM user_data WHERE username=?",
                    (username,))
        row = cur.fetchone()

        priv_data = pub_data = cert_data = None

        if os.path.exists(priv_path) and (not row or not row[0]):
            with open(priv_path, "rb") as f:
                priv_data = f.read()

        if os.path.exists(pub_path) and (not row or not row[1]):
            with open(pub_path, "rb") as f:
                pub_data = f.read()

        if os.path.exists(cert_path) and (not row or not row[2]):
            with open(cert_path) as f:
                cert_data = json.dumps(json.load(f), indent=4)

        if not (priv_data or pub_data or cert_data):
            continue

        if not row:
            cur.execute(
                "INSERT OR IGNORE INTO user_data (username, private_key, public_key, cert_json) "
                "VALUES (?, ?, ?, ?)",
                (username, priv_data, pub_data, cert_data),
            )
        else:
            if priv_data:
                cur.execute("UPDATE user_data SET private_key=? WHERE username=?",
                            (priv_data, username))
            if pub_data:
                cur.execute("UPDATE user_data SET public_key=? WHERE username=?",
                            (pub_data, username))
            if cert_data:
                cur.execute("UPDATE user_data SET cert_json=? WHERE username=?",
                            (cert_data, username))
        con.commit()
