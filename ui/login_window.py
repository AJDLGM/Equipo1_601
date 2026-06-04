import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from auth.permissions import has_permission
from crypto.signature import sign_message, verify_signature, sign_file, verify_file
from client.api_client import get_client
from ui.admin_panel import open_admin_panel

# ── Paleta Casa Monarca ──────────────────────────────────────
BG       = "#F5F5F5"
CARD     = "#FFFFFF"
HDR_BG   = "#2D2D2D"
HDR_FG   = "#FFFFFF"
HDR_SUB  = "#CCCCCC"
PRIMARY  = "#F55C00"
PRIMARY_H= "#D44A00"
DANGER   = "#DC2626"
DANGER_H = "#B91C1C"
SUCCESS  = "#16A34A"
SUCCESS_H= "#15803D"
NEUTRAL  = "#4A4A4A"
NEUTRAL_H= "#3A3A3A"
TEXT     = "#1A1A1A"
SUBTEXT  = "#6B6B6B"
BORDER   = "#E0E0E0"
DIVIDER  = "#F0F0F0"

ROLE_BADGE = {
    "admin":       ("#FEE8D5", "#C45813"),
    "coordinador": ("#FDDCE8", "#B01848"),
    "operativo":   ("#DCFCE7", "#15803D"),
    "externo":     ("#FEF3C7", "#B45309"),
}

FONT = "Segoe UI"


# ── Helpers de UI ────────────────────────────────────────────

def _center(win, w, h):
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


def _darken(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r * 0.85), int(g * 0.85), int(b * 0.85))


def _btn(parent, text, cmd, bg=PRIMARY, fg="white", full=False, pady=9):
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg,
        activebackground=_darken(bg), activeforeground=fg,
        relief="flat", cursor="hand2",
        font=(FONT, 10, "bold"),
        padx=14, pady=pady, bd=0,
    )
    b.bind("<Enter>", lambda e: b.config(bg=_darken(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    if full:
        b.pack(fill="x", pady=3)
    return b


def _field(parent, label_text, show=""):
    tk.Label(parent, text=label_text,
             font=(FONT, 9), bg=CARD, fg=SUBTEXT).pack(anchor="w")
    frame = tk.Frame(parent, bg=CARD,
                     highlightbackground=BORDER, highlightthickness=1)
    frame.pack(fill="x", pady=(2, 12))
    entry = tk.Entry(
        frame, relief="flat", font=(FONT, 11), show=show,
        bg=CARD, fg=TEXT, insertbackground=TEXT,
        bd=0, highlightthickness=0,
    )
    entry.pack(fill="x", padx=10, pady=8)
    return entry


def _sep(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=10)


def _card(parent, title=None):
    outer = tk.Frame(parent, bg=BG)
    outer.pack(fill="x", pady=(0, 10))
    card = tk.Frame(outer, bg=CARD,
                    highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="x")
    if title:
        title_bar = tk.Frame(card, bg=DIVIDER, height=34)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text=f"  {title}",
                 font=(FONT, 9, "bold"), bg=DIVIDER, fg=SUBTEXT
                 ).pack(side="left", padx=4, pady=0)
    body = tk.Frame(card, bg=CARD)
    body.pack(fill="x", padx=16, pady=12)
    return body


# ── Conversión de zona horaria → Ciudad de México ────────────

def _to_cdmx(ts_str, fmt="%Y-%m-%d %H:%M"):
    """Convierte un timestamp UTC (ISO o 'YYYY-MM-DD HH:MM:SS') a hora CDMX."""
    from datetime import datetime, timezone
    try:
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            from backports.zoneinfo import ZoneInfo
        ts = ts_str.strip().replace("T", " ")[:19]
        dt_utc = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return dt_utc.astimezone(ZoneInfo("America/Mexico_City")).strftime(fmt)
    except Exception:
        return ts_str[:16]


# ── Logo (embebido en base64 para funcionar en el bundle) ────

def _load_logo(max_width=300, max_height=120):
    import base64, io
    from ui.logo_data import LOGO_PNG_B64

    data = base64.b64decode(LOGO_PNG_B64)

    # Intentar con PIL (mejor calidad de redimensionado)
    try:
        from PIL import Image, ImageTk
        img = Image.open(io.BytesIO(data))
        img.thumbnail((max_width, max_height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        pass

    # Fallback: tk.PhotoImage nativo (solo funciona con PNG nativo en Tk 8.6+)
    try:
        raw = tk.PhotoImage(data=LOGO_PNG_B64)
        fx = max(1, raw.width()  // max_width)
        fy = max(1, raw.height() // max_height)
        factor = max(fx, fy)
        return raw.subsample(factor) if factor > 1 else raw
    except Exception:
        return None


# ── Sincronización de claves locales ─────────────────────────

def _has_local_keys(username):
    from config.paths import USERS_DIR
    priv = os.path.join(USERS_DIR, username, "keys", f"{username}_private.pem")
    return os.path.exists(priv)


def _sync_local_keys(username, dirs, api):
    priv = os.path.join(dirs["keys"], f"{username}_private.pem")
    pub  = os.path.join(dirs["keys"], f"{username}_public.pem")
    cert = os.path.join(dirs["certs"], f"{username}_cert.json")

    if not os.path.exists(priv):
        data = api.get_private_key(username)
        if data:
            with open(priv, "wb") as f:
                f.write(data)

    if not os.path.exists(pub):
        data = api.get_public_key(username)
        if data:
            with open(pub, "wb") as f:
                f.write(data)

    cert_data = api.get_cert(username)
    if cert_data:
        with open(cert, "w") as f:
            json.dump(cert_data, f, indent=4)


# ── App principal ────────────────────────────────────────────

def start_app():
    api = get_client()

    def login():
        user     = entry_user.get().strip()
        password = entry_pass.get()
        if not user or not password:
            messagebox.showwarning("Campos vacíos",
                                   "Ingresa usuario y contraseña.", parent=root)
            return
        success, role = api.login(user, password)
        if success:
            open_dashboard(user, role)
        elif role == "pending":
            messagebox.showwarning(
                "Cuenta pendiente",
                "Tu cuenta está pendiente de aprobación\n"
                "por el administrador.", parent=root)
        else:
            messagebox.showerror(
                "Acceso denegado",
                "Usuario o contraseña incorrectos,\n"
                "o la cuenta está desactivada.", parent=root)

    def register():
        user     = entry_user.get().strip()
        password = entry_pass.get()
        if not user or not password:
            messagebox.showwarning("Campos vacíos",
                                   "Ingresa usuario y contraseña.", parent=root)
            return
        if api.register(user, password):
            messagebox.showinfo(
                "Solicitud enviada",
                f"Tu cuenta '{user}' fue creada.\n\n"
                "Está pendiente de aprobación por el administrador.\n"
                "Podrás iniciar sesión una vez que sea activada.", parent=root)
        else:
            messagebox.showerror("Error",
                                 "El nombre de usuario ya existe.", parent=root)

    def show_certificate(username):
        cert = api.get_cert(username)
        if not cert:
            messagebox.showerror("Error", "No se encontró el certificado.", parent=root)
            return
        status = cert.get("status", "active").upper()
        reason = cert.get("revocation_reason", "—")
        signed_by = cert.get("signed_by", "—")
        algorithm = cert.get("signature_algorithm", "SHA256-hash")
        signature = cert.get("signature", "")
        messagebox.showinfo(
            "Certificado Digital",
            f"Usuario      : {cert['user']}\n"
            f"Emitido      : {_to_cdmx(cert['issued_at'])}\n"
            f"Expira       : {_to_cdmx(cert['expires_at'])}\n"
            f"Estado       : {status}\n"
            f"Firmado por  : {signed_by}\n"
            f"Algoritmo    : {algorithm}\n"
            f"Motivo rev.  : {reason}\n\n"
            f"Firma        : {signature[:40]}...",
        )

    def open_dashboard(username, role):
        _pending_job = [None]

        dash = tk.Toplevel()
        dash.title("Panel Principal — Casa Monarca")
        dash.configure(bg=BG)
        dash.resizable(False, False)
        _center(dash, 640, 640)

        # ── Header ──────────────────────────────────────────
        hdr = tk.Frame(dash, bg=HDR_BG, height=72)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text=f"Bienvenido, {username}",
                 font=(FONT, 13, "bold"), bg=HDR_BG, fg=HDR_FG
                 ).place(x=20, rely=0.28, anchor="w")

        badge_bg, badge_fg = ROLE_BADGE.get(role, ("#F5D8C5", NEUTRAL))
        tk.Label(hdr, text=f"  {role.upper()}  ",
                 font=(FONT, 8, "bold"), bg=badge_bg, fg=badge_fg,
                 padx=4, pady=2
                 ).place(x=20, rely=0.72, anchor="w")

        tk.Label(hdr, text="Casa Monarca",
                 font=(FONT, 8), bg=HDR_BG, fg=HDR_SUB
                 ).place(relx=1.0, x=-20, rely=0.5, anchor="e")

        # ── Contenido scrollable ─────────────────────────────
        scroll_outer = tk.Frame(dash, bg=BG)
        scroll_outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_outer, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_outer, orient="vertical",
                                 command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=BG)
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def on_content_resize(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_resize(event):
            canvas.itemconfig(content_id, width=event.width)

        content.bind("<Configure>", on_content_resize)
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        pad = tk.Frame(content, bg=BG, height=16)
        pad.pack()
        inner = tk.Frame(content, bg=BG)
        inner.pack(fill="x", padx=20)
        pad2 = tk.Frame(content, bg=BG, height=16)
        pad2.pack()

        content = inner

        # ── Verificación de claves locales ───────────────────
        def _check_keys(parent_window):
            if _has_local_keys(username):
                return True
            from config.paths import get_user_dir as _get_dir
            d = _get_user_dir(username)
            _sync_local_keys(username, d, api)
            if _has_local_keys(username):
                return True
            messagebox.showerror(
                "Claves no encontradas",
                "No se encontraron tus claves locales.\n"
                "Descárgalas desde 'Descargar Certificado y Claves'.",
                parent=parent_window,
            )
            return False

        def _get_user_dir(uname):
            from config.paths import get_user_dir as _gud
            return _gud(uname)

        # CONSULTAR — todos los roles
        if has_permission(role, "consult"):
            sec = _card(content, "Identidad Digital")
            _btn(sec, "Ver mi Certificado",
                 lambda: show_certificate(username),
                 bg=PRIMARY, full=True)

            def download_credentials():
                import pyzipper
                from config.paths import get_user_dir as _get_dir

                pwd = simpledialog.askstring(
                    "Confirmar identidad",
                    "Ingresa tu contraseña para descargar las credenciales:",
                    show="*", parent=dash)
                if not pwd:
                    return

                if not api.verify_password(username, pwd):
                    messagebox.showerror("Contraseña incorrecta",
                                         "La contraseña ingresada no es válida.", parent=dash)
                    return

                d = _get_dir(username)
                _sync_local_keys(username, d, api)

                archivos = [
                    (os.path.join(d["keys"],  f"{username}_private.pem"), f"{username}_private.pem"),
                    (os.path.join(d["keys"],  f"{username}_public.pem"),  f"{username}_public.pem"),
                    (os.path.join(d["certs"], f"{username}_cert.json"),   f"{username}_cert.json"),
                ]
                faltantes = [n for p, n in archivos if not os.path.exists(p)]
                if faltantes:
                    messagebox.showerror(
                        "Archivos no encontrados",
                        "No se encontraron:\n" + "\n".join(faltantes), parent=dash)
                    return

                dest = filedialog.askdirectory(
                    title="Selecciona carpeta de destino", parent=dash)
                if not dest:
                    return

                zip_path = os.path.join(dest, f"{username}_credenciales.zip")
                with pyzipper.AESZipFile(zip_path, "w",
                                         compression=pyzipper.ZIP_DEFLATED,
                                         encryption=pyzipper.WZ_AES) as zf:
                    zf.setpassword(pwd.encode())
                    for src, name in archivos:
                        zf.write(src, name)

                messagebox.showinfo(
                    "Descarga completa",
                    f"ZIP cifrado guardado en:\n{zip_path}\n\n"
                    "Usa tu contraseña de cuenta para abrirlo.", parent=dash)

            _btn(sec, "Descargar Certificado y Claves",
                 download_credentials, bg=NEUTRAL, full=True)

        # SOLICITAR FIRMA — solo externo
        if role == "externo":
            sec_req = _card(content, "Solicitar Firma de Documento")

            _sel_file = [None]

            tk.Label(sec_req, text="Documento:",
                     font=(FONT, 9), bg=CARD, fg=SUBTEXT).pack(anchor="w")
            _file_frame = tk.Frame(sec_req, bg=CARD,
                                   highlightbackground=BORDER, highlightthickness=1)
            _file_frame.pack(fill="x", pady=(2, 8))
            _file_lbl = tk.Label(_file_frame, text="Ningún archivo seleccionado",
                                 font=(FONT, 9), bg=CARD, fg=SUBTEXT)
            _file_lbl.pack(side="left", padx=10, pady=6, fill="x", expand=True)

            def _pick_file():
                path = filedialog.askopenfilename(
                    parent=dash,
                    filetypes=[("PDF", "*.pdf"), ("Word", "*.docx"), ("Todos", "*.*")])
                if path:
                    _sel_file[0] = path
                    _file_lbl.config(text=os.path.basename(path), fg=TEXT)

            _btn(sec_req, "Seleccionar archivo", _pick_file, bg=NEUTRAL, full=True)

            tk.Label(sec_req, text="Enviar a operativo:",
                     font=(FONT, 9), bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(10, 2))
            _op_var = tk.StringVar()
            _op_cb = ttk.Combobox(sec_req, textvariable=_op_var,
                                  state="readonly", font=(FONT, 10))
            _op_cb.pack(fill="x", pady=(0, 10))

            def _load_ops():
                ops = [u for u, r in api.get_active_users() if r == "operativo"]
                _op_cb["values"] = ops
                if ops:
                    _op_var.set(ops[0])

            _load_ops()

            _entry_notes = _field(sec_req, "Notas (opcional)")

            def _send_req():
                if not _sel_file[0]:
                    messagebox.showwarning("Sin archivo",
                                           "Selecciona un documento.", parent=dash)
                    return
                op = _op_var.get()
                if not op:
                    messagebox.showwarning("Sin operativo",
                                           "No hay operativos disponibles.", parent=dash)
                    return
                try:
                    with open(_sel_file[0], "rb") as f:
                        doc_bytes = f.read()
                    doc_name = os.path.basename(_sel_file[0])
                    notes = _entry_notes.get().strip()
                    ok, err = api.create_signing_request(doc_name, doc_bytes, op, notes)
                    if ok:
                        messagebox.showinfo(
                            "Solicitud enviada",
                            f"Documento enviado a '{op}' para revisión.", parent=dash)
                        _sel_file[0] = None
                        _file_lbl.config(text="Ningún archivo seleccionado", fg=SUBTEXT)
                        _entry_notes.delete(0, tk.END)
                        _refresh_my()
                    else:
                        messagebox.showerror("Error al enviar",
                                             f"No se pudo enviar la solicitud:\n{err}",
                                             parent=dash)
                except Exception as e:
                    messagebox.showerror("Error", str(e), parent=dash)

            _btn(sec_req, "Enviar solicitud de firma", _send_req, bg=PRIMARY, full=True)

            # Mis solicitudes
            sec_my = _card(content, "Mis Solicitudes de Firma")

            _ST = {
                "pending_operativo":   "Pendiente (operativo)",
                "pending_coordinador": "En proceso (coordinador)",
                "completed":           "Completado",
            }

            _my_frame = tk.Frame(sec_my, bg=CARD,
                                 highlightbackground=BORDER, highlightthickness=1)
            _my_frame.pack(fill="x", pady=(2, 8))
            _sb_my = tk.Scrollbar(_my_frame, orient="vertical")
            _my_lb = tk.Listbox(
                _my_frame, height=4,
                yscrollcommand=_sb_my.set,
                exportselection=False, relief="flat", bd=0,
                font=("Consolas", 9),
                bg=CARD, fg=TEXT,
                selectbackground=PRIMARY, selectforeground="white",
                activestyle="none",
            )
            _sb_my.config(command=_my_lb.yview)
            _sb_my.pack(side="right", fill="y")
            _my_lb.pack(side="left", fill="x", expand=True, padx=4, pady=4)

            _my_store = [None]

            def _refresh_my():
                _my_lb.delete(0, tk.END)
                reqs = api.get_my_signing_requests()
                _my_store[0] = reqs
                for r in reqs:
                    st   = _ST.get(r["status"], r["status"])
                    date = _to_cdmx(r["created_at"], "%Y-%m-%d")
                    _my_lb.insert(
                        tk.END,
                        f"  {r['document_name'][:22]:<24} {st:<26} {date}")

            def _dl_signed():
                sel = _my_lb.curselection()
                if not sel:
                    messagebox.showwarning("Sin selección",
                                           "Selecciona una solicitud.", parent=dash)
                    return
                req = _my_store[0][sel[0]]
                if req["status"] != "completed":
                    messagebox.showinfo("No disponible",
                                        "El documento aún no ha sido firmado.", parent=dash)
                    return
                name, data = api.download_signed_document(req["id"])
                if not data:
                    messagebox.showerror("Error",
                                         "No se pudo descargar el documento.", parent=dash)
                    return
                dest = filedialog.askdirectory(
                    title="Selecciona carpeta de destino", parent=dash)
                if not dest:
                    return
                save_path = os.path.join(dest, name)
                with open(save_path, "wb") as f:
                    f.write(data)
                messagebox.showinfo("Descargado",
                                    f"Documento firmado guardado en:\n{save_path}", parent=dash)

            _refresh_my()

            _row_my = tk.Frame(sec_my, bg=CARD)
            _row_my.pack(fill="x")
            _btn(_row_my, "Actualizar", _refresh_my, bg=NEUTRAL
                 ).pack(side="left", padx=(0, 6), pady=2)
            _btn(_row_my, "Descargar firmado", _dl_signed, bg=SUCCESS
                 ).pack(side="left", pady=2)

        # EDITAR
        if has_permission(role, "edit"):
            sec = _card(content, "Firma Digital")

            def sign_file_ui():
                path = filedialog.askopenfilename(
                    parent=dash,
                    filetypes=[
                        ("PDF",  "*.pdf"),
                        ("Word", "*.docx"),
                        ("Word 97-2003", "*.doc"),
                        ("Todos los archivos", "*.*"),
                    ]
                )
                if not path:
                    return
                if not _check_keys(dash):
                    return
                try:
                    signed_path = sign_file(username, path)
                    api.log_action(f"Firma de archivo: {os.path.basename(path)}")
                    messagebox.showinfo(
                        "Archivo firmado",
                        f"Documento firmado correctamente.\n\n"
                        f"Archivo generado:\n{signed_path}\n\n"
                        f"La firma queda embebida dentro del propio archivo.",
                        parent=dash
                    )
                except Exception as e:
                    api.log_action(f"Error al firmar archivo: {os.path.basename(path)}")
                    messagebox.showerror(
                        "Error al firmar",
                        f"No se pudo firmar el archivo:\n\n{e}",
                        parent=dash
                    )

            _btn(sec, "Firmar archivo", sign_file_ui, bg=PRIMARY, full=True)

        # SOLICITUDES RECIBIDAS — operativo
        if role == "operativo":
            sec_op = _card(content, "Solicitudes de Firma Recibidas")

            _op_frame = tk.Frame(sec_op, bg=CARD,
                                 highlightbackground=BORDER, highlightthickness=1)
            _op_frame.pack(fill="x", pady=(2, 8))
            _sb_op = tk.Scrollbar(_op_frame, orient="vertical")
            _op_lb = tk.Listbox(
                _op_frame, height=5,
                yscrollcommand=_sb_op.set,
                exportselection=False, relief="flat", bd=0,
                font=("Consolas", 9),
                bg=CARD, fg=TEXT,
                selectbackground=PRIMARY, selectforeground="white",
                activestyle="none",
            )
            _sb_op.config(command=_op_lb.yview)
            _sb_op.pack(side="right", fill="y")
            _op_lb.pack(side="left", fill="x", expand=True, padx=4, pady=4)

            _op_store = [None]

            def _refresh_op():
                _op_lb.delete(0, tk.END)
                reqs = api.get_incoming_signing_requests()
                _op_store[0] = reqs
                for r in reqs:
                    date = _to_cdmx(r["created_at"], "%Y-%m-%d")
                    _op_lb.insert(
                        tk.END,
                        f"  {r['requester']:<16} {r['document_name'][:24]:<26} {date}")

            def _forward_route():
                """Envía la solicitud al primer coordinador de la ruta de firmas."""
                sel = _op_lb.curselection()
                if not sel:
                    messagebox.showwarning("Sin selección",
                                           "Selecciona una solicitud.", parent=dash)
                    return
                req = _op_store[0][sel[0]]
                if api.forward_to_route(req["id"]):
                    route, _ = api.get_firma_route()
                    messagebox.showinfo(
                        "Enviado a ruta",
                        f"Solicitud enviada a la ruta de firmas.\n"
                        f"Primer coordinador: {route[0] if route else '—'}",
                        parent=dash)
                    _refresh_op()
                else:
                    messagebox.showerror(
                        "Error",
                        "No se pudo enviar a la ruta.\n"
                        "Verifica que el administrador haya definido una ruta de firmas.",
                        parent=dash)

            def _forward_manual():
                """Canaliza manualmente a un coordinador (flujo legado)."""
                sel = _op_lb.curselection()
                if not sel:
                    messagebox.showwarning("Sin selección",
                                           "Selecciona una solicitud.", parent=dash)
                    return
                req = _op_store[0][sel[0]]
                coords = [u for u, r in api.get_active_users() if r == "coordinador"]
                if not coords:
                    messagebox.showerror("Sin coordinadores",
                                         "No hay coordinadores activos.", parent=dash)
                    return

                fwd = tk.Toplevel(dash)
                fwd.title("Canalizar a Coordinador")
                fwd.configure(bg=CARD)
                fwd.resizable(False, False)
                _sw, _sh = dash.winfo_screenwidth(), dash.winfo_screenheight()
                fwd.geometry(f"340x200+{(_sw-340)//2}+{(_sh-200)//2}")
                fwd.grab_set()

                tk.Label(fwd,
                         text=f"Documento : {req['document_name']}\n"
                              f"Remitente : {req['requester']}\n\n"
                              f"Selecciona el coordinador:",
                         font=(FONT, 9), bg=CARD, fg=TEXT
                         ).pack(pady=(16, 6), padx=20, anchor="w")

                _cv = tk.StringVar(value=coords[0])
                ttk.Combobox(fwd, textvariable=_cv, values=coords,
                             state="readonly", font=(FONT, 10)
                             ).pack(fill="x", padx=20, pady=(0, 14))

                def _confirm():
                    coord = _cv.get()
                    fwd.destroy()
                    if api.forward_signing_request(req["id"], coord):
                        messagebox.showinfo(
                            "Canalizando",
                            f"Solicitud enviada al coordinador '{coord}'.", parent=dash)
                        _refresh_op()
                    else:
                        messagebox.showerror("Error",
                                             "No se pudo canalizar la solicitud.", parent=dash)

                _btn(fwd, "Canalizar", _confirm, bg=PRIMARY, pady=8
                     ).pack(fill="x", padx=20)
                fwd.wait_window()

            _refresh_op()

            _row_op = tk.Frame(sec_op, bg=CARD)
            _row_op.pack(fill="x")
            _btn(_row_op, "Actualizar", _refresh_op, bg=NEUTRAL
                 ).pack(side="left", padx=(0, 6), pady=2)
            _btn(_row_op, "Enviar a ruta de firmas", _forward_route, bg=PRIMARY
                 ).pack(side="left", padx=(0, 6), pady=2)
            _btn(_row_op, "Canalizar manualmente", _forward_manual, bg=NEUTRAL
                 ).pack(side="left", pady=2)

        # AUTORIZAR
        if has_permission(role, "authorize"):
            sec = _card(content, "Verificación de Firmas")

            def verify_file_ui():
                path = filedialog.askopenfilename(
                    parent=dash,
                    filetypes=[
                        ("PDF firmado",  "*.pdf"),
                        ("Word firmado", "*.docx *.doc"),
                        ("Contenedor firmado", "*.signed"),
                        ("Todos los archivos", "*.*"),
                    ]
                )
                if not path:
                    return
                ok, result = verify_file(path)
                if ok:
                    signed_at = _to_cdmx(result["signed_at"])
                    api.log_action(
                        f"Verificación de archivo: firma válida | archivo:{os.path.basename(path)} | firmante:{result['signer']}"
                    )
                    if result.get("total_signatures", 1) > 1:
                        # Documento de ruta multi-firma
                        ruta_str = " → ".join(result.get("route", []))
                        messagebox.showinfo(
                            "Ruta de firmas válida",
                            f"El documento tiene TODAS las firmas de la ruta y es válido.\n\n"
                            f"Archivo      : {result['original_filename']}\n"
                            f"Ruta definida: {ruta_str}\n"
                            f"Firmantes    : {result['all_signers']}\n"
                            f"Última firma : {signed_at}\n"
                            f"Hash SHA-256 : {result['hash_sha256'][:40]}...",
                            parent=dash,
                        )
                    else:
                        messagebox.showinfo(
                            "Firma válida",
                            f"El documento es auténtico e íntegro.\n\n"
                            f"Firmante     : {result['signer']}\n"
                            f"Archivo      : {result['original_filename']}\n"
                            f"Firmado el   : {signed_at}\n"
                            f"Hash SHA-256 : {result['hash_sha256'][:40]}...\n"
                            f"Cert. estado : {result['cert_status']}",
                            parent=dash,
                        )
                else:
                    api.log_action(f"Verificación de archivo: firma inválida | archivo:{os.path.basename(path)}")
                    messagebox.showerror("Firma inválida", result, parent=dash)

            _btn(sec, "Verificar archivo", verify_file_ui, bg=SUCCESS, full=True)

        # DOCUMENTOS PENDIENTES DE FIRMA — coordinador
        if role == "coordinador":
            sec_cd = _card(content, "Documentos Pendientes de Firma")

            _cd_frame = tk.Frame(sec_cd, bg=CARD,
                                 highlightbackground=BORDER, highlightthickness=1)
            _cd_frame.pack(fill="x", pady=(2, 8))
            _sb_cd = tk.Scrollbar(_cd_frame, orient="vertical")
            _cd_lb = tk.Listbox(
                _cd_frame, height=5,
                yscrollcommand=_sb_cd.set,
                exportselection=False, relief="flat", bd=0,
                font=("Consolas", 9),
                bg=CARD, fg=TEXT,
                selectbackground=PRIMARY, selectforeground="white",
                activestyle="none",
            )
            _sb_cd.config(command=_cd_lb.yview)
            _sb_cd.pack(side="right", fill="y")
            _cd_lb.pack(side="left", fill="x", expand=True, padx=4, pady=4)

            _cd_store = [None]

            def _refresh_cd():
                _cd_lb.delete(0, tk.END)
                reqs = api.get_incoming_signing_requests()
                _cd_store[0] = reqs
                for r in reqs:
                    date = _to_cdmx(r["created_at"])
                    _cd_lb.insert(
                        tk.END,
                        f"  {r['requester']:<14} {r['document_name'][:22]:<24} {date}")

            def _sign_doc():
                sel = _cd_lb.curselection()
                if not sel:
                    messagebox.showwarning("Sin selección",
                                           "Selecciona un documento.", parent=dash)
                    return
                req = _cd_store[0][sel[0]]

                if not _check_keys(dash):
                    return

                doc_name, doc_bytes = api.download_request_document(req["id"])
                if not doc_bytes:
                    messagebox.showerror("Error",
                                         "No se pudo descargar el documento.", parent=dash)
                    return

                is_route = req.get("route_step", 0) >= 1

                import tempfile
                import shutil as _shutil
                tmp = tempfile.mkdtemp()
                tmp_path = os.path.join(tmp, doc_name)
                try:
                    with open(tmp_path, "wb") as f:
                        f.write(doc_bytes)

                    if is_route:
                        from crypto.signature import sign_for_route
                        signed_path, signed_bytes = sign_for_route(username, tmp_path)
                        signed_name = os.path.basename(signed_path)
                        result = api.advance_route_step(req["id"], signed_name, signed_bytes)
                        if result:
                            route, _ = api.get_firma_route()
                            current_step = req.get("route_step", 1)
                            if current_step >= len(route):
                                msg = (f"Documento '{doc_name}' firmado.\n"
                                       "Es la última firma de la ruta.\n"
                                       "El solicitante ya puede descargarlo.")
                            else:
                                next_coord = route[current_step] if current_step < len(route) else "—"
                                msg = (f"Documento '{doc_name}' firmado.\n"
                                       f"Enviado al siguiente coordinador: {next_coord}")
                            messagebox.showinfo("Firmado (ruta)", msg, parent=dash)
                            _refresh_cd()
                        else:
                            messagebox.showerror("Error",
                                                 "No se pudo registrar la firma en la ruta.",
                                                 parent=dash)
                    else:
                        signed_path = sign_file(username, tmp_path)
                        with open(signed_path, "rb") as f:
                            signed_bytes = f.read()
                        signed_name = os.path.basename(signed_path)
                        if api.complete_signing_request(req["id"], signed_name, signed_bytes):
                            messagebox.showinfo(
                                "Firmado",
                                f"Documento '{doc_name}' firmado.\n"
                                f"El solicitante puede descargarlo.", parent=dash)
                            _refresh_cd()
                        else:
                            messagebox.showerror("Error",
                                                 "No se pudo guardar el documento firmado.",
                                                 parent=dash)
                except Exception as e:
                    messagebox.showerror("Error al firmar", str(e), parent=dash)
                finally:
                    _shutil.rmtree(tmp, ignore_errors=True)

            _refresh_cd()

            _row_cd = tk.Frame(sec_cd, bg=CARD)
            _row_cd.pack(fill="x")
            _btn(_row_cd, "Actualizar", _refresh_cd, bg=NEUTRAL
                 ).pack(side="left", padx=(0, 6), pady=2)
            _btn(_row_cd, "Firmar documento seleccionado", _sign_doc, bg=SUCCESS
                 ).pack(side="left", pady=2)

        # ADMIN — Solicitudes pendientes
        if role == "admin":
            sec_pending = _card(content, "Solicitudes de Activación Pendientes")

            pending_frame = tk.Frame(sec_pending, bg=CARD,
                                     highlightbackground=BORDER, highlightthickness=1)
            pending_frame.pack(fill="x", pady=(2, 10))
            sb_p = tk.Scrollbar(pending_frame, orient="vertical")
            pending_lb = tk.Listbox(
                pending_frame, height=4,
                yscrollcommand=sb_p.set,
                exportselection=False,
                relief="flat", bd=0,
                font=(FONT, 10),
                bg=CARD, fg=TEXT,
                selectbackground=PRIMARY,
                selectforeground="white",
                activestyle="none",
            )
            sb_p.config(command=pending_lb.yview)
            sb_p.pack(side="right", fill="y")
            pending_lb.pack(side="left", fill="x", expand=True, padx=4, pady=4)

            no_pending_lbl = tk.Label(
                sec_pending, text="No hay solicitudes pendientes.",
                font=(FONT, 9, "italic"), bg=CARD, fg=SUBTEXT)

            def refresh_pending():
                pending_lb.delete(0, tk.END)
                pending = api.get_pending_users()
                if pending:
                    no_pending_lbl.pack_forget()
                    pending_frame.pack(fill="x", pady=(2, 10))
                    for uname, urole in pending:
                        pending_lb.insert(tk.END, f"  {uname:<22} [{urole}]")
                else:
                    pending_frame.pack_forget()
                    no_pending_lbl.pack(anchor="w", pady=(0, 8))

            def do_approve():
                sel = pending_lb.curselection()
                if not sel:
                    messagebox.showwarning("Sin selección",
                                           "Selecciona una cuenta para aprobar.", parent=dash)
                    return
                uname = pending_lb.get(sel[0]).strip().rsplit("[", 1)[0].strip()

                role_dialog = tk.Toplevel(dash)
                role_dialog.title("Asignar Rol")
                role_dialog.configure(bg=CARD)
                role_dialog.resizable(False, False)
                sw, sh = dash.winfo_screenwidth(), dash.winfo_screenheight()
                role_dialog.geometry(f"300x160+{(sw-300)//2}+{(sh-160)//2}")
                role_dialog.grab_set()

                tk.Label(role_dialog,
                         text=f"Selecciona el rol para '{uname}':",
                         font=(FONT, 10), bg=CARD, fg=TEXT
                         ).pack(pady=(20, 8), padx=20, anchor="w")

                role_var = tk.StringVar(value="externo")
                cb = ttk.Combobox(role_dialog, textvariable=role_var,
                                  values=["externo", "operativo", "coordinador", "admin"],
                                  state="readonly", font=(FONT, 10))
                cb.pack(fill="x", padx=20, pady=(0, 16))

                def confirm_approve():
                    selected_role = role_var.get()
                    role_dialog.destroy()
                    api.approve_user(uname, username, selected_role)
                    messagebox.showinfo(
                        "Cuenta activada",
                        f"La cuenta '{uname}' fue activada con rol '{selected_role}'.", parent=dash)
                    refresh_pending()

                _btn(role_dialog, "Aprobar", confirm_approve,
                     bg=SUCCESS, pady=8).pack(fill="x", padx=20)

                role_dialog.wait_window()

            def do_reject():
                sel = pending_lb.curselection()
                if not sel:
                    messagebox.showwarning("Sin selección",
                                           "Selecciona una cuenta para rechazar.", parent=dash)
                    return
                uname = pending_lb.get(sel[0]).strip().rsplit("[", 1)[0].strip()
                if messagebox.askyesno(
                    "Confirmar rechazo",
                    f"¿Rechazar la solicitud de '{uname}'?\n\n"
                    "La cuenta será eliminada del sistema.",
                    parent=dash, icon="warning",
                ):
                    ok = api.reject_user(uname)
                    if ok:
                        messagebox.showinfo(
                            "Solicitud rechazada",
                            f"La solicitud de '{uname}' fue rechazada.", parent=dash)
                    else:
                        messagebox.showerror(
                            "Error",
                            f"No se pudo rechazar la solicitud de '{uname}'.\n"
                            "Verifica que el servidor esté actualizado.", parent=dash)
                    refresh_pending()

            def _auto_refresh_pending():
                try:
                    refresh_pending()
                except tk.TclError:
                    return
                _pending_job[0] = dash.after(10000, _auto_refresh_pending)

            _auto_refresh_pending()
            _row_p = tk.Frame(sec_pending, bg=CARD)
            _row_p.pack(fill="x")
            _btn(_row_p, "Aprobar cuenta", do_approve,
                 bg=SUCCESS, pady=9).pack(side="left", fill="x", expand=True, padx=(0, 4))
            _btn(_row_p, "Rechazar solicitud", do_reject,
                 bg=DANGER, pady=9).pack(side="left", fill="x", expand=True)

        # ADMIN — Solicitudes de firma pendientes
        if role == "admin":
            sec_sf = _card(content, "Solicitudes de Firma Pendientes")

            def open_sign_requests_panel():
                panel = tk.Toplevel(dash)
                panel.title("Solicitudes de Firma")
                panel.configure(bg=BG)
                panel.resizable(False, False)
                _center(panel, 720, 480)

                hdr_p = tk.Frame(panel, bg=HDR_BG, height=52)
                hdr_p.pack(fill="x")
                hdr_p.pack_propagate(False)
                tk.Label(hdr_p, text="  Solicitudes de firma de documentos",
                         font=(FONT, 11, "bold"), bg=HDR_BG, fg=HDR_FG
                         ).pack(side="left", padx=12, pady=12)

                main_f = tk.Frame(panel, bg=BG)
                main_f.pack(fill="both", expand=True, padx=16, pady=12)

                # Encabezado de columnas
                cols_f = tk.Frame(main_f, bg=DIVIDER)
                cols_f.pack(fill="x", pady=(0, 2))
                for txt, w in [("Fecha / Hora", 160), ("Solicitante", 130), ("Archivo", 280)]:
                    tk.Label(cols_f, text=txt, font=(FONT, 8, "bold"),
                             bg=DIVIDER, fg=SUBTEXT, width=0, anchor="w",
                             padx=8, pady=4).pack(side="left")

                # Lista scrollable
                list_outer = tk.Frame(main_f, bg=CARD,
                                      highlightbackground=BORDER, highlightthickness=1)
                list_outer.pack(fill="both", expand=True)
                sb_sf = tk.Scrollbar(list_outer, orient="vertical")
                lb_sf = tk.Listbox(
                    list_outer, height=12,
                    yscrollcommand=sb_sf.set,
                    exportselection=False,
                    relief="flat", bd=0,
                    font=("Consolas", 9),
                    bg=CARD, fg=TEXT,
                    selectbackground=PRIMARY,
                    selectforeground="white",
                    activestyle="none",
                )
                sb_sf.config(command=lb_sf.yview)
                sb_sf.pack(side="right", fill="y")
                lb_sf.pack(side="left", fill="both", expand=True, padx=4, pady=4)

                _requests = []

                def load_requests():
                    lb_sf.delete(0, tk.END)
                    _requests.clear()
                    rows = api.get_pending_sign_requests()
                    for r in rows:
                        _requests.append(r)
                        fecha = _to_cdmx(r["requested_at"])
                        lb_sf.insert(
                            tk.END,
                            f"  {fecha}   {r['requester']:<16}  {r['filename']}"
                        )
                    if not rows:
                        lb_sf.insert(tk.END, "  No hay solicitudes pendientes.")

                load_requests()

                btn_f = tk.Frame(main_f, bg=BG)
                btn_f.pack(fill="x", pady=(10, 0))

                def firmar_solicitud():
                    sel = lb_sf.curselection()
                    if not sel:
                        messagebox.showwarning("Sin selección",
                                               "Selecciona una solicitud de la lista.", parent=panel)
                        return
                    req = _requests[sel[0]]
                    if not _check_keys(panel):
                        return

                    fname, file_bytes = api.download_sign_request_file(req["id"])
                    if not file_bytes:
                        messagebox.showerror("Error",
                                             "No se pudo descargar el archivo.", parent=panel)
                        return

                    import tempfile
                    ext = os.path.splitext(fname)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext, prefix="solicitud_") as tmp:
                        tmp.write(file_bytes)
                        tmp_path = tmp.name

                    try:
                        signed_path = sign_file(username, tmp_path)
                    except Exception as e:
                        os.unlink(tmp_path)
                        messagebox.showerror("Error al firmar",
                                             f"No se pudo firmar el archivo:\n{e}", parent=panel)
                        return

                    os.unlink(tmp_path)

                    dest_dir = filedialog.askdirectory(
                        title="Selecciona dónde guardar el documento firmado", parent=panel)
                    if dest_dir:
                        import shutil
                        final_name = os.path.splitext(fname)[0] + "_firmado" + ext
                        final_path = os.path.join(dest_dir, final_name)
                        shutil.move(signed_path, final_path)
                    else:
                        final_path = signed_path

                    api.complete_sign_request(req["id"])
                    api.log_action(
                        f"Solicitud de firma completada: {fname} | solicitante: {req['requester']}"
                    )
                    messagebox.showinfo(
                        "Documento firmado",
                        f"El documento '{fname}' fue firmado correctamente.\n\n"
                        f"Guardado en:\n{final_path}",
                        parent=panel,
                    )
                    load_requests()

                _btn(btn_f, "Actualizar lista", load_requests, bg=NEUTRAL
                     ).pack(side="left", padx=(0, 8))
                _btn(btn_f, "Firmar documento seleccionado", firmar_solicitud, bg=SUCCESS
                     ).pack(side="left")

            _btn(sec_sf, "Ver solicitudes pendientes de firma",
                 open_sign_requests_panel, bg=PRIMARY, full=True)

        # ADMIN — Logs y panel
        if role == "admin":
            sec = _card(content, "Administración del Sistema")
            row3 = tk.Frame(sec, bg=CARD)
            row3.pack(fill="x")

            def view_logs():
                log_win = tk.Toplevel(dash)
                log_win.title("Logs del Sistema")
                log_win.configure(bg=BG)
                _center(log_win, 700, 420)

                hdr2 = tk.Frame(log_win, bg=HDR_BG, height=48)
                hdr2.pack(fill="x")
                hdr2.pack_propagate(False)
                tk.Label(hdr2, text="  Registro de actividad del sistema",
                         font=(FONT, 11, "bold"), bg=HDR_BG, fg=HDR_FG
                         ).pack(side="left", padx=12, pady=10)

                frame = tk.Frame(log_win, bg=BG)
                frame.pack(fill="both", expand=True, padx=16, pady=14)

                sb = tk.Scrollbar(frame)
                sb.pack(side="right", fill="y")
                txt = tk.Text(
                    frame, font=("Consolas", 9),
                    bg=CARD, fg=TEXT, relief="flat",
                    yscrollcommand=sb.set,
                    highlightbackground=BORDER, highlightthickness=1,
                    padx=10, pady=8,
                )
                txt.pack(fill="both", expand=True)
                sb.config(command=txt.yview)

                for user, action, timestamp in api.get_logs():
                    txt.insert(tk.END, f"{_to_cdmx(timestamp)}  |  {user:<18}|  {action}\n")
                txt.config(state="disabled")

            _btn(row3, "Gestionar Identidades",
                 lambda: open_admin_panel(username), bg=PRIMARY
                 ).pack(side="left", padx=(0, 6), pady=2)
            _btn(row3, "Ver Logs", view_logs, bg=NEUTRAL
                 ).pack(side="left", pady=2)

        # Footer
        _sep(content)

        def logout():
            if _pending_job[0]:
                dash.after_cancel(_pending_job[0])
            dash.destroy()

        _btn(content, "Cerrar sesión", logout,
             bg=DANGER, full=True, pady=10)

    # ── Ventana de login ─────────────────────────────────────
    root = tk.Tk()
    root.title("Casa Monarca — Sistema de Identidad Digital")
    root.configure(bg=BG)
    root.resizable(False, False)
    _center(root, 420, 600)

    # ── Área del logo ─────────────────────────────────────────
    logo_frame = tk.Frame(root, bg=CARD, height=150)
    logo_frame.pack(fill="x")
    logo_frame.pack_propagate(False)

    _logo_img = _load_logo(300, 130)
    if _logo_img:
        logo_lbl = tk.Label(logo_frame, image=_logo_img, bg=CARD)
        logo_lbl.place(relx=0.5, rely=0.5, anchor="center")
        logo_lbl._logo_img = _logo_img
    else:
        tk.Label(logo_frame,
                 text="CASA MONARCA",
                 font=(FONT, 20, "bold"), bg=CARD, fg=PRIMARY
                 ).place(relx=0.5, rely=0.45, anchor="center")
        tk.Label(logo_frame,
                 text="Ayuda Humanitaria al Migrante, A.B.P.",
                 font=(FONT, 8), bg=CARD, fg=SUBTEXT
                 ).place(relx=0.5, rely=0.78, anchor="center")

    # ── Barra de título del sistema ───────────────────────────
    brand = tk.Frame(root, bg=PRIMARY, height=40)
    brand.pack(fill="x")
    brand.pack_propagate(False)
    tk.Label(brand,
             text="Sistema de Gestión de Identidades",
             font=(FONT, 10, "bold"), bg=PRIMARY, fg="white"
             ).place(relx=0.5, rely=0.5, anchor="center")

    # ── Formulario de acceso ──────────────────────────────────
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True, padx=40, pady=24)

    card = tk.Frame(outer, bg=CARD,
                    highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="both", expand=True)

    inner = tk.Frame(card, bg=CARD)
    inner.pack(fill="both", expand=True, padx=28, pady=22)

    tk.Label(inner, text="Iniciar sesión",
             font=(FONT, 14, "bold"), bg=CARD, fg=TEXT
             ).pack(anchor="w", pady=(0, 14))

    entry_user = _field(inner, "Usuario")
    entry_pass = _field(inner, "Contraseña", show="*")

    tk.Frame(inner, bg=BG, height=4).pack()

    _btn(inner, "Iniciar sesión", login,
         bg=PRIMARY, full=True, pady=11)

    _sep(inner)

    _btn(inner, "Crear cuenta", register,
         bg=NEUTRAL, full=True, pady=10)

    root.bind("<Return>", lambda e: login())
    root.mainloop()
