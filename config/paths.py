import os
import sys


def get_app_root():
    """Returns the writable app root: Railway volume, next to .exe when packaged, or project root in dev."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    volume = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    if volume:
        return volume
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_ROOT = get_app_root()
BASE_DIR = os.path.join(APP_ROOT, "data")
USERS_DIR = os.path.join(BASE_DIR, "users")
DB_PATH = os.path.join(APP_ROOT, "sistema.db")


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