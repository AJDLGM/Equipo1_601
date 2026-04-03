import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

from auth.auth import login_user, register_user
from auth.mfa import generate_otp
from auth.permissions import has_permission

from crypto.signature import sign_message, verify_signature, sign_file, verify_file

from db.admin_queries import get_all_users, update_user_role, get_logs


def start_app():

    def center_window(root, width=500, height=400):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        root.geometry(f"{width}x{height}+{x}+{y}")

    # LOGIN
    def login():

        user = entry_user.get().strip()
        password = entry_pass.get().strip()

        success, role = login_user(user, password)

        if success:

            otp = generate_otp()
            messagebox.showinfo("OTP", f"Tu código es: {otp}")

            user_otp = simpledialog.askstring("Verificación", "Ingresa el código OTP:")

            if user_otp == otp:

                messagebox.showinfo("Acceso", "Login exitoso")

                open_dashboard(user, role)

            else:
                messagebox.showerror("Error", "OTP incorrecto")

        else:
            messagebox.showerror("Error", "Credenciales incorrectas")

    # REGISTER
    def register():

        user = entry_user.get().strip()
        password = entry_pass.get().strip()

        if register_user(user, password):
            messagebox.showinfo("Éxito", "Usuario registrado")
        else:
            messagebox.showerror("Error", "El usuario ya existe")

    # MOSTRAR CERTIFICADO
    def show_certificate(username):

        cert_path = f"crypto/{username}_cert.json"

        if not os.path.exists(cert_path):
            messagebox.showerror("Error", "No existe certificado")
            return

        with open(cert_path) as f:
            cert = json.load(f)

        cert_text = (
            f"Usuario: {cert['user']}\n\n"
            f"Issued At: {cert['issued_at']}\n\n"
            f"Expires At: {cert['expires_at']}\n\n"
            f"Signature: {cert['signature']}"
        )

        messagebox.showinfo("Certificado", cert_text)

    # DASHBOARD
    def open_dashboard(username, role):

        dashboard = tk.Toplevel()
        dashboard.title("Dashboard")

        center_window(dashboard, 450, 500)

        tk.Label(dashboard, text=f"Bienvenido {username}", font=("Arial", 14)).pack(pady=10)

        tk.Label(dashboard, text=f"Rol: {role}", font=("Arial", 10)).pack(pady=5)

        # CONSULTAR
        if has_permission(role, "consult"):

            tk.Button(
                dashboard,
                text="Ver Certificado",
                command=lambda: show_certificate(username)
            ).pack(pady=5)

        # EDITAR
        if has_permission(role, "edit"):

            tk.Label(dashboard, text="Mensaje a firmar").pack(pady=5)

            entry_message = tk.Entry(dashboard, width=30)
            entry_message.pack()

            def sign():

                message = entry_message.get()

                if not message:
                    messagebox.showwarning("Error", "Escribe un mensaje")
                    return

                sign_message(username, message)

                messagebox.showinfo("Firma", "Mensaje firmado")

            tk.Button(
                dashboard,
                text="Firmar Texto",
                command=sign
            ).pack(pady=5)

            def sign_file_ui():

                file_path = filedialog.askopenfilename()

                if not file_path:
                    return

                sign_file(username, file_path)

                messagebox.showinfo("Firma", "Archivo firmado")

            tk.Button(
                dashboard,
                text="Firmar Archivo",
                command=sign_file_ui
            ).pack(pady=5)

        # AUTORIZAR
        if has_permission(role, "authorize"):

            def verify():

                message = entry_message.get()

                signature_file = filedialog.askopenfilename(
                    filetypes=[("Signature", "*.sig")]
                )

                if verify_signature(username, message, signature_file):
                    messagebox.showinfo("Verificación", "Firma válida")
                else:
                    messagebox.showerror("Verificación", "Firma inválida")

            tk.Button(
                dashboard,
                text="Verificar Texto",
                command=verify
            ).pack(pady=5)

            def verify_file_ui():

                file_path = filedialog.askopenfilename()

                if verify_file(username, file_path):
                    messagebox.showinfo("Verificación", "Firma válida")
                else:
                    messagebox.showerror("Verificación", "Firma inválida")

            tk.Button(
                dashboard,
                text="Verificar Archivo",
                command=verify_file_ui
            ).pack(pady=5)

        # ADMIN
        if role == "admin":

            tk.Label(
                dashboard,
                text="Panel de Administrador",
                font=("Arial", 12, "bold")
            ).pack(pady=10)

            tk.Button(
                dashboard,
                text="Administrar Usuarios",
                command=open_admin_panel
            ).pack(pady=5)

            tk.Button(
                dashboard,
                text="Ver Logs del Sistema",
                command=view_logs
            ).pack(pady=5)

        tk.Button(
            dashboard,
            text="Cerrar sesión",
            command=dashboard.destroy
        ).pack(pady=15)
        
        def open_admin_panel():

            admin_window = tk.Toplevel()
            admin_window.title("Administración de Usuarios")

            users = get_all_users()

            for user, role in users:

                frame = tk.Frame(admin_window)
                frame.pack(pady=5)

                tk.Label(frame, text=user, width=15).pack(side="left")
                tk.Label(frame, text=role, width=15).pack(side="left")

                def make_admin(u=user):
                    update_user_role(u, "admin")
                    messagebox.showinfo("Actualizado", f"{u} ahora es admin")

                tk.Button(
                    frame,
                    text="Hacer Admin",
                    command=make_admin
                ).pack(side="left")
        
        def view_logs():

            log_window = tk.Toplevel()
            log_window.title("Logs del Sistema")

            logs = get_logs()

            text = tk.Text(log_window, width=80, height=25)
            text.pack()

            for user, action, timestamp in logs:

                line = f"{timestamp} | {user} | {action}\n"

                text.insert(tk.END, line)        
                        

    # VENTANA PRINCIPAL
    root = tk.Tk()

    root.title("Sistema Casa Monarca")

    center_window(root)

    tk.Label(root, text="Sistema de Identidad Digital", font=("Arial", 16)).pack(pady=20)

    tk.Label(root, text="Usuario").pack()

    entry_user = tk.Entry(root)
    entry_user.pack()

    tk.Label(root, text="Contraseña").pack()

    entry_pass = tk.Entry(root, show="*")
    entry_pass.pack()

    tk.Button(root, text="Login", command=login).pack(pady=10)

    tk.Button(root, text="Registrar", command=register).pack()

    root.mainloop()