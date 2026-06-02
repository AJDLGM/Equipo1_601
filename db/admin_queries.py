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
    log_action(revoked_by, f"Certificado revocado: {username} | motivo: {reason}")


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
    log_action(admin_user, f"Baja de identidad: {username}")


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
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT cert_json FROM user_data WHERE username=?", (username,))
    row = cur.fetchone()
    if row and row[0]:
        cert = json.loads(row[0])
        cert["status"] = status
        if reason:
            cert["revocation_reason"] = reason
        cur.execute("UPDATE user_data SET cert_json=? WHERE username=?",
                    (json.dumps(cert, indent=4), username))
        con.commit()
    con.close()


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

    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT private_key FROM user_data WHERE username=?", (admin_username,))
    row = cur.fetchone()
    con.close()
    admin_private_key = row[0] if row else None

    create_certificate(username, signed_by=admin_username, admin_private_key_pem=admin_private_key)

    from db.logs import log_action
    log_action(admin_username, f"Cuenta aprobada: {username}")


def get_logs():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT user, action, timestamp FROM logs ORDER BY id DESC")
    logs = cur.fetchall()
    con.close()
    return logs


# ── Solicitudes de firma ──────────────────────────────────────

def create_sign_request(requester, filename, file_data: bytes):
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO sign_requests (requester, filename, file_data, requested_at) VALUES (?, ?, ?, ?)",
        (requester, filename, file_data, datetime.now().isoformat()),
    )
    con.commit()
    con.close()


def get_pending_sign_requests():
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT id, requester, filename, requested_at FROM sign_requests "
        "WHERE status='pendiente' ORDER BY requested_at ASC"
    )
    rows = cur.fetchall()
    con.close()
    return rows


def get_sign_request_file(request_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT filename, file_data FROM sign_requests WHERE id=?", (request_id,))
    row = cur.fetchone()
    con.close()
    return row


def complete_sign_request(request_id, signed_by):
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "UPDATE sign_requests SET status='firmado', signed_at=?, signed_by=? WHERE id=?",
        (datetime.now().isoformat(), signed_by, request_id),
    )
    con.commit()
    con.close()