import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

from auth.auth import login_user, register_user
from auth.mfa import generate_otp
from auth.permissions import has_permission
from crypto.signature import sign_message, verify_signature, sign_file, verify_file
from db.admin_queries import get_logs
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
        int(r * 0.85), int(g * 0.85), int(b * 0.85)
    )


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


# ── App principal ────────────────────────────────────────────

def start_app():

    def login():
        user     = entry_user.get().strip()
        password = entry_pass.get()
        if not user or not password:
            messagebox.showwarning("Campos vacíos",
                                   "Ingresa usuario y contraseña.", parent=root)
            return
        success, role = login_user(user, password)
        if success:
            otp = generate_otp()
            messagebox.showinfo("Código OTP",
                                f"Tu código de verificación es:\n\n{otp}",
                                parent=root)
            user_otp = simpledialog.askstring(
                "Verificación", "Ingresa el código OTP:", parent=root)
            if user_otp == otp:
                open_dashboard(user, role)
            else:
                messagebox.showerror("OTP incorrecto",
                                     "El código ingresado no es válido.", parent=root)
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
        if register_user(user, password):
            messagebox.showinfo("Registro exitoso",
                                f"Usuario '{user}' creado correctamente.", parent=root)
        else:
            messagebox.showerror("Error",
                                 "El nombre de usuario ya existe.", parent=root)

    def show_certificate(username):
        from config.paths import get_user_dir
        dirs     = get_user_dir(username)
        cert_path = os.path.join(dirs["certs"], f"{username}_cert.json")
        if not os.path.exists(cert_path):
            messagebox.showerror("Error", "No se encontró el certificado.", parent=root)
            return
        with open(cert_path) as f:
            cert = json.load(f)
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

        # padding interior del contenido
        pad = tk.Frame(content, bg=BG, height=16)
        pad.pack()
        inner = tk.Frame(content, bg=BG)
        inner.pack(fill="x", padx=20)
        pad2 = tk.Frame(content, bg=BG, height=16)
        pad2.pack()

        content = inner  # apuntar al frame con padding

        # CONSULTAR — todos los roles
        if has_permission(role, "consult"):
            sec = _card(content, "Identidad Digital")
            _btn(sec, "Ver mi Certificado",
                 lambda: show_certificate(username),
                 bg=PRIMARY, full=True)

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

            def sign():
                msg = entry_message.get()
                if not msg:
                    messagebox.showwarning("Campo vacío",
                                           "Escribe un mensaje primero.", parent=dash)
                    return
                sign_message(username, msg)
                messagebox.showinfo("Firmado",
                                    "Mensaje firmado correctamente.", parent=dash)

            def sign_file_ui():
                path = filedialog.askopenfilename(parent=dash)
                if not path:
                    return
                sign_file(username, path)
                messagebox.showinfo("Firmado",
                                    "Archivo firmado correctamente.", parent=dash)

            _btn(row, "Firmar texto",   sign,         bg=PRIMARY).pack(side="left", padx=(0, 6), pady=2)
            _btn(row, "Firmar archivo", sign_file_ui, bg=NEUTRAL).pack(side="left", pady=2)

        # AUTORIZAR
        if has_permission(role, "authorize"):
            sec = _card(content, "Verificacion de Firmas")
            row2 = tk.Frame(sec, bg=CARD)
            row2.pack(fill="x")

            def verify():
                msg = entry_message.get()
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

        # ADMIN
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

                for user, action, timestamp in get_logs():
                    txt.insert(tk.END, f"{timestamp[:19]}  |  {user:<18}|  {action}\n")
                txt.config(state="disabled")

            _btn(row3, "Gestionar Identidades",
                 lambda: open_admin_panel(username), bg=PRIMARY
                 ).pack(side="left", padx=(0, 6), pady=2)
            _btn(row3, "Ver Logs", view_logs, bg=NEUTRAL
                 ).pack(side="left", pady=2)

        # Footer
        _sep(content)
        _btn(content, "Cerrar sesion", dash.destroy,
             bg=DANGER, full=True, pady=10)

    # ── Ventana de login ─────────────────────────────────────
    root = tk.Tk()
    root.title("Sistema de Identidad Digital")
    root.configure(bg=BG)
    root.resizable(False, False)
    _center(root, 420, 500)

    # Header
    hdr = tk.Frame(root, bg=HDR_BG, height=90)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    tk.Label(hdr, text="Sistema de Gestión de Identidades",
             font=(FONT, 15, "bold"), bg=HDR_BG, fg=HDR_FG
             ).place(relx=0.5, rely=0.38, anchor="center")
    tk.Label(hdr, text=" ",
             font=(FONT, 9), bg=HDR_BG, fg=HDR_SUB
             ).place(relx=0.5, rely=0.72, anchor="center")

    # Card de login
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
