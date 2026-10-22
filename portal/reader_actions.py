"""Guardar y «me gusta» por cuenta: estado deseado, idempotente y filtrado por permisos actuales.

Las mutaciones sólo aceptan la sesión de navegador de una cuenta verificada (cookie
`__Host-` + Origin del portal, que valida el middleware) y la cabecera propia
`X-Margen-Reader-Action`, que un formulario o un iframe opaco no pueden enviar.
El cuerpo nunca elige la cuenta: siempre actúa quien tiene la sesión.
La lectura nunca expone quién guardó o marcó; sólo el total de cuentas que hoy
pueden leer el artefacto y lo marcaron.

Montaje (portal/app.py, dentro de create_app, junto a los otros mount_*):
    from portal.reader_actions import mount as mount_reader_actions
    mount_reader_actions(app, store, who, account, payload, artifact_for, permissions)
y en merge_admin_aliases, en la lista de UPDATE OR IGNORE por `user`: 'reader_saves', 'reader_likes'.
"""

import time

from fastapi import HTTPException, Request

HEADER = "x-margen-reader-action"
SAVED_PATH = "/?view=saved"
MAX_SAVED = 2000
MAX_LISTED = MAX_SAVED


def migrate(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS reader_saves(user TEXT NOT NULL REFERENCES users(id),artifact TEXT NOT NULL REFERENCES artifacts(id),created INTEGER NOT NULL,PRIMARY KEY(user,artifact));
    CREATE INDEX IF NOT EXISTS reader_saves_recent ON reader_saves(user,created);
    CREATE TABLE IF NOT EXISTS reader_likes(user TEXT NOT NULL REFERENCES users(id),artifact TEXT NOT NULL REFERENCES artifacts(id),created INTEGER NOT NULL,PRIMARY KEY(user,artifact));
    CREATE INDEX IF NOT EXISTS reader_likes_artifact ON reader_likes(artifact);
    """)


def like_count(db, artifact, permissions):
    """Cuenta sólo marcas de cuentas verificadas que todavía pueden leer el artefacto."""
    count = 0
    for row in db.execute(
        "SELECT u.* FROM reader_likes l JOIN users u ON u.id=l.user WHERE l.artifact=? AND u.verified=1",
        (artifact["id"],),
    ):
        if permissions(db, artifact, dict(row))["read"]:
            count += 1
    return count


def state(db, artifact, user, permissions):
    uid = user["id"] if user else None
    mine = lambda table: bool(uid and db.execute(
        f"SELECT 1 FROM {table} WHERE user=? AND artifact=?", (uid, artifact["id"])).fetchone())
    can_act = bool(user and user["verified"] and not user.get("agent"))
    return {
        "artifact": artifact["id"],
        "saved": mine("reader_saves") if can_act else False,
        "liked": mine("reader_likes") if can_act else False,
        "likes": like_count(db, artifact, permissions),
        "signed_in": bool(user and user["verified"]),
        "can_act": can_act,
        "saved_path": SAVED_PATH,
    }


def desired(body):
    if not body or not set(body) <= {"saved", "liked"}:
        raise HTTPException(422, "Indica sólo saved o liked con true o false.")
    if any(not isinstance(v, bool) for v in body.values()):
        raise HTTPException(422, "saved y liked aceptan true o false.")
    return body


def mount(app, store, who, account, payload, artifact_for, permissions):
    with store.db() as db:
        migrate(db)

    @app.get("/api/artifacts/{aid}/reader-actions")
    def reader_state(aid: str, request: Request):
        u = who(request)
        with store.db() as db:
            a = artifact_for(db, aid, u)
            return state(db, a, u, permissions)

    @app.put("/api/artifacts/{aid}/reader-actions")
    async def reader_update(aid: str, request: Request):
        if request.headers.get(HEADER) != "1":
            raise HTTPException(403, "Acción del lector sin confirmar desde el portal.")
        u = account(request, browser=True)
        body = desired(await payload(request))
        now = int(time.time())
        with store.db() as db:
            a = artifact_for(db, aid, u)
            for key, table in (("saved", "reader_saves"), ("liked", "reader_likes")):
                if key not in body:
                    continue
                if not body[key]:
                    db.execute(f"DELETE FROM {table} WHERE user=? AND artifact=?", (u["id"], aid))
                    continue
                if key == "saved" and db.execute(
                    "SELECT count(*) FROM reader_saves WHERE user=?", (u["id"],)
                ).fetchone()[0] >= MAX_SAVED and not db.execute(
                    "SELECT 1 FROM reader_saves WHERE user=? AND artifact=?", (u["id"], aid)
                ).fetchone():
                    raise HTTPException(409, f"Máximo {MAX_SAVED} documentos guardados.")
                db.execute(f"INSERT OR IGNORE INTO {table} VALUES(?,?,?)", (u["id"], aid, now))
            return state(db, a, u, permissions)

    @app.get("/api/reader/saved")
    def saved(request: Request):
        u = account(request)
        rows = []
        with store.db() as db:
            for s in db.execute(
                "SELECT s.created AS saved,a.* FROM reader_saves s JOIN artifacts a ON a.id=s.artifact WHERE s.user=? ORDER BY s.created DESC,s.rowid DESC",
                (u["id"],),
            ):
                a = dict(s)
                saved_at = a.pop("saved")
                # El permiso se evalúa hoy: una revocación oculta el guardado sin borrarlo.
                if not permissions(db, a, u)["read"]:
                    continue
                rows.append({"id": a["id"], "title": a["title"], "space": a["space"],
                             "updated": a["updated"], "saved": saved_at, "url": "/a/" + a["id"]})
                if len(rows) >= MAX_LISTED:
                    break
        return {"artifacts": rows, "total": len(rows), "saved_path": SAVED_PATH}
