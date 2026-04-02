import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from datetime import datetime


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

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    signature_file = f"crypto/{username}_signature_{timestamp}.sig"

    with open(signature_file, "wb") as f:
        f.write(signature)

    return signature_file


def verify_signature(username, message, signature_file):

    with open(f"crypto/{username}_public.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    with open(signature_file, "rb") as f:
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

    except:
        return False


def sign_file(username, file_path):

    with open(f"crypto/{username}_private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    with open(file_path, "rb") as f:
        data = f.read()

    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    signature_file = f"{file_path}.sig"

    with open(signature_file, "wb") as f:
        f.write(signature)

    return signature_file


def verify_file(username, file_path):

    try:

        with open(f"crypto/{username}_public.pem", "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        with open(file_path, "rb") as f:
            data = f.read()

        with open(f"{file_path}.sig", "rb") as f:
            signature = f.read()

        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return True

    except:
        return False