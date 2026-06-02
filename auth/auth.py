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


def register_user(username, password, role="user", pending=False, signed_by=None):
    con = get_connection()
    cur = con.cursor()

    salt, hashed = hash_password(password)
    status = "pending" if pending else "active"

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, salt, role, status) VALUES (?, ?, ?, ?, ?)",
            (username, hashed, salt, role, status)
        )
        con.commit()

        if not pending:
            generate_keys(username)

            signer = signed_by or username
            con2 = get_connection()
            cur2 = con2.cursor()
            cur2.execute("SELECT private_key FROM user_data WHERE username=?", (signer,))
            row = cur2.fetchone()
            con2.close()
            signer_private_key = row[0] if row else None

            create_certificate(username, signed_by=signer, admin_private_key_pem=signer_private_key)

        log_action(username, "Cuenta registrada" if not pending else "Solicitud de registro pendiente de aprobación")

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
        "SELECT password_hash, salt, role, status FROM users WHERE username=?",
        (username,)
    )

    result = cur.fetchone()
    con.close()

    if result:

        stored_hash, salt, role, status = result

        if status == "pending":
            log_action(username, "Inicio de sesión bloqueado — cuenta pendiente de aprobación")
            return False, "pending"

        if status != "active":
            log_action(username, "Inicio de sesión bloqueado — cuenta inactiva o revocada")
            return False, None

        if verify_password(password, salt, stored_hash):

            log_action(username, "Inicio de sesión exitoso")

            return True, role

    log_action(username, "Inicio de sesión fallido — credenciales incorrectas")

    return False, None

