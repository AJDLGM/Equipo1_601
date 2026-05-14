import json
import os
from config.paths import APP_ROOT

_CONFIG_FILE = os.path.join(APP_ROOT, "server_config.json")


def get_server_url():
    if os.path.exists(_CONFIG_FILE):
        with open(_CONFIG_FILE) as f:
            return json.load(f).get("url", "")
    return ""


def save_server_url(url):
    with open(_CONFIG_FILE, "w") as f:
        json.dump({"url": url}, f)
