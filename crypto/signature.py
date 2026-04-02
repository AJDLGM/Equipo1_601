from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def sign_message(username, message):
    with open(f"crypto/{username}_private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    signature = private_key.sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    with open(f"crypto/{username}_signature.sig", "wb") as f:
        f.write(signature)

    return signature


def verify_signature(username, message):
    with open(f"crypto/{username}_public.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    with open(f"crypto/{username}_signature.sig", "rb") as f:
        signature = f.read()

    try:
        public_key.verify(
            signature,
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print("Error verificación:", e)
        return False