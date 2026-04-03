import os

BASE_DIR = "data"
USERS_DIR = os.path.join(BASE_DIR, "users")


def create_directories():
    os.makedirs(USERS_DIR, exist_ok=True)


def get_user_dir(username):

    user_dir = os.path.join(USERS_DIR, username)

    keys_dir = os.path.join(user_dir, "keys")
    cert_dir = os.path.join(user_dir, "certificates")
    sign_dir = os.path.join(user_dir, "signatures")

    os.makedirs(keys_dir, exist_ok=True)
    os.makedirs(cert_dir, exist_ok=True)
    os.makedirs(sign_dir, exist_ok=True)

    return {
        "user": user_dir,
        "keys": keys_dir,
        "certs": cert_dir,
        "sign": sign_dir
    }