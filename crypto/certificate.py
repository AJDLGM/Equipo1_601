import json
import hashlib
from datetime import datetime, timedelta

def create_certificate(username):
    cert = {
        "user": username,
        "issued_at": str(datetime.utcnow()),
        "expires_at": str(datetime.utcnow() + timedelta(days=365))
    }

    cert_str = json.dumps(cert)

    # hash del certificado
    cert_hash = hashlib.sha256(cert_str.encode()).hexdigest()

    cert["signature"] = cert_hash

    with open(f"crypto/{username}_cert.json", "w") as f:
        json.dump(cert, f, indent=4)

    return True