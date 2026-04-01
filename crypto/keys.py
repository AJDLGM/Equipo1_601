from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_keys(username):
    # Generar llave privada
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Obtener llave pública
    public_key = private_key.public_key()

    # Guardar llave privada
    with open(f"crypto/{username}_private.pem", "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    # Guardar llave pública
    with open(f"crypto/{username}_public.pem", "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    return True