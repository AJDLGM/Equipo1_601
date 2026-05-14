from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_keys(username):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key  = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    from db.database import get_connection
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO user_data (username) VALUES (?)", (username,))
    cur.execute(
        "UPDATE user_data SET private_key=?, public_key=? WHERE username=?",
        (private_pem, public_pem, username),
    )
    con.commit()
    con.close()
    return True
