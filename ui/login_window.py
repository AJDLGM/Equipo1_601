import tkinter as tk
from tkinter import messagebox
from auth.auth import login_user, register_user
from auth.mfa import generate_otp

def start_app():

    # 🔹 Función para centrar ventana
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
            print("OTP:", otp)  # simulación en consola

            messagebox.showinfo("OTP", f"Tu código es: {otp}")
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

    # 🖥️ VENTANA PRINCIPAL
    root = tk.Tk()
    root.title("Sistema Casa Monarca")

    center_window(root, 500, 400)
    root.resizable(False, False)
    root.configure(bg="#f0f0f0")

    # 🔹 Título
    tk.Label(root, text="Sistema de Identidad Digital",
             font=("Arial", 16, "bold"),
             bg="#f0f0f0").pack(pady=20)

    # 🔹 Usuario
    tk.Label(root, text="Usuario", bg="#f0f0f0").pack(pady=5)
    entry_user = tk.Entry(root, width=30)
    entry_user.pack()

    # 🔹 Contraseña
    tk.Label(root, text="Contraseña", bg="#f0f0f0").pack(pady=5)
    entry_pass = tk.Entry(root, show="*", width=30)
    entry_pass.pack()

    # 🔹 Botones
    tk.Button(root, text="Login", width=20, command=login).pack(pady=15)
    tk.Button(root, text="Registrar", width=20, command=register).pack()

    root.mainloop()