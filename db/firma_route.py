from datetime import datetime, timezone
from db.database import get_connection


def get_firma_route():
    """Lista ordenada de coordinadores en la ruta de firma activa."""
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT coordinador FROM firma_route ORDER BY orden ASC")
    rows = cur.fetchall()
    con.close()
    return [r[0] for r in rows]


def set_firma_route(coordinadores: list, admin_username: str):
    """Reemplaza la ruta completa con la lista ordenada dada."""
    con = get_connection()
    cur = con.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cur.execute("DELETE FROM firma_route")
    for i, coord in enumerate(coordinadores, start=1):
        cur.execute(
            "INSERT INTO firma_route (orden, coordinador, definido_en, definido_por) "
            "VALUES (?, ?, ?, ?)",
            (i, coord, now, admin_username),
        )
    con.commit()
    con.close()
