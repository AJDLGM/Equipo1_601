import urllib.request
import urllib.error
import json

_client = None


def get_client():
    return _client


def init_client(base_url: str):
    global _client
    _client = APIClient(base_url.strip())
    return _client


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = None

    def _req(self, method, path, body=None, raw=False):
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
                return (content if raw else json.loads(content)), None
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read()).get("error", str(e))
            except Exception:
                err = str(e)
            return None, err
        except Exception as e:
            return None, str(e)

    # ── Health ───────────────────────────────────────────────

    def ping(self):
        _, err = self._req("GET", "/ping")
        return err is None

    # ── Auth ─────────────────────────────────────────────────

    def login(self, username, password):
        result, err = self._req("POST", "/auth/login",
                                {"username": username, "password": password})
        if err == "pending":
            return False, "pending"
        if err:
            return False, None
        self.token = result["token"]
        return True, result["role"]

    def register(self, username, password):
        _, err = self._req("POST", "/auth/register",
                           {"username": username, "password": password})
        return err is None

    def verify_password(self, username, password):
        result, err = self._req("POST", "/auth/verify-password",
                                {"username": username, "password": password})
        return not err and result.get("valid", False)

    # ── Users ────────────────────────────────────────────────

    def get_pending_users(self):
        result, err = self._req("GET", "/users/pending")
        if err:
            return []
        return [(u["username"], u["role"]) for u in result]

    def approve_user(self, username, admin_username, role):
        _, err = self._req("POST", f"/users/{username}/approve",
                           {"role": role, "admin_username": admin_username})
        return err is None

    def get_active_users(self):
        result, err = self._req("GET", "/users/active")
        if err:
            return []
        return [(u["username"], u["role"]) for u in result]

    def get_all_users_with_status(self):
        result, err = self._req("GET", "/users/all")
        if err:
            return []
        return [(u["username"], u["role"], u["status"]) for u in result]

    def revoke_identity(self, username, reason, admin_username):
        _, err = self._req("POST", f"/users/{username}/revoke",
                           {"reason": reason, "admin_username": admin_username})
        return err is None

    def deactivate_user(self, username, admin_username):
        _, err = self._req("POST", f"/users/{username}/deactivate",
                           {"admin_username": admin_username})
        return err is None

    def admin_create_user(self, username, password, role):
        _, err = self._req("POST", "/admin/users",
                           {"username": username, "password": password, "role": role})
        return err is None

    # ── Claves y certificados ────────────────────────────────

    def get_cert(self, username):
        result, err = self._req("GET", f"/users/{username}/cert")
        return None if err else result

    def get_private_key(self, username):
        result, err = self._req("GET", f"/users/{username}/keys/private", raw=True)
        return None if err else result

    def get_public_key(self, username):
        result, err = self._req("GET", f"/users/{username}/keys/public", raw=True)
        return None if err else result

    def get_revoked_certs(self):
        result, err = self._req("GET", "/certs/revoked")
        if err:
            return []
        return [(c["username"], c["reason"], c["revoked_at"], c["revoked_by"])
                for c in result]

    # ── Logs ─────────────────────────────────────────────────

    def get_logs(self):
        result, err = self._req("GET", "/logs")
        if err:
            return []
        return [(e["user"], e["action"], e["timestamp"]) for e in result]
