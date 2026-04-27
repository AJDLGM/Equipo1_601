import json
import hashlib
from datetime import datetime, timedelta


def create_certificate(username):
    cert = {
        "user":       username,
        "issued_at":  str(datetime.now()),
        "expires_at": str(datetime.now() + timedelta(days=365)),
        "status":     "active",
    }
    cert["signature"] = hashlib.sha256(json.dumps(cert).encode()).hexdigest()

    from db.database import get_connection
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO user_data (username) VALUES (?)", (username,))
    cur.execute(
        "UPDATE user_data SET cert_json=? WHERE username=?",
        (json.dumps(cert, indent=4), username),
    )
    con.commit()
    con.close()
    return True
