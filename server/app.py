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


@app.route("/users/<username>/reject", methods=["POST"])
def reject(username):
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    from db.admin_queries import reject_pending_user
    reject_pending_user(username, sess["username"])
    return jsonify({"ok": True})


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
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    data = request.json or {}
    ok = register_user(data.get("username", ""), data.get("password", ""),
                       role=data.get("role", "externo"),
                       signed_by=sess["username"])
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


@app.route("/users/<username>/cert/verify", methods=["GET"])
def verify_cert(username):
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    from crypto.certificate import verify_certificate
    valid, message = verify_certificate(username)
    return jsonify({"valid": valid, "message": message})


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


# ── Solicitudes de firma ─────────────────────────────────────

@app.route("/signing-requests", methods=["POST"])
def create_signing_request():
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    try:
        doc_file = request.files.get("document")
        if not doc_file:
            return jsonify({"error": "No se recibio el documento"}), 400
        doc_bytes = doc_file.read()
        doc_name  = doc_file.filename or "documento"
        operativo = request.form.get("operativo", "")
        notes     = request.form.get("notes", "")
        from db.signing_requests import create_signing_request as _create
        req_id = _create(
            requester=sess["username"],
            document_name=doc_name,
            document_data=doc_bytes,
            operativo=operativo,
            notes=notes,
        )
        log_action(sess["username"],
                   f"Solicitud de firma enviada — ID: {req_id} | operativo: {operativo}")
        return jsonify({"ok": True, "id": req_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/signing-requests/mine", methods=["GET"])
def my_signing_requests():
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    from db.signing_requests import get_requests_by_requester
    rows = get_requests_by_requester(sess["username"])
    return jsonify([{
        "id": r[0], "document_name": r[1], "operativo": r[2],
        "coordinador": r[3], "status": r[4], "notes": r[5], "created_at": r[6],
    } for r in rows])


@app.route("/signing-requests/incoming", methods=["GET"])
def incoming_signing_requests():
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    from db.signing_requests import (get_requests_for_operativo,
                                     get_requests_for_coordinador,
                                     get_requests_at_route_step)
    from db.firma_route import get_firma_route
    role = sess["role"]
    username = sess["username"]

    if role == "operativo":
        rows = get_requests_for_operativo(username)
        return jsonify([{
            "id": r[0], "requester": r[1], "document_name": r[2],
            "status": r[3], "notes": r[4], "created_at": r[5],
        } for r in rows])

    if role in ("coordinador", "admin"):
        results = []
        # Solicitudes de la ruta en las que le toca a este coordinador
        route = get_firma_route()
        if username in route:
            step = route.index(username) + 1  # 1-indexed
            for r in get_requests_at_route_step(step):
                results.append({
                    "id": r[0], "requester": r[1], "document_name": r[2],
                    "status": r[3], "notes": r[4], "created_at": r[5],
                    "operativo": "", "route_step": step,
                })
        # Solicitudes del flujo legado (coordinador elegido manualmente)
        for r in get_requests_for_coordinador(username):
            results.append({
                "id": r[0], "requester": r[1], "document_name": r[2],
                "status": r[3], "notes": r[4], "created_at": r[5],
                "operativo": r[6], "route_step": 0,
            })
        return jsonify(results)

    return jsonify([])


@app.route("/signing-requests/<int:req_id>/document", methods=["GET"])
def download_signing_document(req_id):
    import base64
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    from db.signing_requests import get_request_document, get_document_for_route_step, get_route_step
    step = get_route_step(req_id)
    if step >= 1:
        row = get_document_for_route_step(req_id, step)
    else:
        row = get_request_document(req_id)
    if not row or not row[1]:
        return jsonify({"error": "Documento no encontrado"}), 404
    return jsonify({
        "document_name": row[0],
        "document_data_b64": base64.b64encode(row[1]).decode(),
    })


@app.route("/signing-requests/<int:req_id>", methods=["DELETE"])
def delete_signing_request(req_id):
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    from db.signing_requests import delete_signing_request as _delete
    _delete(req_id)
    log_action(sess["username"], f"Solicitud de firma eliminada — ID: {req_id}")
    return jsonify({"ok": True})


@app.route("/signing-requests/<int:req_id>/forward", methods=["POST"])
def forward_signing_request(req_id):
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    data = request.json or {}
    from db.signing_requests import forward_to_coordinador
    forward_to_coordinador(req_id, data.get("coordinador", ""))
    log_action(sess["username"],
               f"Solicitud de firma canalizada — ID: {req_id} | coordinador: {data.get('coordinador', '')}")
    return jsonify({"ok": True})


@app.route("/signing-requests/<int:req_id>/complete", methods=["POST"])
def complete_signing_request(req_id):
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    try:
        signed_file = request.files.get("signed_document")
        if not signed_file:
            return jsonify({"error": "No se recibio el documento firmado"}), 400
        signed_bytes = signed_file.read()
        signed_name  = signed_file.filename or "documento_firmado"
        from db.signing_requests import complete_signing_request as _complete
        _complete(req_id, signed_name, signed_bytes)
        log_action(sess["username"], f"Documento firmado — ID: {req_id}")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/signing-requests/<int:req_id>/signed-document", methods=["GET"])
def download_signed_document(req_id):
    import base64
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    from db.signing_requests import get_request_signed_document
    row = get_request_signed_document(req_id)
    if not row or not row[1]:
        return jsonify({"error": "Documento firmado no disponible"}), 404
    return jsonify({
        "document_name": row[0],
        "document_data_b64": base64.b64encode(row[1]).decode(),
    })


# ── Ruta de firmas (admin) ────────────────────────────────────

@app.route("/admin/firma-route", methods=["GET"])
def get_firma_route_endpoint():
    if not _session():
        return jsonify({"error": "No autenticado"}), 401
    from db.firma_route import get_firma_route
    return jsonify({"route": get_firma_route()})


@app.route("/admin/firma-route", methods=["POST"])
def set_firma_route_endpoint():
    sess = _session()
    if not sess or sess.get("role") != "admin":
        return jsonify({"error": "Solo el administrador puede definir la ruta"}), 403
    data = request.json or {}
    route = data.get("route", [])
    from db.firma_route import set_firma_route
    set_firma_route(route, sess["username"])
    log_action(sess["username"],
               f"Ruta de firmas actualizada: {' → '.join(route) if route else '(vacía)'}")
    return jsonify({"ok": True})


@app.route("/signing-requests/<int:req_id>/forward-route", methods=["POST"])
def forward_to_route_endpoint(req_id):
    """Operativo aprueba y envía al primer coordinador de la ruta."""
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    from db.firma_route import get_firma_route
    from db.signing_requests import forward_to_route
    route = get_firma_route()
    if not route:
        return jsonify({"error": "No hay ruta de firmas definida"}), 400
    forward_to_route(req_id)
    log_action(sess["username"],
               f"Solicitud {req_id} enviada a ruta de firmas — primer coordinador: {route[0]}")
    return jsonify({"ok": True, "first_coordinator": route[0]})


@app.route("/signing-requests/<int:req_id>/advance", methods=["POST"])
def advance_signing_route(req_id):
    """Coordinador firma y avanza al siguiente paso de la ruta."""
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    try:
        signed_file = request.files.get("signed_document")
        if not signed_file:
            return jsonify({"error": "No se recibió el documento firmado"}), 400
        signed_bytes = signed_file.read()
        signed_name  = signed_file.filename or "documento_firmado.msigned"

        from db.firma_route import get_firma_route
        from db.signing_requests import get_route_step, advance_route_step
        route = get_firma_route()
        current_step = get_route_step(req_id)
        next_step = current_step + 1
        is_final = next_step > len(route)

        advance_route_step(req_id, signed_name, signed_bytes, next_step, is_final)

        signer = sess["username"]
        if is_final:
            log_action(signer,
                       f"Ruta de firmas completada — solicitud {req_id} | último firmante: {signer}")
        else:
            next_coord = route[next_step - 1]
            log_action(signer,
                       f"Firma de ruta — solicitud {req_id} paso {current_step}/{len(route)} | siguiente: {next_coord}")

        return jsonify({"ok": True, "completed": is_final})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Log de cliente ────────────────────────────────────────────

@app.route("/logs", methods=["POST"])
def log_client_action():
    sess = _session()
    if not sess:
        return jsonify({"error": "No autenticado"}), 401
    data = request.json or {}
    action = data.get("action", "").strip()
    if not action:
        return jsonify({"error": "Accion requerida"}), 400
    log_action(sess["username"], action)
    return jsonify({"ok": True})


# ── Setup inicial (solo funciona si no hay usuarios) ──────────

@app.route("/setup", methods=["POST"])
def setup():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    con.close()
    if count > 0:
        return jsonify({"error": "El sistema ya tiene usuarios registrados"}), 400
    data = request.json or {}
    username = data.get("username", "admin")
    password = data.get("password", "")
    if not password:
        return jsonify({"error": "Se requiere contraseña"}), 400
    ok = register_user(username, password, role="admin")
    if ok:
        return jsonify({"ok": True, "mensaje": f"Admin '{username}' creado correctamente"})
    return jsonify({"error": "Error al crear el admin"}), 500


# ── Reset temporal (eliminar después de usar) ─────────────────

@app.route("/reset", methods=["POST"])
def reset():
    secret = os.environ.get("RESET_SECRET", "")
    data = request.json or {}
    if not secret or data.get("secret") != secret:
        return jsonify({"error": "No autorizado"}), 403

    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM revoked_certs")
    cur.execute("DELETE FROM user_data")
    cur.execute("DELETE FROM users")
    try:
        cur.execute("DELETE FROM logs")
    except Exception:
        pass
    con.commit()
    con.close()

    import shutil
    from config.paths import USERS_DIR
    if os.path.exists(USERS_DIR):
        shutil.rmtree(USERS_DIR)
        os.makedirs(USERS_DIR, exist_ok=True)

    return jsonify({"ok": True, "mensaje": "Base de datos limpiada. Usa /setup para crear el admin."})


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
