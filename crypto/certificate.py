import json
import hashlib
import os
from datetime import datetime, timedelta
from config.paths import get_user_dir


def create_certificate(username):

    dirs = get_user_dir(username)

    cert = {
        "user": username,
        "issued_at": str(datetime.now()),
        "expires_at": str(datetime.now() + timedelta(days=365))
    }

    cert_str = json.dumps(cert)

    cert_hash = hashlib.sha256(cert_str.encode()).hexdigest()

    cert["signature"] = cert_hash

    cert_path = os.path.join(
        dirs["certs"],
        f"{username}_cert.json"
    )

    with open(cert_path, "w") as f:
        json.dump(cert, f, indent=4)

    return True