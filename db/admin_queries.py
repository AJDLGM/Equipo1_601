import json
import os
from datetime import datetime
from db.database import get_connection


def get_all_users():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT username, role FROM users")
    users = cur.fetchall()
    con.close()
    return users


def get_all_users_with_status():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT username, role, status FROM users")
    users = cur.fetchall()
    con.close()
    return users


def get_active_users():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT username, role FROM users WHERE status='active'")
    users = cur.fetchall()
    con.close()
    return users


def update_user_role(username, role):
    con = get_connection()
    cur = con.cursor()
    cur.execute("UPDATE users SET role=? WHERE username=?", (role, username))
    con.commit()
    con.close()


def revoke_identity(username, reason, revoked_by):
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO revoked_certs (username, reason, revoked_at, revoked_by) VALUES (?, ?, ?, ?)",
        (username, reason, datetime.now().isoformat(), revoked_by)
    )
    cur.execute("UPDATE users SET status='revoked' WHERE username=?", (username,))
    con.commit()
    con.close()

    _update_cert_status(username, "revoked", reason)

    from db.logs import log_action
    log_action(revoked_by, f"REVOKE_CERT:{username} | motivo:{reason}")


def deactivate_user(username, admin_user):
    con = get_connection()
    cur = con.cursor()
    cur.execute("UPDATE users SET status='inactive' WHERE username=?", (username,))
    # Agregar a CRL si no estaba ya revocado
    cur.execute("SELECT id FROM revoked_certs WHERE username=?", (username,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO revoked_certs (username, reason, revoked_at, revoked_by) VALUES (?, ?, ?, ?)",
            (username, "Baja administrativa", datetime.now().isoformat(), admin_user)
        )
    con.commit()
    con.close()

    _update_cert_status(username, "inactive", "Baja administrativa")

    from db.logs import log_action
    log_action(admin_user, f"DEACTIVATE_USER:{username}")


def get_revoked_certs():
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT username, reason, revoked_at, revoked_by FROM revoked_certs ORDER BY revoked_at DESC"
    )
    certs = cur.fetchall()
    con.close()
    return certs


def _update_cert_status(username, status, reason=""):
    from config.paths import get_user_dir
    dirs = get_user_dir(username)
    cert_path = os.path.join(dirs["certs"], f"{username}_cert.json")
    if os.path.exists(cert_path):
        with open(cert_path) as f:
            cert = json.load(f)
        cert["status"] = status
        if reason:
            cert["revocation_reason"] = reason
        with open(cert_path, "w") as f:
            json.dump(cert, f, indent=4)


def get_pending_users():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT username, role FROM users WHERE status='pending'")
    users = cur.fetchall()
    con.close()
    return users


def approve_user(username, admin_username, role="user"):
    from crypto.keys import generate_keys
    from crypto.certificate import create_certificate

    con = get_connection()
    cur = con.cursor()
    cur.execute("UPDATE users SET status='active', role=? WHERE username=?", (role, username))
    con.commit()
    con.close()

    generate_keys(username)
    create_certificate(username)

    from db.logs import log_action
    log_action(admin_username, f"APPROVE_USER:{username}")


def get_logs():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT user, action, timestamp FROM logs ORDER BY id DESC")
    logs = cur.fetchall()
    con.close()
    return logs