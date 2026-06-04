from datetime import datetime
from db.database import get_connection


def create_signing_request(requester, document_name, document_data, operativo, notes=""):
    con = get_connection()
    cur = con.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO signing_requests
        (requester, document_name, document_data, operativo, status, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'pending_operativo', ?, ?, ?)
    """, (requester, document_name, document_data, operativo, notes, now, now))
    req_id = cur.lastrowid
    con.commit()
    con.close()
    return req_id


def get_requests_for_operativo(operativo):
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        SELECT id, requester, document_name, status, notes, created_at
        FROM signing_requests
        WHERE operativo=? AND status='pending_operativo'
        ORDER BY created_at ASC
    """, (operativo,))
    rows = cur.fetchall()
    con.close()
    return rows


def get_requests_for_coordinador(coordinador):
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        SELECT id, requester, document_name, status, notes, created_at, operativo
        FROM signing_requests
        WHERE coordinador=? AND status='pending_coordinador'
        ORDER BY created_at ASC
    """, (coordinador,))
    rows = cur.fetchall()
    con.close()
    return rows


def get_requests_by_requester(requester):
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        SELECT id, document_name, operativo, coordinador, status, notes, created_at
        FROM signing_requests
        WHERE requester=?
        ORDER BY created_at DESC
    """, (requester,))
    rows = cur.fetchall()
    con.close()
    return rows


def forward_to_coordinador(request_id, coordinador):
    con = get_connection()
    cur = con.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        UPDATE signing_requests
        SET coordinador=?, status='pending_coordinador', updated_at=?
        WHERE id=?
    """, (coordinador, now, request_id))
    con.commit()
    con.close()


def complete_signing_request(request_id, signed_document_name, signed_document_data):
    con = get_connection()
    cur = con.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        UPDATE signing_requests
        SET status='completed', signed_document_name=?, signed_document_data=?, updated_at=?
        WHERE id=?
    """, (signed_document_name, signed_document_data, now, request_id))
    con.commit()
    con.close()


def get_request_document(request_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT document_name, document_data FROM signing_requests WHERE id=?",
        (request_id,)
    )
    row = cur.fetchone()
    con.close()
    return row


def get_request_signed_document(request_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT signed_document_name, signed_document_data FROM signing_requests WHERE id=?",
        (request_id,)
    )
    row = cur.fetchone()
    con.close()
    return row


# ── Funciones de ruta de firmas ───────────────────────────────

def forward_to_route(request_id):
    """El operativo aprueba y envía al primer paso de la ruta."""
    con = get_connection()
    cur = con.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        "UPDATE signing_requests SET route_step=1, status='pending_route', updated_at=? WHERE id=?",
        (now, request_id),
    )
    con.commit()
    con.close()


def get_requests_at_route_step(step: int):
    """Solicitudes que están esperando la firma del coordinador en la posición `step`."""
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        SELECT id, requester, document_name, status, notes, created_at
        FROM signing_requests
        WHERE route_step=? AND status='pending_route'
        ORDER BY created_at ASC
    """, (step,))
    rows = cur.fetchall()
    con.close()
    return rows


def get_document_for_route_step(request_id, route_step):
    """
    Devuelve el documento que debe firmar el coordinador en `route_step`.
    - Paso 1 (primer coordinador): documento original.
    - Pasos siguientes: documento firmado por el coordinador anterior.
    """
    con = get_connection()
    cur = con.cursor()
    if route_step <= 1:
        cur.execute(
            "SELECT document_name, document_data FROM signing_requests WHERE id=?",
            (request_id,),
        )
    else:
        cur.execute(
            "SELECT signed_document_name, signed_document_data FROM signing_requests WHERE id=?",
            (request_id,),
        )
    row = cur.fetchone()
    con.close()
    return row  # (name, bytes) o None


def advance_route_step(request_id, signed_name, signed_bytes, next_step, is_final=False):
    """
    Registra el documento firmado y avanza al siguiente paso de la ruta.
    Si `is_final=True`, marca la solicitud como completada.
    """
    con = get_connection()
    cur = con.cursor()
    now = datetime.utcnow().isoformat()
    new_status = "completed" if is_final else "pending_route"
    cur.execute("""
        UPDATE signing_requests
        SET signed_document_name=?, signed_document_data=?,
            route_step=?, status=?, updated_at=?
        WHERE id=?
    """, (signed_name, signed_bytes, next_step, new_status, now, request_id))
    con.commit()
    con.close()


def get_route_step(request_id):
    """Devuelve el route_step actual de una solicitud."""
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT route_step FROM signing_requests WHERE id=?", (request_id,))
    row = cur.fetchone()
    con.close()
    return row[0] if row else 0


def delete_signing_request(request_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM signing_requests WHERE id=?", (request_id,))
    con.commit()
    con.close()
