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

    def _req(self, method, path, body=None, raw=False, timeout=10):
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
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

    def _req_multipart(self, method, path, fields=None, files=None, timeout=120):
        """Envia una peticion multipart/form-data usando requests (para archivos)."""
        import requests as _req_lib
        url = f"{self.base_url}{path}"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        mp_files = {
            name: (filename, data, "application/octet-stream")
            for name, (filename, data) in (files or {}).items()
        }
        try:
            resp = _req_lib.request(
                method, url,
                data=fields or {},
                files=mp_files or None,
                headers=headers,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json(), None
        except _req_lib.exceptions.HTTPError as e:
            try:
                err = e.response.json().get("error", str(e))
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

    def reject_user(self, username):
        from urllib.parse import quote
        _, err = self._req("POST", f"/users/{quote(username, safe='')}/reject", {})
        return err is None

    def approve_user(self, username, admin_username, role):
        from urllib.parse import quote
        _, err = self._req("POST", f"/users/{quote(username, safe='')}/approve",
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
        from urllib.parse import quote
        _, err = self._req("POST", f"/users/{quote(username, safe='')}/revoke",
                           {"reason": reason, "admin_username": admin_username})
        return err is None

    def deactivate_user(self, username, admin_username):
        from urllib.parse import quote
        _, err = self._req("POST", f"/users/{quote(username, safe='')}/deactivate",
                           {"admin_username": admin_username})
        return err is None

    def admin_create_user(self, username, password, role):
        _, err = self._req("POST", "/admin/users",
                           {"username": username, "password": password, "role": role})
        return err is None

    # ── Claves y certificados ────────────────────────────────

    def needs_key_download(self, username):
        from urllib.parse import quote
        result, err = self._req("GET", f"/users/{quote(username, safe='')}/keys/needs-download")
        return not err and result.get("needs_download", False)

    def clear_private_key(self, username):
        from urllib.parse import quote
        _, err = self._req("POST", f"/users/{quote(username, safe='')}/keys/clear-private", {})
        return err is None

    def get_cert(self, username):
        from urllib.parse import quote
        result, err = self._req("GET", f"/users/{quote(username, safe='')}/cert")
        return None if err else result

    def get_private_key(self, username):
        from urllib.parse import quote
        result, err = self._req("GET", f"/users/{quote(username, safe='')}/keys/private", raw=True)
        return None if err else result

    def get_public_key(self, username):
        from urllib.parse import quote
        result, err = self._req("GET", f"/users/{quote(username, safe='')}/keys/public", raw=True)
        return None if err else result

    def get_revoked_certs(self):
        result, err = self._req("GET", "/certs/revoked")
        if err:
            return []
        return [(c["username"], c["reason"], c["revoked_at"], c["revoked_by"])
                for c in result]

    # ── Logs ─────────────────────────────────────────────────

    def get_pending_sign_requests(self):
        result, err = self._req("GET", "/admin/sign-requests")
        return [] if err else result

    def download_sign_request_file(self, req_id):
        import base64
        result, err = self._req("GET", f"/admin/sign-requests/{req_id}/file")
        if err:
            return None, None
        return result["filename"], base64.b64decode(result["file_data_b64"])

    def complete_sign_request(self, req_id):
        _, err = self._req("POST", f"/admin/sign-requests/{req_id}/complete", {})
        return err is None

    def get_logs(self):
        result, err = self._req("GET", "/logs")
        if err:
            return []
        return [(e["user"], e["action"], e["timestamp"]) for e in result]

    def log_action(self, action: str):
        self._req("POST", "/logs", {"action": action})

    # ── Solicitudes de firma ──────────────────────────────────

    def delete_signing_request(self, req_id):
        _, err = self._req("DELETE", f"/signing-requests/{req_id}")
        return err is None

    def create_signing_request(self, document_name, document_bytes, operativo, notes=""):
        result, err = self._req_multipart(
            "POST", "/signing-requests",
            fields={"operativo": operativo, "notes": notes or ""},
            files={"document": (document_name, document_bytes)},
        )
        return (err is None), err

    def get_my_signing_requests(self):
        result, err = self._req("GET", "/signing-requests/mine")
        return [] if err else result

    def get_incoming_signing_requests(self):
        result, err = self._req("GET", "/signing-requests/incoming")
        return [] if err else result

    def download_request_document(self, req_id):
        import base64
        result, err = self._req("GET", f"/signing-requests/{req_id}/document")
        if err:
            return None, None
        return result["document_name"], base64.b64decode(result["document_data_b64"])

    def forward_signing_request(self, req_id, coordinador):
        _, err = self._req("POST", f"/signing-requests/{req_id}/forward",
                           {"coordinador": coordinador})
        return err is None

    def complete_signing_request(self, req_id, signed_document_name, signed_document_bytes):
        _, err = self._req_multipart(
            "POST", f"/signing-requests/{req_id}/complete",
            files={"signed_document": (signed_document_name, signed_document_bytes)},
        )
        return err is None

    def download_signed_document(self, req_id):
        import base64
        result, err = self._req("GET", f"/signing-requests/{req_id}/signed-document")
        if err:
            return None, None
        return result["document_name"], base64.b64decode(result["document_data_b64"])

    # ── Ruta de firmas ────────────────────────────────────────

    def get_firma_route(self):
        """Devuelve (lista, ok). ok=False si hubo error de red/servidor."""
        result, err = self._req("GET", "/admin/firma-route")
        if err:
            return [], False
        return result.get("route", []), True

    def set_firma_route(self, coordinadores: list):
        _, err = self._req("POST", "/admin/firma-route", {"route": coordinadores})
        return err is None

    def forward_to_route(self, req_id):
        _, err = self._req("POST", f"/signing-requests/{req_id}/forward-route", {})
        return err is None

    def advance_route_step(self, req_id, signed_name, signed_bytes):
        _, err = self._req_multipart(
            "POST", f"/signing-requests/{req_id}/advance",
            files={"signed_document": (signed_name, signed_bytes)},
        )
        return err is None
