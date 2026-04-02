import tkinter as tk
from tkinter import messagebox, simpledialog
from auth.auth import login_user, register_user
from auth.mfa import generate_otp
from crypto.signature import sign_message, verify_signature


def start_app():

    def center_window(root, width=500, height=400):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        root.geometry(f"{width}x{height}+{x}+{y}")

    # 🔐 LOGIN
    def login():
        user = entry_user.get().strip()
        password = entry_pass.get().strip()

        if not user or not password:
            messagebox.showwarning("Advertencia", "Completa todos los campos")
            return

        if login_user(user, password):
            otp = generate_otp()
            messagebox.showinfo("OTP", f"Tu código es: {otp}")

            user_otp = simpledialog.askstring("Verificación", "Ingresa el código OTP:")

            if user_otp == otp:
                messagebox.showinfo("Acceso", "Login exitoso ✅")
                open_dashboard(user)
            else:
                messagebox.showerror("Error", "OTP incorrecto ❌")
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")

    # 📝 REGISTER
    def register():
        user = entry_user.get().strip()
        password = entry_pass.get().strip()

        if not user or not password:
            messagebox.showwarning("Advertencia", "Completa todos los campos")
            return

        if register_user(user, password):
            messagebox.showinfo("Éxito", "Usuario registrado correctamente")
        else:
            messagebox.showerror("Error", "El usuario ya existe")

    # 📜 MOSTRAR CERTIFICADO
    def show_certificate(username):
        try:
            with open(f"crypto/{username}_cert.json", "r") as f:
                cert = f.read()

            messagebox.showinfo("Certificado", cert)
        except:
            messagebox.showerror("Error", "No se encontró el certificado")

    # 🖥️ DASHBOARD
    def open_dashboard(username):
        dashboard = tk.Toplevel()
        dashboard.title("Dashboard")

        center_window(dashboard, 450, 400)

        tk.Label(dashboard, text=f"Bienvenid@ {username}",
                 font=("Arial", 14)).pack(pady=10)

        tk.Button(dashboard, text="Ver Certificado", width=20,
                  command=lambda: show_certificate(username)).pack(pady=5)

        # 📩 Campo de mensaje
        tk.Label(dashboard, text="Mensaje a firmar").pack(pady=5)
        entry_message = tk.Entry(dashboard, width=30)
        entry_message.pack()

        # 🔐 Firmar
        def sign():
            message = entry_message.get()

            if not message:
                messagebox.showwarning("Error", "Escribe un mensaje")
                return

            sign_message(username, message)
            messagebox.showinfo("Firma", "Mensaje firmado correctamente")

        # 🔍 Verificar
        def verify():
            message = entry_message.get()

            if not message:
                messagebox.showwarning("Error", "Escribe un mensaje")
                return

            if verify_signature(username, message):
                messagebox.showinfo("Verificación", "Firma válida ✅")
            else:
                messagebox.showerror("Verificación", "Firma inválida ❌")

        tk.Button(dashboard, text="Firmar", command=sign).pack(pady=5)
        tk.Button(dashboard, text="Verificar Firma", command=verify).pack(pady=5)

        tk.Button(dashboard, text="Cerrar sesión",
                  command=dashboard.destroy).pack(pady=10)

    # 🖥️ VENTANA PRINCIPAL
    root = tk.Tk()
    root.title("Sistema Casa Monarca")

    center_window(root, 500, 400)
    root.resizable(False, False)
    root.configure(bg="#f0f0f0")

    tk.Label(root, text="Sistema de Identidad Digital",
             font=("Arial", 16, "bold"),
             bg="#f0f0f0").pack(pady=20)

    tk.Label(root, text="Usuario", bg="#f0f0f0").pack(pady=5)
    entry_user = tk.Entry(root, width=30)
    entry_user.pack()

    tk.Label(root, text="Contraseña", bg="#f0f0f0").pack(pady=5)
    entry_pass = tk.Entry(root, show="*", width=30)
    entry_pass.pack()

    tk.Button(root, text="Login", width=20, command=login).pack(pady=15)
    tk.Button(root, text="Registrar", width=20, command=register).pack()

    root.mainloop()