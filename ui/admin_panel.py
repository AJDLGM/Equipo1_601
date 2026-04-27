import tkinter as tk
from tkinter import ttk, messagebox

from client.api_client import get_client

# ── Paleta (misma que login_window) ─────────────────────────
BG       = "#F1F5F9"
CARD     = "#FFFFFF"
HDR_BG   = "#0F172A"
HDR_FG   = "#F8FAFC"
HDR_SUB  = "#94A3B8"
PRIMARY  = "#2563EB"
DANGER   = "#DC2626"
SUCCESS  = "#16A34A"
NEUTRAL  = "#475569"
TEXT     = "#0F172A"
SUBTEXT  = "#64748B"
BORDER   = "#E2E8F0"
DIVIDER  = "#F8FAFC"

FONT = "Segoe UI"


# ── Helpers ──────────────────────────────────────────────────

def _center(win, w, h):
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


def _darken(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r * 0.85), int(g * 0.85), int(b * 0.85))


def _btn(parent, text, cmd, bg=PRIMARY, fg="white", full=False, pady=8, width=None):
    kw = {}
    if width:
        kw["width"] = width
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg,
        activebackground=_darken(bg), activeforeground=fg,
        relief="flat", cursor="hand2",
        font=(FONT, 10, "bold"),
        padx=14, pady=pady, bd=0, **kw,
    )
    b.bind("<Enter>", lambda e: b.config(bg=_darken(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    if full:
        b.pack(fill="x", pady=3)
    return b


def _field_row(parent, label, show="", width=28):
    tk.Label(parent, text=label, font=(FONT, 9),
             bg=CARD, fg=SUBTEXT).pack(anchor="w")
    frame = tk.Frame(parent, bg=CARD,
                     highlightbackground=BORDER, highlightthickness=1)
    frame.pack(fill="x", pady=(2, 10))
    e = tk.Entry(frame, relief="flat", font=(FONT, 10), show=show,
                 bg=CARD, fg=TEXT, insertbackground=TEXT,
                 bd=0, highlightthickness=0, width=width)
    e.pack(fill="x", padx=10, pady=7)
    return e


def _section_header(parent, text):
    f = tk.Frame(parent, bg=DIVIDER, height=34)
    f.pack(fill="x")
    f.pack_propagate(False)
    tk.Label(f, text=f"  {text}", font=(FONT, 9, "bold"),
             bg=DIVIDER, fg=SUBTEXT).pack(side="left", padx=4)


def _userlist(parent, height=6):
    frame = tk.Frame(parent, bg=CARD,
                     highlightbackground=BORDER, highlightthickness=1)
    frame.pack(fill="x", pady=(2, 10))
    sb = tk.Scrollbar(frame, orient="vertical")
    lb = tk.Listbox(
        frame, height=height,
        yscrollcommand=sb.set,
        exportselection=False,
        relief="flat", bd=0,
        font=(FONT, 10),
        bg=CARD, fg=TEXT,
        selectbackground=PRIMARY,
        selectforeground="white",
        activestyle="none",
    )
    sb.config(command=lb.yview)
    sb.pack(side="right", fill="y")
    lb.pack(side="left", fill="x", expand=True, padx=4, pady=4)
    return lb


# ── Panel principal ──────────────────────────────────────────

def open_admin_panel(admin_username):

    win = tk.Toplevel()
    win.title("Panel de Administrador")
    win.configure(bg=BG)
    win.resizable(False, False)
    _center(win, 680, 580)

    hdr = tk.Frame(win, bg=HDR_BG, height=60)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    tk.Label(hdr, text="Panel de Administrador",
             font=(FONT, 14, "bold"), bg=HDR_BG, fg=HDR_FG
             ).place(relx=0.5, rely=0.38, anchor="center")
    tk.Label(hdr, text=f"Sesion: {admin_username}",
             font=(FONT, 8), bg=HDR_BG, fg=HDR_SUB
             ).place(relx=0.5, rely=0.74, anchor="center")

    style = ttk.Style()
    style.theme_use("default")
    style.configure("Admin.TNotebook",
                    background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
    style.configure("Admin.TNotebook.Tab",
                    font=(FONT, 10, "bold"),
                    padding=[18, 8],
                    background="#E2E8F0",
                    foreground=SUBTEXT)
    style.map("Admin.TNotebook.Tab",
              background=[("selected", CARD)],
              foreground=[("selected", PRIMARY)])

    nb = ttk.Notebook(win, style="Admin.TNotebook")
    nb.pack(fill="both", expand=True, padx=0, pady=0)

    tab_alta = tk.Frame(nb, bg=BG)
    tab_rev  = tk.Frame(nb, bg=BG)
    tab_baja = tk.Frame(nb, bg=BG)

    nb.add(tab_alta, text="  Alta  ")
    nb.add(tab_rev,  text="  Revocacion  ")
    nb.add(tab_baja, text="  Baja  ")

    rev_refresher = [None]

    refresh_baja = _build_baja(tab_baja, admin_username,
                               on_deactivate=lambda: rev_refresher[0] and rev_refresher[0]())
    refresh_rev  = _build_revocacion(tab_rev, admin_username, on_revoke=refresh_baja)
    rev_refresher[0] = refresh_rev

    _build_alta(tab_alta, admin_username,
                on_register=lambda: (refresh_rev(), refresh_baja()))


# ── RF01: Alta de identidad ──────────────────────────────────

def _build_alta(parent, admin_username, on_register=None):
    api = get_client()

    outer = tk.Frame(parent, bg=BG)
    outer.pack(fill="both", expand=True, padx=24, pady=20)

    card = tk.Frame(outer, bg=CARD,
                    highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="x")

    _section_header(card, "Registrar nueva identidad digital")

    body = tk.Frame(card, bg=CARD)
    body.pack(fill="x", padx=20, pady=16)

    body.columnconfigure(0, weight=1)
    body.columnconfigure(1, weight=1)

    def lbl(text, row, col):
        tk.Label(body, text=text, font=(FONT, 9), bg=CARD, fg=SUBTEXT
                 ).grid(row=row, column=col, sticky="w", pady=(0, 2))

    def entry_grid(row, col, show=""):
        f = tk.Frame(body, bg=CARD,
                     highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=row + 1, column=col, sticky="ew",
               padx=(0, 10) if col == 0 else (10, 0), pady=(0, 12))
        e = tk.Entry(f, relief="flat", font=(FONT, 10), show=show,
                     bg=CARD, fg=TEXT, bd=0, highlightthickness=0)
        e.pack(fill="x", padx=10, pady=7)
        return e

    lbl("Usuario",              0, 0)
    lbl("Rol",                  0, 1)
    e_user = entry_grid(0, 0)

    role_var = tk.StringVar(value="externo")
    role_frame = tk.Frame(body, bg=CARD,
                          highlightbackground=BORDER, highlightthickness=1)
    role_frame.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 12))
    role_cb = ttk.Combobox(
        role_frame, textvariable=role_var,
        values=["externo", "operativo", "coordinador", "admin"],
        state="readonly", font=(FONT, 10),
    )
    role_cb.pack(fill="x", padx=6, pady=6)

    lbl("Contrasena",           2, 0)
    lbl("Confirmar contrasena", 2, 1)
    e_pass  = entry_grid(2, 0, show="*")
    e_pass2 = entry_grid(2, 1, show="*")

    msg_var = tk.StringVar()
    msg_lbl = tk.Label(body, textvariable=msg_var,
                       font=(FONT, 9, "bold"), bg=CARD)
    msg_lbl.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 8))

    def do_register():
        username = e_user.get().strip()
        password = e_pass.get()
        password2 = e_pass2.get()
        role      = role_var.get()

        msg_lbl.config(fg=DANGER)
        if not username or not password:
            msg_var.set("Usuario y contrasena son obligatorios.")
            return
        if len(password) < 6:
            msg_var.set("La contrasena debe tener al menos 6 caracteres.")
            return
        if password != password2:
            msg_var.set("Las contrasenias no coinciden.")
            return

        if api.admin_create_user(username, password, role):
            msg_lbl.config(fg=SUCCESS)
            msg_var.set(f"Identidad '{username}' registrada correctamente.")
            e_user.delete(0, tk.END)
            e_pass.delete(0, tk.END)
            e_pass2.delete(0, tk.END)
            role_var.set("externo")
            if on_register:
                on_register()
        else:
            msg_var.set(f"El usuario '{username}' ya existe.")

    btn = _btn(body, "Registrar Identidad", do_register,
               bg=SUCCESS, pady=10)
    btn.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(4, 0))


# ── RF02: Revocacion de identidad ────────────────────────────

def _build_revocacion(parent, admin_username, on_revoke=None):
    api = get_client()

    outer = tk.Frame(parent, bg=BG)
    outer.pack(fill="both", expand=True, padx=24, pady=20)

    top_card = tk.Frame(outer, bg=CARD,
                        highlightbackground=BORDER, highlightthickness=1)
    top_card.pack(fill="x", pady=(0, 12))
    _section_header(top_card, "Revocar certificado digital")

    top_body = tk.Frame(top_card, bg=CARD)
    top_body.pack(fill="x", padx=20, pady=14)

    tk.Label(top_body, text="Selecciona un usuario activo:",
             font=(FONT, 9), bg=CARD, fg=SUBTEXT).pack(anchor="w")
    user_list = _userlist(top_body, height=4)

    def refresh_users():
        user_list.delete(0, tk.END)
        for uname, role in api.get_active_users():
            if uname != admin_username:
                user_list.insert(tk.END, f"  {uname:<22} [{role}]")

    refresh_users()

    e_reason = _field_row(top_body, "Motivo de revocacion:")

    def do_revoke():
        sel = user_list.curselection()
        if not sel:
            messagebox.showwarning("Sin seleccion",
                                   "Selecciona un usuario.", parent=top_card.winfo_toplevel())
            return
        username = user_list.get(sel[0]).strip().split()[0]
        reason   = e_reason.get().strip()
        if not reason:
            messagebox.showwarning("Motivo requerido",
                                   "Ingresa el motivo de revocacion.", parent=top_card.winfo_toplevel())
            return
        if messagebox.askyesno(
            "Confirmar revocacion",
            f"Revocar el certificado de '{username}'?\n\nMotivo: {reason}",
            parent=top_card.winfo_toplevel(),
        ):
            api.revoke_identity(username, reason, admin_username)
            messagebox.showinfo(
                "Certificado revocado",
                f"El certificado de '{username}' fue revocado\n"
                "y agregado a la CRL.",
                parent=top_card.winfo_toplevel(),
            )
            e_reason.delete(0, tk.END)
            refresh_users()
            refresh_crl()
            if on_revoke:
                on_revoke()

    _btn(top_body, "Revocar Certificado", do_revoke,
         bg=DANGER, full=True, pady=9)

    bot_card = tk.Frame(outer, bg=CARD,
                        highlightbackground=BORDER, highlightthickness=1)
    bot_card.pack(fill="both", expand=True)
    _section_header(bot_card, "Lista de Revocacion (CRL)")

    bot_body = tk.Frame(bot_card, bg=CARD)
    bot_body.pack(fill="both", expand=True, padx=12, pady=10)

    style = ttk.Style()
    style.configure("CRL.Treeview",
                    font=(FONT, 9), rowheight=26,
                    background=CARD, fieldbackground=CARD,
                    foreground=TEXT, borderwidth=0)
    style.configure("CRL.Treeview.Heading",
                    font=(FONT, 9, "bold"),
                    background=DIVIDER, foreground=SUBTEXT, relief="flat")
    style.map("CRL.Treeview", background=[("selected", "#DBEAFE")])

    cols = ("Usuario", "Motivo", "Fecha (UTC)", "Revocado por")
    tree = ttk.Treeview(bot_body, columns=cols, show="headings",
                        height=5, style="CRL.Treeview")
    for col, w in zip(cols, (130, 200, 155, 130)):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="w")

    vsb = ttk.Scrollbar(bot_body, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    def refresh_crl():
        for row in tree.get_children():
            tree.delete(row)
        for uname, reason, revoked_at, revoked_by in api.get_revoked_certs():
            tree.insert("", "end",
                        values=(uname, reason, revoked_at[:19], revoked_by))

    refresh_crl()

    def _auto_refresh():
        try:
            refresh_users()
            refresh_crl()
        except tk.TclError:
            return
        outer.after(10000, _auto_refresh)

    outer.after(10000, _auto_refresh)

    return refresh_users


# ── RF03: Baja de identidad ──────────────────────────────────

def _build_baja(parent, admin_username, on_deactivate=None):
    api = get_client()

    outer = tk.Frame(parent, bg=BG)
    outer.pack(fill="both", expand=True, padx=24, pady=20)

    card = tk.Frame(outer, bg=CARD,
                    highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="both", expand=True)

    _section_header(card, "Dar de baja una identidad")

    body = tk.Frame(card, bg=CARD)
    body.pack(fill="both", expand=True, padx=20, pady=16)

    warn = tk.Frame(body, bg="#FEF2F2",
                    highlightbackground="#FECACA", highlightthickness=1)
    warn.pack(fill="x", pady=(0, 14))
    tk.Label(
        warn,
        text="  Esta accion desactiva permanentemente la identidad y revoca su certificado.\n"
             "  El registro se conserva en la base de datos con fines de auditoria.",
        font=(FONT, 9), bg="#FEF2F2", fg="#991B1B",
        justify="left",
    ).pack(anchor="w", padx=8, pady=8)

    tk.Label(body, text="Usuarios en el sistema (activos y revocados):",
             font=(FONT, 9), bg=CARD, fg=SUBTEXT).pack(anchor="w")
    user_list = _userlist(body, height=10)

    STATUS_ES = {"active": "activo", "revoked": "revocado", "inactive": "inactivo"}

    def refresh_users():
        user_list.delete(0, tk.END)
        for uname, role, status in api.get_all_users_with_status():
            if uname != admin_username and status != "inactive":
                label = STATUS_ES.get(status, status)
                user_list.insert(
                    tk.END, f"  {uname:<22} [{role:<12}]  —  {label}")

    refresh_users()

    def do_deactivate():
        sel = user_list.curselection()
        if not sel:
            messagebox.showwarning("Sin seleccion",
                                   "Selecciona un usuario.", parent=card.winfo_toplevel())
            return
        username = user_list.get(sel[0]).strip().split()[0]
        if messagebox.askyesno(
            "Confirmar baja",
            f"Dar de baja permanentemente a '{username}'?\n\n"
            "Se bloqueara el acceso y se revocara el certificado.\n"
            "Esta accion no se puede deshacer.",
            parent=card.winfo_toplevel(),
            icon="warning",
        ):
            api.deactivate_user(username, admin_username)
            messagebox.showinfo(
                "Baja realizada",
                f"La identidad '{username}' fue dada de baja del sistema.",
                parent=card.winfo_toplevel(),
            )
            refresh_users()
            if on_deactivate:
                on_deactivate()

    _btn(body, "Dar de Baja", do_deactivate,
         bg=DANGER, full=True, pady=10)

    def _auto_refresh():
        try:
            refresh_users()
        except tk.TclError:
            return
        outer.after(10000, _auto_refresh)

    outer.after(10000, _auto_refresh)

    return refresh_users
