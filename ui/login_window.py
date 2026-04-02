import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from auth.auth import login_user, register_user
from auth.mfa import generate_otp
from crypto.signature import sign_message, verify_signature
from tkinter import filedialog
from crypto.signature import sign_file, verify_file

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
            if not os.path.exists(f"crypto/{username}_private.pem"):
                raise Exception("No existen claves para este usuario")

            with open(f"crypto/{username}_private.pem", "rb") as f:
                private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
            
    #DASHBOARD
    def open_dashboard(username):
        from tkinter import filedialog

        dashboard = tk.Toplevel()
        dashboard.title("Dashboard")

        center_window(dashboard, 450, 500)

        tk.Label(dashboard, text=f"Bienvenid@ {username}",
                font=("Arial", 14)).pack(pady=10)

        tk.Button(dashboard, text="Ver Certificado",
                command=lambda: show_certificate(username)).pack(pady=5)

        # 📩 Campo de mensaje
        tk.Label(dashboard, text="Mensaje a firmar").pack(pady=5)
        entry_message = tk.Entry(dashboard, width=30)
        entry_message.pack()

        # 🔐 Firmar texto
        def sign():
            message = entry_message.get()

            if not message:
                messagebox.showwarning("Error", "Escribe un mensaje")
                return

            sign_message(username, message)
            messagebox.showinfo("Firma", "Mensaje firmado correctamente")

        # 🔍 Verificar texto
        def verify():
            message = entry_message.get()

            if not message:
                messagebox.showwarning("Error", "Escribe un mensaje")
                return

            if verify_signature(username, message):
                messagebox.showinfo("Verificación", "Firma válida ✅")
            else:
                messagebox.showerror("Verificación", "Firma inválida ❌")

        tk.Button(dashboard, text="Firmar Texto", command=sign).pack(pady=5)
        tk.Button(dashboard, text="Verificar Texto", command=verify).pack(pady=5)

        # =========================
        # 🔥 BOTONES DE ARCHIVO
        # =========================

        def sign_file_ui():
            file_path = filedialog.askopenfilename()

            if not file_path:
                return

            sign_file(username, file_path)
            messagebox.showinfo("Firma", "Archivo firmado correctamente")

        def verify_file_ui():
            file_path = filedialog.askopenfilename()

            if not file_path:
                return

            if verify_file(username, file_path):
                messagebox.showinfo("Verificación", "Firma válida ✅")
            else:
                messagebox.showerror("Verificación", "Firma inválida ❌")

        tk.Button(dashboard, text="Firmar Archivo",
                command=sign_file_ui).pack(pady=5)

        tk.Button(dashboard, text="Verificar Archivo",
                command=verify_file_ui).pack(pady=5)

        # =========================

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