import sys
import os
import secrets
import json as _json
import socket

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, Response
from auth.auth import login_user, register_user, verify_password
from db.admin_queries import (
    get_all_users_with_status, get_active_users,
    revoke_identity, deactivate_user,
    get_revoked_certs, get_pending_users, approve_user, get_logs,
)
from db.logs import log_action
from db.database import get_connection, create_tables
from config.paths import create_directories

app = Flask(__name__)

# token → {username, role}
_sessions = {}


def _session():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    return _sessions.get(token)


# ── Auth ──────────────────────────────────────────────────────

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    success, role_or_status = login_user(data.get("username", ""), data.get("password", ""))
    if success:
        token = secrets.token_hex(32)
        _sessions[token] = {"username": data["username"], "role": role_or_status}
        return jsonify({"token": token, "role": role_or_status})
    if role_or_status == "pending":
        return jsonify({"error": "pending"}), 403
    return jsonify({"error": "invalid"}), 401


@app.route("/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    ok = register_user(data.get("username", ""), data.get("password", ""), pending=True)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"error": "El usuario ya existe"}), 409


@app.route("/auth/verify-password", methods=["POST"])
def verify_pwd():
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    data = request.json or {}
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT password_hash, salt FROM users WHERE username=?", (data.get("username", ""),))
    row = cur.fetchone()
    con.close()
    if not row:
        return jsonify({"valid": False})
    return jsonify({"valid": verify_password(data.get("password", ""), row[1], row[0])})


# ── Users ─────────────────────────────────────────────────────

@app.route("/users/pending", methods=["GET"])
def pending_users():
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    return jsonify([{"username": u, "role": r} for u, r in get_pending_users()])


@app.route("/users/<username>/approve", methods=["POST"])
def approve(username):
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    data = request.json or {}
    approve_user(username, data.get("admin_username", sess["username"]), data.get("role", "externo"))
    return jsonify({"ok": True})


@app.route("/users/active", methods=["GET"])
def active_users():
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    return jsonify([{"username": u, "role": r} for u, r in get_active_users()])


@app.route("/users/all", methods=["GET"])
def all_users():
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    return jsonify([{"username": u, "role": r, "status": s}
                    for u, r, s in get_all_users_with_status()])


@app.route("/users/<username>/revoke", methods=["POST"])
def revoke(username):
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    data = request.json or {}
    revoke_identity(username, data.get("reason", ""), data.get("admin_username", sess["username"]))
    return jsonify({"ok": True})


@app.route("/users/<username>/deactivate", methods=["POST"])
def deactivate(username):
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    data = request.json or {}
    deactivate_user(username, data.get("admin_username", sess["username"]))
    return jsonify({"ok": True})


@app.route("/admin/users", methods=["POST"])
def admin_create_user():
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    data = request.json or {}
    ok = register_user(data.get("username", ""), data.get("password", ""),
                       role=data.get("role", "externo"))
    if ok:
        return jsonify({"ok": True})
    return jsonify({"error": "El usuario ya existe"}), 409


# ── Certificados y claves (desde BD) ─────────────────────────

@app.route("/users/<username>/cert", methods=["GET"])
def get_cert(username):
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT cert_json FROM user_data WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()
    if not row or not row[0]:
        return jsonify({"error": "Certificado no encontrado"}), 404
    return jsonify(_json.loads(row[0]))


@app.route("/users/<username>/keys/private", methods=["GET"])
def get_private_key(username):
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    if sess["username"] != username and sess["role"] != "admin":
        return jsonify({"error": "No autorizado"}), 403
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT private_key FROM user_data WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()
    if not row or not row[0]:
        return jsonify({"error": "Clave no encontrada"}), 404
    return Response(row[0], mimetype="application/x-pem-file")


@app.route("/users/<username>/keys/public", methods=["GET"])
def get_public_key(username):
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT public_key FROM user_data WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()
    if not row or not row[0]:
        return jsonify({"error": "Clave no encontrada"}), 404
    return Response(row[0], mimetype="application/x-pem-file")


# ── CRL ───────────────────────────────────────────────────────

@app.route("/certs/revoked", methods=["GET"])
def revoked_certs():
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    return jsonify([{"username": u, "reason": r, "revoked_at": ra, "revoked_by": rb}
                    for u, r, ra, rb in get_revoked_certs()])


# ── Logs ──────────────────────────────────────────────────────

@app.route("/logs", methods=["GET"])
def logs():
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    return jsonify([{"user": u, "action": a, "timestamp": t} for u, a, t in get_logs()])


# ── Health ────────────────────────────────────────────────────

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"ok": True})


if __name__ == "__main__":
    create_directories()
    create_tables()

    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"

    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "desconocida"

    print("\n" + "=" * 52)
    print("  Servidor - Sistema de Identidad Digital")
    print("=" * 52)
    print(f"  Este equipo  : http://localhost:{port}")
    print(f"  Otros equipos: http://{ip}:{port}")
    print("=" * 52)
    print("  Presiona Ctrl+C para detener el servidor\n")

    app.run(host=host, port=port, debug=False)
