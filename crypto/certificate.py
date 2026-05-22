import json
import hashlib
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def create_certificate(username, signed_by=None, admin_private_key_pem=None):
    from db.database import get_connection

    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT public_key FROM user_data WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()

    public_key_str = ""
    if row and row[0]:
        pk = row[0]
        public_key_str = pk.decode() if isinstance(pk, bytes) else pk

    cert = {
        "user":                username,
        "issued_at":           str(datetime.now()),
        "expires_at":          str(datetime.now() + timedelta(days=365)),
        "status":              "active",
        "signed_by":           signed_by or username,
        "public_key":          public_key_str,
        "signature_algorithm": "RSA-PSS-SHA256",
    }

    cert_data = json.dumps(
        {k: cert[k] for k in sorted(cert) if k != "signature"},
        sort_keys=True
    ).encode()

    if admin_private_key_pem:
        pk_bytes = (
            admin_private_key_pem
            if isinstance(admin_private_key_pem, bytes)
            else admin_private_key_pem.encode()
        )
        private_key = serialization.load_pem_private_key(pk_bytes, password=None)
        signature = private_key.sign(
            cert_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        cert["signature"] = signature.hex()
    else:
        cert["signature"] = hashlib.sha256(cert_data).hexdigest()

    from db.database import get_connection as _gc
    con = _gc()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO user_data (username) VALUES (?)", (username,))
    cur.execute(
        "UPDATE user_data SET cert_json=? WHERE username=?",
        (json.dumps(cert, indent=4), username),
    )
    con.commit()
    con.close()
    return True


def verify_certificate(username):
    from db.database import get_connection

    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT cert_json FROM user_data WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()

    if not row or not row[0]:
        return False, "Certificado no encontrado"

    cert = json.loads(row[0])
    signature_hex = cert.get("signature", "")
    signed_by = cert.get("signed_by", "")
    algorithm = cert.get("signature_algorithm", "")

    if algorithm != "RSA-PSS-SHA256":
        return False, "Algoritmo de firma no soportado para verificacion"

    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT public_key FROM user_data WHERE username=?", (signed_by,))
    row = cur.fetchone()
    con.close()

    if not row or not row[0]:
        return False, f"Clave publica del firmante '{signed_by}' no encontrada"

    pk = row[0]
    public_key_pem = pk if isinstance(pk, bytes) else pk.encode()

    cert_data = json.dumps(
        {k: cert[k] for k in sorted(cert) if k != "signature"},
        sort_keys=True
    ).encode()

    try:
        public_key = serialization.load_pem_public_key(public_key_pem)
        public_key.verify(
            bytes.fromhex(signature_hex),
            cert_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True, "Certificado valido"
    except Exception:
        return False, "Firma invalida"
