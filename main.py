import tkinter as tk
from tkinter import messagebox, simpledialog

from config.paths import create_directories
from config.server_config import get_server_url, save_server_url
from client.api_client import init_client


def _ask_server_url(current_url=""):
    root = tk.Tk()
    root.withdraw()

    while True:
        url = simpledialog.askstring(
            "Conectar al servidor",
            "Ingresa la URL del servidor:\n\n"
            "  Ejemplo (mismo equipo):  http://localhost:5000\n"
            "  Ejemplo (otra PC):       http://192.168.1.5:5000",
            initialvalue=current_url or "http://localhost:5000",
            parent=root,
        )
        if url is None:
            messagebox.showerror(
                "Requerido",
                "La URL del servidor es necesaria para continuar.",
                parent=root,
            )
            continue

        api = init_client(url.strip())
        if api.ping():
            save_server_url(url.strip())
            break

        retry = messagebox.askretrycancel(
            "Sin conexion",
            f"No se pudo conectar a:\n{url}\n\n"
            "Verifica que el servidor este activo y la URL sea correcta.",
            parent=root,
        )
        if not retry:
            root.destroy()
            raise SystemExit("No se pudo conectar al servidor.")

    root.destroy()


if __name__ == "__main__":
    create_directories()

    saved_url = get_server_url()
    api = init_client(saved_url) if saved_url else None

    if not api or not api.ping():
        _ask_server_url(saved_url)

    from ui.login_window import start_app
    start_app()
