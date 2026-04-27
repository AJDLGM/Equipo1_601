import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from auth.permissions import has_permission
from crypto.signature import sign_message, verify_signature, sign_file, verify_file
from client.api_client import get_client
from ui.admin_panel import open_admin_panel

# ── Paleta de colores ────────────────────────────────────────
BG       = "#F1F5F9"
CARD     = "#FFFFFF"
HDR_BG   = "#0F172A"
HDR_FG   = "#F8FAFC"
HDR_SUB  = "#94A3B8"
PRIMARY  = "#2563EB"
PRIMARY_H= "#1D4ED8"
DANGER   = "#DC2626"
DANGER_H = "#B91C1C"
SUCCESS  = "#16A34A"
SUCCESS_H= "#15803D"
NEUTRAL  = "#475569"
NEUTRAL_H= "#334155"
TEXT     = "#0F172A"
SUBTEXT  = "#64748B"
BORDER   = "#E2E8F0"
DIVIDER  = "#F8FAFC"

ROLE_BADGE = {
    "admin":       ("#EDE9FE", "#6D28D9"),
    "coordinador": ("#DBEAFE", "#1D4ED8"),
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


# ── Sincronizacion de claves locales ─────────────────────────

def _has_local_keys(username):
    """Verifica si el usuario ya tiene sus claves descargadas localmente."""
    from config.paths import USERS_DIR
    priv = os.path.join(USERS_DIR, username, "keys", f"{username}_private.pem")
    return os.path.exists(priv)


def _sync_local_keys(username, dirs, api):
    """Descarga claves y certificado del servidor al cache local."""
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
            messagebox.showwarning("Campos vacios",
                                   "Ingresa usuario y contrasena.", parent=root)
            return
        success, role = api.login(user, password)
        if success:
            open_dashboard(user, role)
        elif role == "pending":
            messagebox.showwarning(
                "Cuenta pendiente",
                "Tu cuenta esta pendiente de aprobacion\n"
                "por el administrador.", parent=root)
        else:
            messagebox.showerror(
                "Acceso denegado",
                "Usuario o contrasena incorrectos,\n"
                "o la cuenta esta desactivada.", parent=root)

    def register():
        user     = entry_user.get().strip()
        password = entry_pass.get()
        if not user or not password:
            messagebox.showwarning("Campos vacios",
                                   "Ingresa usuario y contrasena.", parent=root)
            return
        if api.register(user, password):
            messagebox.showinfo(
                "Solicitud enviada",
                f"Tu cuenta '{user}' fue creada.\n\n"
                "Esta pendiente de aprobacion por el administrador.\n"
                "Podras iniciar sesion una vez que sea activada.", parent=root)
        else:
            messagebox.showerror("Error",
                                 "El nombre de usuario ya existe.", parent=root)

    def show_certificate(username):
        cert = api.get_cert(username)
        if not cert:
            messagebox.showerror("Error", "No se encontro el certificado.", parent=root)
            return
        status = cert.get("status", "active").upper()
        reason = cert.get("revocation_reason", "—")
        messagebox.showinfo(
            "Certificado Digital",
            f"Usuario      : {cert['user']}\n"
            f"Emitido      : {cert['issued_at'][:19]}\n"
            f"Expira       : {cert['expires_at'][:19]}\n"
            f"Estado       : {status}\n"
            f"Motivo rev.  : {reason}\n\n"
            f"Hash         : {cert['signature'][:40]}...",
        )

    def open_dashboard(username, role):
        _pending_job = [None]

        dash = tk.Toplevel()
        dash.title("Dashboard")
        dash.configure(bg=BG)
        dash.resizable(False, False)
        _center(dash, 500, 600)

        # ── Header ──────────────────────────────────────────
        hdr = tk.Frame(dash, bg=HDR_BG, height=72)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text=f"Bienvenido, {username}",
                 font=(FONT, 13, "bold"), bg=HDR_BG, fg=HDR_FG
                 ).place(x=20, rely=0.28, anchor="w")

        badge_bg, badge_fg = ROLE_BADGE.get(role, ("#E2E8F0", NEUTRAL))
        tk.Label(hdr, text=f"  {role.upper()}  ",
                 font=(FONT, 8, "bold"), bg=badge_bg, fg=badge_fg,
                 padx=4, pady=2
                 ).place(x=20, rely=0.72, anchor="w")

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
                    "Ingresa tu contrasena para descargar las credenciales:",
                    show="*", parent=dash)
                if not pwd:
                    return

                if not api.verify_password(username, pwd):
                    messagebox.showerror("Contrasena incorrecta",
                                         "La contrasena ingresada no es valida.", parent=dash)
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
                    "Usa tu contrasena de cuenta para abrirlo.", parent=dash)

            _btn(sec, "Descargar Certificado y Claves",
                 download_credentials, bg=NEUTRAL, full=True)

        # EDITAR
        if has_permission(role, "edit"):
            sec = _card(content, "Firma Digital")

            tk.Label(sec, text="Mensaje a firmar:",
                     font=(FONT, 9), bg=CARD, fg=SUBTEXT).pack(anchor="w")
            msg_wrap = tk.Frame(sec, bg=CARD,
                                highlightbackground=BORDER, highlightthickness=1)
            msg_wrap.pack(fill="x", pady=(2, 10))
            entry_message = tk.Entry(
                msg_wrap, relief="flat", font=(FONT, 10),
                bg=CARD, fg=TEXT, bd=0, highlightthickness=0,
            )
            entry_message.pack(fill="x", padx=10, pady=7)

            row = tk.Frame(sec, bg=CARD)
            row.pack(fill="x")

            def _check_keys(parent_win):
                if not _has_local_keys(username):
                    messagebox.showwarning(
                        "Credenciales no encontradas",
                        "Primero descarga tus credenciales usando el boton\n"
                        "'Descargar Certificado y Claves'.",
                        parent=parent_win)
                    return False
                return True

            def sign():
                msg = entry_message.get()
                if not msg:
                    messagebox.showwarning("Campo vacio",
                                           "Escribe un mensaje primero.", parent=dash)
                    return
                if not _check_keys(dash):
                    return
                sign_message(username, msg)
                messagebox.showinfo("Firmado",
                                    "Mensaje firmado correctamente.", parent=dash)

            def sign_file_ui():
                path = filedialog.askopenfilename(parent=dash)
                if not path:
                    return
                if not _check_keys(dash):
                    return
                sign_file(username, path)
                messagebox.showinfo("Firmado",
                                    "Archivo firmado correctamente.", parent=dash)

            _btn(row, "Firmar texto",   sign,         bg=PRIMARY).pack(side="left", padx=(0, 6), pady=2)
            _btn(row, "Firmar archivo", sign_file_ui, bg=NEUTRAL).pack(side="left", pady=2)

        # AUTORIZAR
        if has_permission(role, "authorize"):
            sec = _card(content, "Verificacion de Firmas")

            tk.Label(sec, text="Mensaje a verificar:",
                     font=(FONT, 9), bg=CARD, fg=SUBTEXT).pack(anchor="w")
            verify_wrap = tk.Frame(sec, bg=CARD,
                                   highlightbackground=BORDER, highlightthickness=1)
            verify_wrap.pack(fill="x", pady=(2, 10))
            entry_verify_msg = tk.Entry(
                verify_wrap, relief="flat", font=(FONT, 10),
                bg=CARD, fg=TEXT, bd=0, highlightthickness=0,
            )
            entry_verify_msg.pack(fill="x", padx=10, pady=7)

            row2 = tk.Frame(sec, bg=CARD)
            row2.pack(fill="x")

            def verify():
                if not _check_keys(dash):
                    return
                msg = entry_verify_msg.get()
                sig = filedialog.askopenfilename(
                    parent=dash, filetypes=[("Firma", "*.sig")])
                if not sig:
                    return
                if verify_signature(username, msg, sig):
                    messagebox.showinfo("Valida", "La firma es valida.", parent=dash)
                else:
                    messagebox.showerror("Invalida",
                                         "La firma no es valida o fue alterada.", parent=dash)

            def verify_file_ui():
                if not _check_keys(dash):
                    return
                path = filedialog.askopenfilename(parent=dash)
                if not path:
                    return
                if verify_file(username, path):
                    messagebox.showinfo("Valida", "La firma es valida.", parent=dash)
                else:
                    messagebox.showerror("Invalida",
                                         "La firma no es valida o fue alterada.", parent=dash)

            _btn(row2, "Verificar texto",   verify,          bg=SUCCESS).pack(side="left", padx=(0, 6), pady=2)
            _btn(row2, "Verificar archivo", verify_file_ui,  bg=SUCCESS).pack(side="left", pady=2)

        # ADMIN — Solicitudes pendientes
        if role == "admin":
            sec_pending = _card(content, "Solicitudes de Activacion Pendientes")

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
                    messagebox.showwarning("Sin seleccion",
                                           "Selecciona una cuenta para aprobar.", parent=dash)
                    return
                uname = pending_lb.get(sel[0]).strip().split()[0]

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

            def _auto_refresh_pending():
                try:
                    refresh_pending()
                except tk.TclError:
                    return
                _pending_job[0] = dash.after(10000, _auto_refresh_pending)

            _auto_refresh_pending()
            _btn(sec_pending, "Aprobar cuenta seleccionada", do_approve,
                 bg=SUCCESS, full=True, pady=9)

        # ADMIN — Logs y panel
        if role == "admin":
            sec = _card(content, "Administracion del Sistema")
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
                    txt.insert(tk.END, f"{timestamp[:19]}  |  {user:<18}|  {action}\n")
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

        _btn(content, "Cerrar sesion", logout,
             bg=DANGER, full=True, pady=10)

    # ── Ventana de login ─────────────────────────────────────
    root = tk.Tk()
    root.title("Sistema de Identidad Digital")
    root.configure(bg=BG)
    root.resizable(False, False)
    _center(root, 420, 500)

    hdr = tk.Frame(root, bg=HDR_BG, height=90)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    tk.Label(hdr, text="Sistema de Gestion de Identidades",
             font=(FONT, 15, "bold"), bg=HDR_BG, fg=HDR_FG
             ).place(relx=0.5, rely=0.38, anchor="center")
    tk.Label(hdr, text=" ",
             font=(FONT, 9), bg=HDR_BG, fg=HDR_SUB
             ).place(relx=0.5, rely=0.72, anchor="center")

    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True, padx=40, pady=28)

    card = tk.Frame(outer, bg=CARD,
                    highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="both", expand=True)

    inner = tk.Frame(card, bg=CARD)
    inner.pack(fill="both", expand=True, padx=28, pady=24)

    tk.Label(inner, text="Iniciar sesion",
             font=(FONT, 14, "bold"), bg=CARD, fg=TEXT
             ).pack(anchor="w", pady=(0, 16))

    entry_user = _field(inner, "Usuario")
    entry_pass = _field(inner, "Contrasena", show="*")

    tk.Frame(inner, bg=BG, height=4).pack()

    _btn(inner, "Iniciar sesion", login,
         bg=PRIMARY, full=True, pady=11)

    _sep(inner)

    _btn(inner, "Crear cuenta", register,
         bg=NEUTRAL, full=True, pady=10)

    root.bind("<Return>", lambda e: login())
    root.mainloop()
