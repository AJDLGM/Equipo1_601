import os
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from config.paths import get_user_dir


def sign_message(username, message):

    dirs = get_user_dir(username)

    private_path = os.path.join(
        dirs["keys"],
        f"{username}_private.pem"
    )

    with open(private_path, "rb") as f:
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

    signature_path = os.path.join(
        dirs["sign"],
        f"signature_{timestamp}.sig"
    )

    with open(signature_path, "wb") as f:
        f.write(signature)

    return signature_path


def verify_signature(username, message, signature_file):

    dirs = get_user_dir(username)

    public_path = os.path.join(
        dirs["keys"],
        f"{username}_public.pem"
    )

    with open(public_path, "rb") as f:
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

    except Exception:
        return False


def sign_file(username, file_path):

    dirs = get_user_dir(username)

    private_path = os.path.join(
        dirs["keys"],
        f"{username}_private.pem"
    )

    with open(private_path, "rb") as f:
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

        dirs = get_user_dir(username)

        public_path = os.path.join(
            dirs["keys"],
            f"{username}_public.pem"
        )

        with open(public_path, "rb") as f:
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

    except Exception:
        return False