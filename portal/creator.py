"""Creator-owned decisions, revision assignments and inspectable learning records."""

import hashlib
import json
import secrets
import time
import uuid
from datetime import date
from fastapi import HTTPException, Request
from portal.workflows import context_for, prompt_bundle, compare, version_state

STATES = {
    "prepared": {"queued", "cancelled"},
    "queued": {"cancelled"},
    "received": {"working", "failed", "cancelled"},
    "working": {"proposed", "failed", "cancelled", "waiting"},
    "waiting": {"working", "failed", "cancelled", "queued"},
    "failed": {"queued", "cancelled"},
    "proposed": {"accepted", "queued", "cancelled"},
    "accepted": set(),
    "cancelled": set(),
}


def migrate(db):
    from portal.memory import migrate as migrate_memory

    migrate_memory(db)
    from portal.job_leases import migrate as migrate_leases

    migrate_leases(db)
    db.executescript(
        """
    CREATE TABLE IF NOT EXISTS creator_decisions(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),project TEXT NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,state TEXT NOT NULL,review_on TEXT NOT NULL,updated INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS creator_decision_history(id INTEGER PRIMARY KEY,decision TEXT NOT NULL REFERENCES creator_decisions(id),actor TEXT NOT NULL,record TEXT NOT NULL,at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS creator_decisions_owner ON creator_decisions(owner,project,updated);
    CREATE TABLE IF NOT EXISTS creator_jobs(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),artifact TEXT NOT NULL REFERENCES artifacts(id),base_version TEXT NOT NULL REFERENCES versions(id),title TEXT NOT NULL,target TEXT NOT NULL,packet TEXT NOT NULL,status TEXT NOT NULL,result TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1,created INTEGER NOT NULL,updated INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS creator_jobs_owner ON creator_jobs(owner,status,updated);
    CREATE TABLE IF NOT EXISTS creator_receipts(id INTEGER PRIMARY KEY,job TEXT NOT NULL REFERENCES creator_jobs(id),state TEXT NOT NULL,actor TEXT NOT NULL,detail TEXT NOT NULL,at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS creator_connectors(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),label TEXT NOT NULL,agent TEXT NOT NULL,device TEXT NOT NULL,token_hash TEXT NOT NULL UNIQUE,seen INTEGER NOT NULL DEFAULT 0,revoked INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS creator_rules(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),project TEXT NOT NULL,rule TEXT NOT NULL,source TEXT NOT NULL,active INTEGER NOT NULL,updated INTEGER NOT NULL);
    """
    )


def mount(
    app,
    store,
    origin,
    account,
    payload,
    clean,
    artifact_for,
    permissions,
    threads,
    snapshot,
):
    def owned(db, aid, u):
        a = artifact_for(db, aid, u, "manage")
        if a["owner"] != u["id"]:
            raise HTTPException(404, "Proyecto no disponible.")
        return a

    def job_for(db, key, u):
        row = db.execute(
            "SELECT * FROM creator_jobs WHERE id=? AND owner=?", (key, u["id"])
        ).fetchone()
        if not row:
            raise HTTPException(404, "Encargo no disponible.")
        owned(db, row["artifact"], u)
        return dict(row)

    def evidence(db, values, u):
        if not isinstance(values, list) or len(values) > 30:
            raise HTTPException(422, "Selecciona hasta 30 evidencias.")
        out = []
        for e in values:
            if not isinstance(e, dict):
                raise HTTPException(422, "Evidencia inválida.")
            aid = clean(e.get("artifact"), 32)
            a = owned(db, aid, u)
            vid = clean(e.get("version") or a["current_version"], 120)
            v = db.execute(
                "SELECT sha FROM versions WHERE id=? AND artifact=?", (vid, aid)
            ).fetchone()
            if not v:
                raise HTTPException(404, "Versión no disponible.")
            quote = clean(e.get("quote", ""), 2000, True)
            from portal.search import extract_text

            if quote and " ".join(quote.split()) not in " ".join(
                extract_text((store.files / (v["sha"] + ".html")).read_text()).split()
            ):
                raise HTTPException(422, "La cita no coincide con esa versión.")
            out.append(
                {"artifact": aid, "version": vid, "title": a["title"], "quote": quote}
            )
        return out

    def inspect_decision(db, r, u):
        value = {**dict(r), **json.loads(r["body"])}
        value.pop("body", None)
        current = []
        for e in value["evidence"]:
            a = owned(db, e["artifact"], u)
            current.append(
                {
                    **e,
                    "current_version": a["current_version"],
                    "changed": a["current_version"] != e["version"],
                    "materiality": __import__(
                        "portal.memory", fromlist=["materiality"]
                    ).materiality(store, db, e, a["current_version"]),
                    "url": origin + "/a/" + a["id"] + "?version=" + e["version"],
                }
            )
        value["evidence"] = current
        value["needs_review"] = any(
            e["materiality"]
            in (
                "cited_text_changed",
                "quoted_text_preserved",
                "unassessed",
                "unavailable",
            )
            for e in current
        ) or bool(value["review_on"] and value["review_on"] <= date.today().isoformat())
        return value

    def inspect_job(db, r):
        j = dict(r)
        lease = db.execute(
            "SELECT heartbeat,expires,stopped FROM job_leases WHERE job=?", (j["id"],)
        ).fetchone()
        j["execution"] = dict(lease) if lease else None
        j["target"] = json.loads(j["target"])
        j["result"] = json.loads(j["result"])
        j.pop("packet", None)
        j["receipts"] = [
            dict(x)
            for x in db.execute(
                "SELECT state,actor,detail,at FROM creator_receipts WHERE job=? ORDER BY id",
                (j["id"],),
            )
        ]
        return j

    @app.get("/api/creator")
    def dashboard(request: Request):
        u = account(request)
        project = request.query_params.get("project", "")
        with store.db() as db:
            from portal.job_leases import expire

            expire(db)
            artifacts = [
                dict(r)
                for r in db.execute(
                    "SELECT id,title,space,current_version,updated FROM artifacts WHERE owner=? ORDER BY updated DESC",
                    (u["id"],),
                )
            ]
            counts = {}
            for a in artifacts:
                counts[a["space"]] = counts.get(a["space"], 0) + 1
            decisions = [
                inspect_decision(db, r, u)
                for r in db.execute(
                    "SELECT * FROM creator_decisions WHERE owner=? AND (?='' OR project=?) ORDER BY updated DESC LIMIT 200",
                    (u["id"], project, project),
                )
            ]
            jobs = [
                inspect_job(db, r)
                for r in db.execute(
                    "SELECT j.* FROM creator_jobs j JOIN artifacts a ON a.id=j.artifact WHERE j.owner=? AND (?='' OR a.space=?) ORDER BY j.updated DESC LIMIT 200",
                    (u["id"], project, project),
                )
            ]
            connectors = [
                dict(r)
                for r in db.execute(
                    "SELECT id,label,agent,device,seen,revoked FROM creator_connectors WHERE owner=?",
                    (u["id"],),
                )
            ]
            rules = [
                dict(r)
                for r in db.execute(
                    "SELECT id,project,rule,source,active,updated FROM creator_rules WHERE owner=? AND (?='' OR project='' OR project=?) ORDER BY updated DESC",
                    (u["id"], project, project),
                )
            ]
        return {
            "projects": [
                {"name": k, "artifacts": v} for k, v in sorted(counts.items())
            ],
            "artifacts": [a for a in artifacts if not project or a["space"] == project],
            "decisions": decisions,
            "jobs": jobs,
            "connectors": connectors,
            "rules": rules,
            "limits": {"decisions": 200, "jobs": 200},
        }

    @app.post("/api/creator/decisions")
    async def save_decision(request: Request):
        u = account(request, True)
        b = await payload(request)
        key = clean(b.get("id") or uuid.uuid4().hex, 32)
        state = b.get("state", "proposed")
        if state not in ("proposed", "accepted", "superseded", "rejected"):
            raise HTTPException(422, "Estado inválido.")
        review = clean(b.get("review_on", ""), 10, True)
        if review:
            try:
                date.fromisoformat(review)
            except ValueError:
                raise HTTPException(422, "Fecha inválida.")
        with store.db() as db:
            old = db.execute(
                "SELECT owner FROM creator_decisions WHERE id=?", (key,)
            ).fetchone()
            if old and old["owner"] != u["id"]:
                raise HTTPException(404)
            refs = evidence(db, b.get("evidence", []), u)
            if state == "accepted" and not refs:
                raise HTTPException(422, "Una decisión aceptada necesita evidencia.")
            body = {
                k: clean(b.get(k, ""), 4000, True)
                for k in (
                    "rationale",
                    "alternatives",
                    "expected",
                    "uncertainty",
                    "outcome",
                )
            }
            body["evidence"] = refs
            db.execute(
                "INSERT INTO creator_decisions VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET project=excluded.project,title=excluded.title,body=excluded.body,state=excluded.state,review_on=excluded.review_on,updated=excluded.updated",
                (
                    key,
                    u["id"],
                    clean(b.get("project", "Personal"), 60),
                    clean(b.get("title"), 200),
                    json.dumps(body),
                    state,
                    review,
                    int(time.time()),
                ),
            )
            db.execute(
                "INSERT INTO creator_decision_history(decision,actor,record,at) VALUES(?,?,?,?)",
                (
                    key,
                    u["id"],
                    json.dumps(
                        dict(
                            db.execute(
                                "SELECT * FROM creator_decisions WHERE id=?", (key,)
                            ).fetchone()
                        )
                    ),
                    int(time.time()),
                ),
            )
        return {"id": key}

    @app.get("/api/creator/decisions/{key}/history")
    def decision_history(key: str, request: Request):
        u = account(request)
        with store.db() as db:
            if not db.execute(
                "SELECT 1 FROM creator_decisions WHERE id=? AND owner=?", (key, u["id"])
            ).fetchone():
                raise HTTPException(404)
            return {
                "items": [
                    dict(r)
                    for r in db.execute(
                        "SELECT actor,record,at FROM creator_decision_history WHERE decision=? ORDER BY id DESC LIMIT 100",
                        (key,),
                    )
                ]
            }

    @app.post("/api/creator/rules")
    async def save_rule(request: Request):
        u = account(request, True)
        b = await payload(request)
        key = clean(b.get("id") or uuid.uuid4().hex, 32)
        if not isinstance(b.get("active", True), bool):
            raise HTTPException(422, "Estado inválido.")
        with store.db() as db:
            old = db.execute(
                "SELECT owner FROM creator_rules WHERE id=?", (key,)
            ).fetchone()
            if old and old["owner"] != u["id"]:
                raise HTTPException(404)
            source = evidence(db, b.get("source", []), u)
            db.execute(
                "INSERT INTO creator_rules VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET project=excluded.project,rule=excluded.rule,source=excluded.source,active=excluded.active,updated=excluded.updated",
                (
                    key,
                    u["id"],
                    clean(b.get("project", ""), 60, True),
                    clean(b.get("rule"), 2000),
                    json.dumps(source),
                    int(b.get("active", True)),
                    int(time.time()),
                ),
            )
        return {"id": key}

    @app.delete("/api/creator/rules/{key}")
    def delete_rule(key: str, request: Request):
        u = account(request, True)
        with store.db() as db:
            db.execute(
                "DELETE FROM creator_rules WHERE id=? AND owner=?", (key, u["id"])
            )
        return {"ok": True}

    @app.post("/api/creator/jobs")
    async def create_job(request: Request):
        u = account(request)
        b = await payload(request)
        ids = b.get("threads", [])
        if (
            not isinstance(ids, list)
            or len(ids) > 200
            or any(not isinstance(x, str) for x in ids)
        ):
            raise HTTPException(422, "Selección inválida.")
        include = b.get("include_notes", False)
        if not isinstance(include, bool):
            raise HTTPException(422, "Privacidad inválida.")
        with store.db() as db:
            a = owned(db, clean(b.get("artifact"), 32), u)
            base = a["current_version"]
            items = []
            for t in threads(snapshot(db, a, u)["events"]):
                if t["thread"] not in ids:
                    continue
                if t.get("entry_type") == "note" and not include:
                    raise HTTPException(
                        422, "Selecciona explícitamente incluir tus notas."
                    )
                items.append(
                    {
                        "artifact": a["id"],
                        "title": a["title"],
                        "space": a["space"],
                        "thread": t,
                        "context": context_for(store, db, a, t, origin),
                    }
                )
            if set(ids) != {i["thread"]["thread"] for i in items}:
                raise HTTPException(404, "Uno de los hilos no está disponible.")
            target = b.get("target", {})
            if not isinstance(target, dict):
                raise HTTPException(422, "Destino inválido.")
            target = {
                k: clean(target.get(k, ""), 200, True)
                for k in ("agent", "device", "session", "connector")
            }
            if target["connector"]:
                c = db.execute(
                    "SELECT * FROM creator_connectors WHERE id=? AND owner=? AND revoked=0",
                    (target["connector"], u["id"]),
                ).fetchone()
                if not c:
                    raise HTTPException(404, "Conector no disponible.")
                target.update(agent=c["agent"], device=c["device"])
            rules = [
                {"id": r["id"], "rule": r["rule"]}
                for r in db.execute(
                    "SELECT id,rule FROM creator_rules WHERE owner=? AND active=1 AND project IN (?,'')",
                    (u["id"], a["space"]),
                )
            ]
            instructions = clean(b.get("instructions", ""), 8000, True)
            packet = {
                "format": "margen-assignment/1",
                "artifact": a["id"],
                "document_id": a["document_id"],
                "base_version": base,
                "url": origin + "/a/" + a["id"],
                "target": target,
                "items": items,
                "rules": rules,
                "instructions": instructions,
                "text": prompt_bundle(items),
                "policy": "Create a draft and report evidence for each addressed thread. Never publish or resolve feedback from this assignment.",
            }
            key = uuid.uuid4().hex
            now = int(time.time())
            db.execute(
                "INSERT INTO creator_jobs VALUES(?,?,?,?,?,?,?,?,?,1,?,?)",
                (
                    key,
                    u["id"],
                    a["id"],
                    base,
                    clean(b.get("title") or a["title"], 200),
                    json.dumps(target),
                    json.dumps(packet),
                    "prepared",
                    "{}",
                    now,
                    now,
                ),
            )
            db.execute(
                "INSERT INTO creator_receipts(job,state,actor,detail,at) VALUES(?,?,?,?,?)",
                (
                    key,
                    "prepared",
                    u["id"],
                    "Contexto seleccionado por el creador.",
                    now,
                ),
            )
        return {"id": key, "status": "prepared"}

    @app.get("/api/creator/jobs/{key}")
    def get_job(key: str, request: Request):
        u = account(request)
        with store.db() as db:
            j = job_for(db, key, u)
            return {**inspect_job(db, j), "packet": json.loads(j["packet"])}

    @app.post("/api/creator/jobs/{key}/state")
    async def job_state(key: str, request: Request):
        u = account(request, True)
        b = await payload(request)
        with store.db() as db:
            j = job_for(db, key, u)
            state = b.get("status")
            if state not in STATES[j["status"]] or state in ("working", "proposed"):
                raise HTTPException(409, "Transición no disponible.")
            if b.get("revision") != j["revision"]:
                raise HTTPException(409, "El encargo cambió; vuelve a abrirlo.")
            if state == "queued":
                lease = db.execute(
                    "SELECT * FROM job_leases WHERE job=?", (key,)
                ).fetchone()
                if (
                    lease
                    and not lease["stopped"]
                    and lease["expires"] > int(time.time())
                ):
                    raise HTTPException(
                        409,
                        "El intento anterior sigue activo; espera su detención o el vencimiento.",
                    )
                target = json.loads(j["target"])
                if not db.execute(
                    "SELECT 1 FROM creator_connectors WHERE id=? AND owner=? AND revoked=0",
                    (target.get("connector"), u["id"]),
                ).fetchone():
                    raise HTTPException(
                        422, "Selecciona un conector activo al preparar el encargo."
                    )
            db.execute(
                "UPDATE creator_jobs SET status=?,revision=revision+1,updated=? WHERE id=?",
                (state, int(time.time()), key),
            )
            db.execute(
                "INSERT INTO creator_receipts(job,state,actor,detail,at) VALUES(?,?,?,?,?)",
                (
                    key,
                    state,
                    u["id"],
                    clean(b.get("detail", ""), 2000, True),
                    int(time.time()),
                ),
            )
        return {"status": state}

    @app.get("/api/creator/jobs/{key}/comparison")
    def comparison(key: str, request: Request):
        u = account(request)
        with store.db() as db:
            j = job_for(db, key, u)
            result = json.loads(j["result"])
            vid = result.get("version")
            versions = [
                db.execute(
                    "SELECT sha FROM versions WHERE id=? AND artifact=?",
                    (v, j["artifact"]),
                ).fetchone()
                for v in (j["base_version"], vid)
            ]
            if not all(versions):
                raise HTTPException(
                    404, "El encargo aún no tiene una propuesta de versión."
                )
            return {
                **compare(
                    *[
                        (store.files / (v["sha"] + ".html")).read_text()
                        for v in versions
                    ]
                ),
                "threads": result.get("threads", []),
                "version": vid,
                "current_changed": owned(db, j["artifact"], u)["current_version"]
                != j["base_version"],
            }

    @app.post("/api/creator/connectors")
    async def connector_create(request: Request):
        u = account(request, True)
        b = await payload(request)
        token = secrets.token_urlsafe(40)
        key = uuid.uuid4().hex
        agent = clean(b.get("agent"), 60)
        if agent not in ("Codex", "Claude", "Hermes"):
            raise HTTPException(422, "Agente no compatible.")
        with store.db() as db:
            db.execute(
                "INSERT INTO creator_connectors(id,owner,label,agent,device,token_hash) VALUES(?,?,?,?,?,?)",
                (
                    key,
                    u["id"],
                    clean(b.get("label"), 120),
                    agent,
                    clean(b.get("device"), 200),
                    hashlib.sha256(token.encode()).hexdigest(),
                ),
            )
        return {
            "id": key,
            "token": token,
            "server": origin,
            "scope": "assigned-jobs-only",
        }

    @app.delete("/api/creator/connectors/{key}")
    def connector_revoke(key: str, request: Request):
        u = account(request, True)
        with store.db() as db:
            db.execute(
                "UPDATE creator_connectors SET revoked=1 WHERE id=? AND owner=?",
                (key, u["id"]),
            )
        return {"ok": True}

    def connector(db, request):
        auth = request.headers.get("authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else ""
        c = db.execute(
            "SELECT * FROM creator_connectors WHERE token_hash=? AND revoked=0",
            (hashlib.sha256(token.encode()).hexdigest(),),
        ).fetchone()
        if not c:
            raise HTTPException(401, "Conector revocado o inválido.")
        db.execute(
            "UPDATE creator_connectors SET seen=? WHERE id=?",
            (int(time.time()), c["id"]),
        )
        return dict(c)

    @app.get("/api/connector/pending")
    def pending(request: Request):
        with store.db() as db:
            c = connector(db, request)
            return {
                "jobs": [
                    r["id"]
                    for r in db.execute(
                        "SELECT id FROM creator_jobs WHERE owner=? AND status='received' AND json_extract(target,'$.connector')=? ORDER BY created",
                        (c["owner"], c["id"]),
                    )
                ]
            }

    @app.post("/api/connector/claim")
    async def claim(request: Request):
        with store.db() as db:
            c = connector(db, request)
            r = db.execute(
                "SELECT * FROM creator_jobs WHERE owner=? AND status='queued' AND json_extract(target,'$.connector')=? ORDER BY created LIMIT 1",
                (c["owner"], c["id"]),
            ).fetchone()
            if not r:
                return {"job": None}
            changed = db.execute(
                "UPDATE creator_jobs SET status='received',revision=revision+1,updated=? WHERE id=? AND status='queued'",
                (int(time.time()), r["id"]),
            ).rowcount
            if not changed:
                return {"job": None}
            db.execute(
                "INSERT INTO creator_receipts(job,state,actor,detail,at) VALUES(?,?,?,?,?)",
                (
                    r["id"],
                    "received",
                    c["id"],
                    "Conector autenticado recibió el encargo.",
                    int(time.time()),
                ),
            )
            return {
                "job": r["id"],
                "packet": json.loads(r["packet"]),
                "revision": r["revision"] + 1,
            }

    @app.post("/api/connector/jobs/{key}/report")
    async def report(key: str, request: Request):
        b = await payload(request)
        with store.db() as db:
            c = connector(db, request)
            u = dict(
                db.execute("SELECT * FROM users WHERE id=?", (c["owner"],)).fetchone()
            )
            j = job_for(db, key, u)
            if json.loads(j["target"]).get("connector") != c["id"]:
                raise HTTPException(404)
            state = b.get("status")
            if (
                state not in ("working", "waiting", "failed", "proposed")
                or state not in STATES[j["status"]]
            ):
                raise HTTPException(409, "Transición inválida.")
            if b.get("revision") != j["revision"]:
                raise HTTPException(409, "El encargo cambió.")
            result = {"summary": clean(b.get("summary", ""), 4000, True)}
            if state == "proposed":
                vid = clean(b.get("version"), 120)
                if not db.execute(
                    "SELECT 1 FROM versions v JOIN version_meta m ON m.version=v.id WHERE v.id=? AND v.artifact=? AND m.state='draft' AND json_extract(m.source,'$.label')=?",
                    (vid, j["artifact"], "Margen assignment " + key),
                ).fetchone():
                    raise HTTPException(
                        422,
                        "La propuesta debe ser una versión borrador del mismo artefacto.",
                    )
                selected = {
                    i["thread"]["thread"] for i in json.loads(j["packet"])["items"]
                }
                updates = b.get("threads", [])
                if not isinstance(updates, list) or len(updates) > 200:
                    raise HTTPException(422, "Resultados inválidos.")
                result.update(version=vid, threads=[])
                for item in updates:
                    if (
                        not isinstance(item, dict)
                        or item.get("id") not in selected
                        or item.get("status")
                        not in ("addressed", "blocked", "unchanged")
                    ):
                        raise HTTPException(422, "Resultado de hilo inválido.")
                    result["threads"].append(
                        {
                            "id": item["id"],
                            "status": item["status"],
                            "explanation": clean(item.get("explanation"), 2000),
                        }
                    )
                if (
                    len(result["threads"]) != len(selected)
                    or {t["id"] for t in result["threads"]} != selected
                ):
                    raise HTTPException(
                        422,
                        "Reporta una vez cada hilo seleccionado, incluso si quedó bloqueado o sin cambios.",
                    )
            db.execute(
                "UPDATE creator_jobs SET status=?,result=?,revision=revision+1,updated=? WHERE id=?",
                (state, json.dumps(result), int(time.time()), key),
            )
            db.execute(
                "INSERT INTO creator_receipts(job,state,actor,detail,at) VALUES(?,?,?,?,?)",
                (key, state, c["id"], result["summary"], int(time.time())),
            )
        return {"status": state, "revision": j["revision"] + 1}

    def connector_job(db, request, key):
        c = connector(db, request)
        u = dict(db.execute("SELECT * FROM users WHERE id=?", (c["owner"],)).fetchone())
        j = job_for(db, key, u)
        if json.loads(j["target"]).get("connector") != c["id"] or j["status"] not in (
            "received",
            "working",
            "proposed",
        ):
            raise HTTPException(404, "Encargo no disponible para este conector.")
        return c, u, j

    @app.get("/api/connector/jobs/{key}")
    def connector_context(key: str, request: Request):
        with store.db() as db:
            c, u, j = connector_job(db, request, key)
            v = db.execute(
                "SELECT sha FROM versions WHERE id=? AND artifact=?",
                (j["base_version"], j["artifact"]),
            ).fetchone()
            return {
                "job": key,
                "revision": j["revision"],
                "status": j["status"],
                "packet": json.loads(j["packet"]),
                "html": (store.files / (v["sha"] + ".html")).read_text(),
            }

    @app.post("/api/connector/jobs/{key}/draft")
    async def connector_draft(key: str, request: Request):
        import re

        b = await payload(request)
        content = b.get("html")
        if (
            not isinstance(content, str)
            or not content.strip()
            or len(content.encode()) > 20 * 1024 * 1024
        ):
            raise HTTPException(422, "HTML inválido o demasiado grande.")
        with store.db() as db:
            c, u, j = connector_job(db, request, key)
            if j["status"] != "working":
                raise HTTPException(409, "El encargo debe estar en curso.")
            lease = db.execute(
                "SELECT * FROM job_leases WHERE job=?", (key,)
            ).fetchone()
            expected = b.get("revision", j["revision"] if lease is None else None)
            if expected != j["revision"] or (
                lease
                and (
                    lease["revision"] != j["revision"]
                    or lease["expires"] < int(time.time())
                )
            ):
                raise HTTPException(
                    409, "El intento cambió o venció; vuelve a consultar el encargo."
                )
            a = owned(db, j["artifact"], u)
            match = re.search(
                r"<meta\s+name=[\"\']nota-documento[\"\']\s+content=[\"\']([a-zA-Z0-9_-]{1,120})[\"\']",
                content,
            )
            if not match or match[1] != a["document_id"]:
                raise HTTPException(409, "Conserva el documento-id original.")
            sha = hashlib.sha256(content.encode()).hexdigest()
            target = json.loads(j["target"])
            source = {
                "agent": c["agent"],
                "device": c["device"],
                "session": clean(
                    b.get("session") or target.get("session", ""), 200, True
                ),
                "label": "Margen assignment " + key,
            }
            prior = db.execute(
                "SELECT v.id FROM versions v JOIN version_meta m ON m.version=v.id WHERE v.artifact=? AND v.sha=? AND m.state='draft' AND json_extract(m.source,'$.label')=?",
                (a["id"], sha, source["label"]),
            ).fetchone()
            if prior:
                return {"version": prior["id"], "state": "draft"}
            if (
                db.execute(
                    "SELECT count(*) FROM versions WHERE artifact=?", (a["id"],)
                ).fetchone()[0]
                >= 200
            ):
                raise HTTPException(409, "Máximo 200 versiones por documento.")
            file = store.files / (sha + ".html")
            if not file.exists():
                temp = store.files / (uuid.uuid4().hex + ".tmp")
                temp.write_text(content)
                temp.replace(file)
            vid = uuid.uuid4().hex
            import shutil

            original = store.files / "attachments" / j["base_version"]
            if original.is_dir():
                shutil.copytree(original, store.files / "attachments" / vid)
            db.execute(
                "INSERT INTO versions VALUES(?,?,?,?)",
                (vid, a["id"], sha, int(time.time())),
            )
            from portal.formats import describe

            db.execute(
                "INSERT INTO version_formats VALUES(?,?)",
                (vid, json.dumps(describe(content))),
            )
            db.execute(
                "INSERT INTO version_meta VALUES(?,?,?,?,?)",
                (vid, "draft", a["title"], a["space"], json.dumps(source)),
            )
            db.execute(
                "INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)",
                (c["id"], "connector:draft", a["id"], int(time.time())),
            )
        return {
            "version": vid,
            "state": "draft",
            "preview_url": origin + "/a/" + a["id"] + "?version=" + vid,
        }

    @app.get("/api/creator/graph")
    def creator_graph(request: Request):
        from portal.context_graph import network
        from portal.knowledge import enrich
        from portal.workflows import metadata

        u = account(request)
        project = request.query_params.get("project", "")
        focus = request.query_params.get("artifact", "")
        with store.db() as db:
            rows = [
                dict(r)
                for r in db.execute(
                    "SELECT a.* FROM artifacts a WHERE a.owner=? AND (?='' OR a.space=?) ORDER BY a.updated DESC LIMIT 151",
                    (u["id"], project, project),
                )
            ]
            if focus:
                a = owned(db, focus, u)
                rows = [a] + [r for r in rows if r["id"] != focus]
            total = db.execute(
                "SELECT count(*) FROM artifacts WHERE owner=? AND (?='' OR space=?)",
                (u["id"], project, project),
            ).fetchone()[0]
            rows = rows[:150]
            valid = {r["id"] for r in rows}
            records = [
                {
                    **r,
                    **metadata(db, r["id"]),
                    **enrich(db, r, u),
                }
                for r in rows
            ]
            graph = network(db, records, u)
            for d in db.execute(
                "SELECT * FROM creator_decisions WHERE owner=? AND (?='' OR project=?) ORDER BY updated DESC LIMIT 200",
                (u["id"], project, project),
            ):
                refs = [
                    e
                    for e in json.loads(d["body"])["evidence"]
                    if e["artifact"] in valid
                ]
                if not refs:
                    continue
                node = "decision:" + d["id"]
                graph["nodes"].append(
                    {
                        "id": node,
                        "title": d["title"],
                        "kind": "decision",
                        "state": d["state"],
                        "review_on": d["review_on"],
                        "expected": json.loads(d["body"]).get("expected", ""),
                        "count": len(refs),
                    }
                )
                for e in refs:
                    changed = (
                        next(
                            a["current_version"]
                            for a in rows
                            if a["id"] == e["artifact"]
                        )
                        != e["version"]
                    )
                    graph["edges"].append(
                        {
                            "source": node,
                            "target": e["artifact"],
                            "kind": "evidence",
                            "reason": (
                                "Evidencia cambió · revisar: "
                                if changed
                                else "Evidencia registrada: "
                            )
                            + e["title"],
                            "version": e["version"],
                        }
                    )
            claim_ids = set()
            for claim in db.execute(
                "SELECT * FROM memory_claims WHERE owner=? AND (?='' OR project=?) ORDER BY updated DESC LIMIT 200",
                (u["id"], project, project),
            ):
                refs = [
                    e for e in json.loads(claim["evidence"]) if e["artifact"] in valid
                ]
                if not refs:
                    continue
                node = "claim:" + claim["id"]
                claim_ids.add(claim["id"])
                graph["nodes"].append(
                    {
                        "id": node,
                        "title": claim["statement"],
                        "kind": "claim",
                        "state": claim["state"],
                        "period": claim["period"],
                        "subject": claim["subject"],
                        "count": len(refs),
                    }
                )
                for e in refs:
                    graph["edges"].append(
                        {
                            "source": e["artifact"],
                            "target": node,
                            "kind": "evidence",
                            "reason": e["quote"],
                            "version": e["version"],
                        }
                    )
            for contrast in db.execute(
                "SELECT * FROM memory_links WHERE owner=? AND state!='dismissed'",
                (u["id"],),
            ):
                if {contrast["left_id"], contrast["right_id"]} <= claim_ids:
                    graph["edges"].append(
                        {
                            "source": "claim:" + contrast["left_id"],
                            "target": "claim:" + contrast["right_id"],
                            "kind": (
                                "confirmed_contrast"
                                if contrast["state"] == "confirmed"
                                else "suggestion"
                            ),
                            "reason": contrast["reason"],
                        }
                    )
            groups = {}
            for v in db.execute(
                "SELECT v.artifact,m.source FROM versions v JOIN version_meta m ON m.version=v.id JOIN artifacts a ON a.id=v.artifact WHERE a.owner=? AND (?='' OR a.space=?) ORDER BY v.created DESC LIMIT 2000",
                (u["id"], project, project),
            ):
                source = json.loads(v["source"])
                if v["artifact"] in valid and source.get("session"):
                    groups.setdefault(
                        (
                            source.get("agent", ""),
                            source["session"],
                            source.get("device", ""),
                        ),
                        set(),
                    ).add(v["artifact"])
            for (agent, session, device), ids in groups.items():
                node = (
                    "session:"
                    + hashlib.sha256((agent + session + device).encode()).hexdigest()[
                        :20
                    ]
                )
                graph["nodes"].append(
                    {
                        "id": node,
                        "title": agent + " · " + session[:22],
                        "kind": "session",
                        "agent": agent,
                        "session": session,
                        "device": device,
                        "count": len(ids),
                    }
                )
                for aid in ids:
                    graph["edges"].append(
                        {
                            "source": node,
                            "target": aid,
                            "kind": "created",
                            "reason": "Origen registrado · " + agent + " · " + device,
                        }
                    )
        return {
            "nodes": records,
            "edges": [],
            "network": graph,
            "total": total,
            "truncated": total > 150,
            "scope": "Hasta 150 artefactos recientes y 2000 versiones de este proyecto. Las relaciones muestran su evidencia.",
        }

    from portal.memory import mount as mount_memory

    mount_memory(
        app,
        store,
        origin,
        account,
        payload,
        clean,
        owned,
        evidence,
        inspect_decision,
        threads,
        snapshot,
    )

    from portal.job_leases import mount as mount_leases

    mount_leases(app, store, payload, connector, job_for)
