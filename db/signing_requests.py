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
