"""Permission-filtered knowledge records, personal views and explicit evidence links."""

import json
import time
import uuid
from fastapi import HTTPException, Request
from portal.search import normalized
from portal.workflows import metadata, outline, version_state

LINK_TYPES = ("cites", "updates", "contradicts", "depends_on", "resolves")


def migrate(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS context_entities(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),kind TEXT NOT NULL,name TEXT NOT NULL,aliases TEXT NOT NULL,properties TEXT NOT NULL,created INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS context_memberships(entity TEXT NOT NULL REFERENCES context_entities(id),artifact TEXT NOT NULL REFERENCES artifacts(id),PRIMARY KEY(entity,artifact));
    CREATE TABLE IF NOT EXISTS context_links(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),source TEXT NOT NULL REFERENCES artifacts(id),target TEXT NOT NULL REFERENCES artifacts(id),version TEXT NOT NULL REFERENCES versions(id),anchor TEXT NOT NULL,quote TEXT NOT NULL,kind TEXT NOT NULL,state TEXT NOT NULL,created INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS context_links_target ON context_links(target);
    CREATE INDEX IF NOT EXISTS context_links_source ON context_links(source);
    CREATE TABLE IF NOT EXISTS context_views(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),kind TEXT NOT NULL,name TEXT NOT NULL,body TEXT NOT NULL,updated INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS context_view_grants(view_id TEXT NOT NULL REFERENCES context_views(id),email TEXT NOT NULL,PRIMARY KEY(view_id,email));
    CREATE INDEX IF NOT EXISTS context_views_owner ON context_views(owner,kind);
    CREATE TABLE IF NOT EXISTS context_dismissals(owner TEXT NOT NULL REFERENCES users(id),source TEXT NOT NULL REFERENCES artifacts(id),target TEXT NOT NULL REFERENCES artifacts(id),PRIMARY KEY(owner,source,target));
    """)


def network(db, rows, user):
    """Edges only when both endpoints are already authorized and in scope."""
    from portal.knowledge import knowledge_network

    result = knowledge_network(rows)
    valid = {r["id"] for r in rows}
    uid = user["id"]
    for entity in db.execute(
        "SELECT * FROM context_entities WHERE owner=? ORDER BY name LIMIT 300", (uid,)
    ):
        members = [
            r["artifact"]
            for r in db.execute(
                "SELECT artifact FROM context_memberships WHERE entity=?",
                (entity["id"],),
            )
            if r["artifact"] in valid
        ]
        if not members:
            continue
        result["nodes"].append(
            {
                "id": "entity:" + entity["id"],
                "title": entity["name"],
                "kind": entity["kind"],
                "count": len(members),
                "entity": entity["id"],
                "aliases": json.loads(entity["aliases"]),
            }
        )
        for aid in members:
            result["edges"].append(
                {
                    "source": aid,
                    "target": "entity:" + entity["id"],
                    "reason": "Assigned " + entity["kind"] + ": " + entity["name"],
                    "kind": "membership",
                }
            )
    placeholders=','.join('?' for _ in valid) or 'NULL'
    for link in db.execute(f"SELECT * FROM context_links WHERE state='confirmed' AND source IN ({placeholders}) AND target IN ({placeholders})",(*valid,*valid)):
        if (
            link["source"] in valid
            and link["target"] in valid
            and version_state(db, link["version"]) != "draft"
        ):
            result["edges"].append(
                {
                    "source": link["source"],
                    "target": link["target"],
                    "reason": link["kind"] + ": " + link["quote"],
                    "kind": link["kind"],
                    "link": link["id"],
                    "version": link["version"],
                    "anchor": link["anchor"],
                }
            )
    return result


def cited_version_readable(db, a, version, u, permissions):
    """Only an explicit confirmed citation exposes a historical published version."""
    if version == a["current_version"] or (u and a["owner"] == u["id"]):
        return True
    if version_state(db, version) == "draft":
        return False
    for row in db.execute(
        "SELECT target FROM context_links WHERE source=? AND version=? AND state='confirmed'",
        (a["id"], version),
    ):
        target = db.execute(
            "SELECT * FROM artifacts WHERE id=?", (row["target"],)
        ).fetchone()
        if target and permissions(db, target, u)["read"]:
            return True
    return False


def mount(app, store, origin, account, payload, clean, artifact_for, permissions):
    def owner(db, aid, u):
        a = artifact_for(db, aid, u, "manage")
        if a["owner"] != u["id"]:
            raise HTTPException(403, "Sólo el creador puede editar estas conexiones.")
        return a

    def authorized(db, u):
        from portal.app import is_admin
        from portal.domain_access import verified_domain
        return {
            r["id"]: dict(r)
            for r in db.execute("SELECT * FROM artifacts WHERE owner=? OR ? OR visibility IN ('public','unlisted') OR id IN (SELECT artifact FROM grants WHERE email=?) OR id IN (SELECT artifact FROM domain_grants WHERE domain=?)",(u["id"],is_admin(u),u.get("email") or "",verified_domain(u)))
            if permissions(db, r, u)["read"]
        }

    def visible_links(db, u, aid=None):
        allowed = authorized(db, u)
        result = []
        for row in db.execute(
            "SELECT * FROM context_links WHERE (? IS NULL OR source=? OR target=?) ORDER BY created DESC LIMIT 5000", (aid,aid,aid)
        ):
            if aid and aid not in (row["source"], row["target"]):
                continue
            if row["source"] not in allowed or row["target"] not in allowed:
                continue
            if row["state"] == "dismissed" or (
                row["state"] != "confirmed" and row["owner"] != u["id"]
            ):
                continue
            source = allowed[row["source"]]
            if (
                version_state(db, row["version"]) == "draft"
                and not permissions(db, source, u)["edit"]
            ):
                continue
            result.append(
                {
                    **dict(row),
                    "source_title": source["title"],
                    "target_title": allowed[row["target"]]["title"],
                    "url": origin
                    + "/a/"
                    + row["source"]
                    + "?version="
                    + row["version"]
                    + "#"
                    + row["anchor"],
                }
            )
        return result

    @app.get("/api/context/links")
    def links(request: Request):
        u = account(request)
        aid = request.query_params.get("artifact")
        with store.db() as db:
            if aid:
                artifact_for(db, aid, u)
            return {"items": visible_links(db, u, aid)}

    @app.post("/api/context/links")
    async def link(request: Request):
        u = account(request)
        body = await payload(request)
        kind = body.get("kind")
        state = body.get("state", "confirmed")
        if kind not in LINK_TYPES or state not in ("proposed", "confirmed"):
            raise HTTPException(422, "Tipo de relación inválido.")
        source = clean(body.get("source"), 32)
        target = clean(body.get("target"), 32)
        if source == target:
            raise HTTPException(422, "Elige dos artefactos distintos.")
        anchor = clean(body.get("anchor", ""), 200, True)
        quote = clean(body.get("quote"), 2000)
        with store.db() as db:
            a = owner(db, source, u)
            artifact_for(db, target, u)
            version = clean(body.get("version", a["current_version"]),120)
            v = db.execute(
                "SELECT * FROM versions WHERE id=? AND artifact=?", (version, source)
            ).fetchone()
            if not v:
                raise HTTPException(404, "Versión no disponible.")
            content = (store.files / (v["sha"] + ".html")).read_text()
            parsed = outline(content)
            scope = parsed.ids.get(anchor, "") if anchor else " ".join(parsed.lines)
            if " ".join(quote.split()) not in scope:
                raise HTTPException(
                    422, "El fragmento no aparece en esa versión y referencia."
                )
            if (
                db.execute(
                    "SELECT count(*) FROM context_links WHERE owner=?", (u["id"],)
                ).fetchone()[0]
                >= 2000
            ):
                raise HTTPException(409, "Máximo 2000 relaciones por cuenta.")
            key = uuid.uuid4().hex
            db.execute(
                "INSERT INTO context_links VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    key,
                    u["id"],
                    source,
                    target,
                    version,
                    anchor,
                    quote,
                    kind,
                    state,
                    int(time.time()),
                ),
            )
        return {"id": key}

    @app.patch("/api/context/links/{key}")
    async def update_link(key: str, request: Request):
        u = account(request)
        body = await payload(request)
        state = body.get("state")
        if state not in ("confirmed", "dismissed"):
            raise HTTPException(422, "Estado inválido.")
        with store.db() as db:
            row = db.execute(
                "SELECT * FROM context_links WHERE id=? AND owner=?", (key, u["id"])
            ).fetchone()
            if not row:
                raise HTTPException(404, "Relación no disponible.")
            owner(db, row["source"], u)
            artifact_for(db, row["target"], u)
            db.execute("UPDATE context_links SET state=? WHERE id=?", (state, key))
        return {"ok": True}

    @app.get("/api/context/entities")
    def entities(request: Request):
        u = account(request)
        with store.db() as db:
            allowed = authorized(db, u)
            items = []
            for row in db.execute(
                "SELECT * FROM context_entities WHERE owner=? ORDER BY name", (u["id"],)
            ):
                members = [
                    allowed[r["artifact"]]
                    for r in db.execute(
                        "SELECT artifact FROM context_memberships WHERE entity=?",
                        (row["id"],),
                    )
                    if r["artifact"] in allowed
                ]
                items.append(
                    {
                        **dict(row),
                        "aliases": json.loads(row["aliases"]),
                        "properties": json.loads(row["properties"]),
                        "artifacts": [
                            {"id": a["id"], "title": a["title"]} for a in members
                        ],
                    }
                )
            return {"items": items}

    @app.post("/api/context/entities")
    async def entity(request: Request):
        u = account(request)
        body = await payload(request)
        kind = body.get("kind")
        name = clean(body.get("name"), 100)
        if kind not in ("company", "project", "topic"):
            raise HTTPException(422, "Tipo de entidad inválido.")
        aliases = body.get("aliases", [])
        props = body.get("properties", {})
        members = body.get("artifacts", [])
        if (
            not isinstance(aliases, list)
            or len(aliases) > 30
            or not isinstance(props, dict)
            or len(props) > 20
            or not isinstance(members, list)
            or len(members) > 200
        ):
            raise HTTPException(422, "Entidad demasiado grande.")
        aliases = list(dict.fromkeys(clean(v, 100) for v in aliases))
        props = {clean(k, 60): clean(v, 300, True) for k, v in props.items()}
        with store.db() as db:
            for aid in members:
                owner(db, clean(aid, 32), u)
            if (
                not body.get("id")
                and db.execute(
                    "SELECT count(*) FROM context_entities WHERE owner=?", (u["id"],)
                ).fetchone()[0]
                >= 200
            ):
                raise HTTPException(409, "Máximo 200 entidades por cuenta.")
            key = clean(body.get("id"),80) if body.get("id") else uuid.uuid4().hex
            if (
                body.get("id")
                and not db.execute(
                    "SELECT 1 FROM context_entities WHERE id=? AND owner=?",
                    (key, u["id"]),
                ).fetchone()
            ):
                raise HTTPException(404, "Entidad no disponible.")
            db.execute(
                "INSERT INTO context_entities VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,name=excluded.name,aliases=excluded.aliases,properties=excluded.properties",
                (
                    key,
                    u["id"],
                    kind,
                    name,
                    json.dumps(aliases),
                    json.dumps(props),
                    int(time.time()),
                ),
            )
            db.execute("DELETE FROM context_memberships WHERE entity=?", (key,))
            for aid in set(members):
                db.execute("INSERT INTO context_memberships VALUES(?,?)", (key, aid))
        return {"id": key}

    @app.get("/api/context/suggestions")
    def suggestions(request: Request):
        u = account(request)
        aid = request.query_params.get("artifact")
        with store.db() as db:
            owner(db, aid, u)
            allowed = authorized(db, u)
            source = db.execute(
                "SELECT body FROM artifact_fts WHERE artifact=?", (aid,)
            ).fetchone()
            text = source["body"] if source else ""
            norm = normalized(text)
            existing = {
                (r["source"], r["target"])
                for r in db.execute(
                    "SELECT source,target FROM context_links WHERE owner=?", (u["id"],)
                )
            }
            dismissed = {
                r["target"]
                for r in db.execute(
                    "SELECT target FROM context_dismissals WHERE owner=? AND source=?",
                    (u["id"], aid),
                )
            }
            items = []
            for target, a in allowed.items():
                title = a["title"]
                needle = normalized(title)
                if (
                    target == aid
                    or len(needle) < 5
                    or (aid, target) in existing
                    or target in dismissed
                ):
                    continue
                at = norm.find(needle)
                if at >= 0:
                    items.append(
                        {
                            "source": aid,
                            "target": target,
                            "title": title,
                            "evidence": text[max(0, at - 90) : at + len(title) + 90],
                            "reason": "Coincidencia literal del título; no confirma una relación.",
                            "state": "proposed",
                        }
                    )
            return {"items": items[:50], "limited": len(items) > 50}

    @app.post("/api/context/suggestions/dismiss")
    async def dismiss(request: Request):
        u = account(request)
        b = await payload(request)
        with store.db() as db:
            owner(db, b.get("source"), u)
            artifact_for(db, b.get("target"), u)
            db.execute(
                "INSERT OR IGNORE INTO context_dismissals VALUES(?,?,?)",
                (u["id"], b["source"], b["target"]),
            )
        return {"ok": True}

    @app.get("/api/context/views")
    def views(request: Request):
        u = account(request)
        with store.db() as db:
            allowed = authorized(db, u)
            items = []
            for row in db.execute(
                "SELECT v.* FROM context_views v WHERE owner=? OR (kind='table' AND EXISTS(SELECT 1 FROM context_view_grants g WHERE g.view_id=v.id AND g.email=?)) ORDER BY updated DESC",
                (u["id"], u["email"]),
            ):
                body = json.loads(row["body"])
                body["items"] = [
                    i
                    for i in body.get("items", [])
                    if i.get("artifact") in allowed or not i.get("artifact")
                ]
                for item in body["items"]:
                    if item.get("artifact"):
                        item["title"] = allowed[item["artifact"]]["title"]
                own=row['owner']==u['id']
                if not own: body={"params":body.get("params",{}),"items":[]}
                items.append({**dict(row), "body": body,"can_manage":own,"shared":not own,"grants":[r['email'] for r in db.execute('SELECT email FROM context_view_grants WHERE view_id=?',(row['id'],))] if own else []})
            return {"items": items}

    @app.put("/api/context/views/{key}")
    async def view(key: str, request: Request):
        u = account(request)
        b = await payload(request)
        kind = b.get("kind")
        name = clean(b.get("name"), 100)
        body = b.get("body", {})
        if (
            len(key) > 80
            or kind not in ("table", "working_set", "board", "graph")
            or not isinstance(body, dict)
            or len(json.dumps(body)) > 100000
        ):
            raise HTTPException(422, "Vista inválida.")
        entries = body.get("items", [])
        if not isinstance(entries, list) or len(entries) > 200:
            raise HTTPException(422, "Máximo 200 elementos.")
        with store.db() as db:
            existing = db.execute(
                "SELECT owner FROM context_views WHERE id=?", (key,)
            ).fetchone()
            if (
                not existing
                and db.execute(
                    "SELECT count(*) FROM context_views WHERE owner=?", (u["id"],)
                ).fetchone()[0]
                >= 100
            ):
                raise HTTPException(409, "Máximo 100 vistas por cuenta.")
            if existing and existing["owner"] != u["id"]:
                raise HTTPException(404, "Vista no disponible.")
            cleaned = []
            for entry in entries:
                if not isinstance(entry, dict):
                    raise HTTPException(422, "Elemento inválido.")
                aid = entry.get("artifact")
                if aid:
                    artifact_for(db, clean(aid, 32), u)
                try:
                    x = float(entry.get("x", 0))
                    y = float(entry.get("y", 0))
                except (TypeError, ValueError):
                    raise HTTPException(422, "Posición inválida.") from None
                if not (-10000 <= x <= 10000 and -10000 <= y <= 10000):
                    raise HTTPException(422, "Posición fuera del tablero.")
                cleaned.append(
                    {
                        "artifact": aid,
                        "text": clean(entry.get("text", ""), 4000, True),
                        "x": x,
                        "y": y,
                    }
                )
            body = {**body, "items": cleaned}
            db.execute(
                "INSERT INTO context_views VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,body=excluded.body,updated=excluded.updated",
                (key, u["id"], kind, name, json.dumps(body), int(time.time())),
            )
        return {"id": key}

    @app.put('/api/context/views/{key}/access')
    async def share_view(key:str,request:Request):
        u=account(request,True);b=await payload(request);emails=b.get('emails',[])
        if not isinstance(emails,list) or len(emails)>30 or any(not isinstance(e,str) or not __import__('re').fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',e) or len(e)>254 for e in emails):raise HTTPException(422,'Correos inválidos.')
        with store.db() as db:
            view=db.execute("SELECT 1 FROM context_views WHERE id=? AND owner=? AND kind='table'",(key,u['id'])).fetchone()
            if not view:raise HTTPException(404)
            db.execute('DELETE FROM context_view_grants WHERE view_id=?',(key,))
            db.executemany('INSERT INTO context_view_grants VALUES(?,?)',[(key,e.strip().lower()) for e in set(emails)])
        return {'saved':True,'scope':'View definition only; artifact permissions are unchanged.'}

    @app.delete("/api/context/views/{key}")
    def delete_view(key: str, request: Request):
        u = account(request)
        with store.db() as db:
            db.execute('DELETE FROM context_view_grants WHERE view_id=? AND EXISTS(SELECT 1 FROM context_views WHERE id=? AND owner=?)',(key,key,u['id']))
            db.execute(
                "DELETE FROM context_views WHERE id=? AND owner=?", (key, u["id"])
            )
        return {"ok": True}

    @app.get("/api/context/sessions")
    def sessions(request: Request):
        u = account(request)
        groups = {}
        with store.db() as db:
            for row in db.execute(
                "SELECT v.id,v.artifact,m.source,m.title FROM versions v JOIN version_meta m ON m.version=v.id JOIN artifacts a ON a.id=v.artifact WHERE a.owner=? ORDER BY v.created DESC LIMIT 2000",
                (u["id"],),
            ):
                source = json.loads(row["source"])
                session = source.get("session")
                if not session:
                    continue
                key = (source.get("agent", ""), session, source.get("device", ""))
                groups.setdefault(key, []).append(
                    {
                        "artifact": row["artifact"],
                        "version": row["id"],
                        "title": row["title"],
                    }
                )
        return {
            "items": [
                {"agent": k[0], "session": k[1], "device": k[2], "outputs": v}
                for k, v in groups.items()
            ]
        }

    @app.post("/api/context/batch")
    async def batch(request: Request):
        u = account(request)
        b = await payload(request)
        ids = b.get("artifacts", [])
        action = b.get("action")
        value = clean(b.get("value", ""), 60, True)
        if (
            not isinstance(ids, list)
            or not ids
            or len(ids) > 200
            or action not in ("tag", "collection", "archive", "restore")
            or (action in ("tag", "collection") and not value)
        ):
            raise HTTPException(422, "Lote inválido.")
        with store.db() as db:
            for aid in ids:
                owner(db, clean(aid, 32), u)
            for aid in set(ids):
                meta = metadata(db, aid)
                if action in ("tag", "collection"):
                    key = "tags" if action == "tag" else "collections"
                    meta[key] = list(dict.fromkeys(meta[key] + [value]))
                    if len(meta[key]) > 20:
                        raise HTTPException(
                            422, "Un artefacto supera las 20 etiquetas o colecciones."
                        )
                else:
                    meta["archived"] = action == "archive"
                db.execute(
                    "INSERT INTO artifact_meta VALUES(?,?,?,?) ON CONFLICT(artifact) DO UPDATE SET tags=excluded.tags,collections=excluded.collections,archived=excluded.archived",
                    (
                        aid,
                        json.dumps(meta["tags"]),
                        json.dumps(meta["collections"]),
                        int(meta["archived"]),
                    ),
                )
                db.execute(
                    "INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)",
                    (u["id"], "batch:" + action, aid, int(time.time())),
                )
        return {"updated": len(set(ids))}
