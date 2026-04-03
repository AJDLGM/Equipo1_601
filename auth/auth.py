import os
import hashlib
from db.database import get_connection
from crypto.keys import generate_keys
from crypto.certificate import create_certificate
from db.logs import log_action


def hash_password(password):
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        200000
    )
    return salt, hashed


def verify_password(password, salt, stored_hash):
    new_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        200000
    )
    return new_hash == stored_hash


def register_user(username, password, role="user"):
    con = get_connection()
    cur = con.cursor()

    salt, hashed = hash_password(password)

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            (username, hashed, salt, role)
        )
        con.commit()

        # 🔐 Generar claves y certificado
        generate_keys(username)
        create_certificate(username)

        log_action(username, "REGISTER")

        return True

    except Exception as e:
        print("Error:", e)
        return False

    finally:
        con.close()


def login_user(username, password):

    con = get_connection()
    cur = con.cursor()

    cur.execute(
        "SELECT password_hash, salt, role FROM users WHERE username=?",
        (username,)
    )

    result = cur.fetchone()
    con.close()

    if result:

        stored_hash, salt, role = result

        if verify_password(password, salt, stored_hash):

            log_action(username, "LOGIN SUCCESS")

            return True, role   # 👈 IMPORTANTE

    log_action(username, "LOGIN FAILED")

    return False, None   # 👈 IMPORTANTE

