from datetime import datetime, timezone
from db.database import get_connection

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS firma_route (
    orden        INTEGER PRIMARY KEY,
    coordinador  TEXT NOT NULL,
    definido_en  TEXT,
    definido_por TEXT
)
"""


def _ensure_table(cur, con):
    cur.execute(_CREATE_SQL)
    con.commit()


def get_firma_route():
    """Lista ordenada de coordinadores en la ruta de firma activa."""
    con = get_connection()
    cur = con.cursor()
    _ensure_table(cur, con)
    cur.execute("SELECT coordinador FROM firma_route ORDER BY orden ASC")
    rows = cur.fetchall()
    con.close()
    return [r[0] for r in rows]


def set_firma_route(coordinadores: list, admin_username: str):
    """Reemplaza la ruta completa con la lista ordenada dada."""
    con = get_connection()
    cur = con.cursor()
    _ensure_table(cur, con)
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
