"""Inspectable working memory: cited claims, continuity, contradictions and outcomes."""

import json
import re
import time
import uuid
from datetime import date
from fastapi import HTTPException, Request
from portal.search import extract_text, normalized


def migrate(db):
    db.executescript(
        """CREATE TABLE IF NOT EXISTS memory_claims(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),project TEXT NOT NULL,statement TEXT NOT NULL,subject TEXT NOT NULL,period TEXT NOT NULL,value TEXT NOT NULL,state TEXT NOT NULL,review_on TEXT NOT NULL,evidence TEXT NOT NULL,updated INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS memory_claims_owner ON memory_claims(owner,project,updated);
    CREATE TABLE IF NOT EXISTS memory_history(id INTEGER PRIMARY KEY,owner TEXT NOT NULL,entity TEXT NOT NULL,record TEXT NOT NULL,at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS memory_links(id TEXT PRIMARY KEY,owner TEXT NOT NULL,left_id TEXT NOT NULL,right_id TEXT NOT NULL,state TEXT NOT NULL,reason TEXT NOT NULL,updated INTEGER NOT NULL,UNIQUE(owner,left_id,right_id));
    CREATE TABLE IF NOT EXISTS memory_sessions(id TEXT PRIMARY KEY,owner TEXT NOT NULL,agent TEXT NOT NULL,device TEXT NOT NULL,session TEXT NOT NULL,project TEXT NOT NULL,objective TEXT NOT NULL,summary TEXT NOT NULL,next_step TEXT NOT NULL,updated INTEGER NOT NULL,UNIQUE(owner,agent,device,session));"""
    )


def materiality(store, db, e, current):
    if e["version"] == current:
        return "unchanged"
    versions = [
        db.execute(
            "SELECT sha FROM versions WHERE id=? AND artifact=?", (v, e["artifact"])
        ).fetchone()
        for v in (e["version"], current)
    ]
    if not all(versions):
        return "unavailable"
    texts = [
        " ".join(extract_text((store.files / (v["sha"] + ".html")).read_text()).split())
        for v in versions
    ]
    if texts[0] == texts[1]:
        return "presentation_only"
    quote = " ".join(e.get("quote", "").split())
    if quote and quote in texts[1]:
        return "quoted_text_preserved"
    return "cited_text_changed" if quote else "unassessed"


def mount(
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
):
    def claims(db, u, project):
        result = []
        for row in db.execute(
            "SELECT * FROM memory_claims WHERE owner=? AND (?='' OR project=?) ORDER BY updated DESC,id LIMIT 500",
            (u["id"], project, project),
        ):
            c = dict(row)
            refs = []
            for e in json.loads(c["evidence"]):
                a = owned(db, e["artifact"], u)
                refs.append(
                    {
                        **e,
                        "url": origin + "/a/" + a["id"] + "?version=" + e["version"],
                        "materiality": materiality(store, db, e, a["current_version"]),
                    }
                )
            c["evidence"] = refs
            c["needs_review"] = c["state"] != "discarded" and (
                bool(c["review_on"] and c["review_on"] <= date.today().isoformat())
                or any(
                    e["materiality"]
                    in (
                        "cited_text_changed",
                        "quoted_text_preserved",
                        "unassessed",
                        "unavailable",
                    )
                    for e in refs
                )
            )
            result.append(c)
        return result

    def contradictions(db, u, items):
        candidates = []
        saved = {
            (r["left_id"], r["right_id"]): dict(r)
            for r in db.execute("SELECT * FROM memory_links WHERE owner=?", (u["id"],))
        }
        groups = {}
        for c in items:
            if (
                c["state"] == "discarded"
                or not c["subject"]
                or not c["period"]
                or not c["value"]
            ):
                continue
            group = (c["project"], normalized(c["subject"]), normalized(c["period"]))
            groups.setdefault(group, []).append(c)
        for group, values in groups.items():
            for i, a in enumerate(values):
                for b in values[i + 1 :]:
                    if normalized(a["value"]) == normalized(b["value"]):
                        continue
                    left, right = sorted([a["id"], b["id"]])
                    choice = saved.get((left, right), {})
                    candidates.append(
                        {
                            "left": a,
                            "right": b,
                            "state": choice.get("state", "suggested"),
                            "reason": choice.get("reason")
                            or "Mismo proyecto, asunto y periodo declarados; valores distintos. Comprobar unidad, alcance y autoridad de ambas fuentes.",
                            "id": choice.get("id"),
                        }
                    )
                    if len(candidates) >= 100:
                        return candidates
        return candidates

    def sessions(db, u, project):
        groups = {}
        for row in db.execute(
            "SELECT a.id artifact,a.title,a.space,v.id version,v.created,m.source FROM versions v JOIN artifacts a ON a.id=v.artifact JOIN version_meta m ON m.version=v.id WHERE a.owner=? AND (?='' OR a.space=?) ORDER BY v.created DESC LIMIT 2000",
            (u["id"], project, project),
        ):
            r = dict(row)
            s = json.loads(r.pop("source"))
            if not s.get("session"):
                continue
            key = (s.get("agent", ""), s.get("device", ""), s["session"])
            group = groups.setdefault(
                key,
                {
                    "agent": key[0],
                    "device": key[1],
                    "session": key[2],
                    "outputs": [],
                    "objective": "",
                    "summary": "",
                    "next_step": "",
                },
            )
            group["outputs"].append(
                {
                    **r,
                    "url": origin + "/a/" + r["artifact"] + "?version=" + r["version"],
                }
            )
        for key, g in groups.items():
            row = db.execute(
                "SELECT objective,summary,next_step,updated FROM memory_sessions WHERE owner=? AND agent=? AND device=? AND session=?",
                (u["id"], *key),
            ).fetchone()
            if row:
                g.update(dict(row))
        return list(groups.values())[:200]

    @app.get("/api/creator/memory")
    def memory(request: Request):
        u = account(request)
        project = request.query_params.get("project", "")
        with store.db() as db:
            items = claims(db, u, project)
            decisions = [
                inspect_decision(db, r, u)
                for r in db.execute(
                    "SELECT * FROM creator_decisions WHERE owner=? AND (?='' OR project=?) ORDER BY updated DESC LIMIT 200",
                    (u["id"], project, project),
                )
            ]
            return {
                "claims": items,
                "contradictions": contradictions(db, u, items),
                "sessions": sessions(db, u, project),
                "outcomes": decisions,
                "limits": {
                    "claims": 500,
                    "contradictions": 100,
                    "decisions": 200,
                    "session_origins": 2000,
                },
                "method": "Declared matching subject and period with differing values; candidates require human review, not semantic fact checking.",
            }

    @app.post("/api/creator/claims")
    async def save_claim(request: Request):
        u = account(request, True)
        b = await payload(request)
        key = clean(b.get("id") or uuid.uuid4().hex, 32)
        state = b.get("state", "open")
        if state not in ("open", "supported", "discarded"):
            raise HTTPException(422, "Estado inválido.")
        review = clean(b.get("review_on", ""), 10, True)
        if review:
            try:
                date.fromisoformat(review)
            except ValueError:
                raise HTTPException(422, "Fecha inválida.")
        with store.db() as db:
            previous = db.execute(
                "SELECT * FROM memory_claims WHERE id=?", (key,)
            ).fetchone()
            if previous and previous["owner"] != u["id"]:
                raise HTTPException(404)
            if previous and b.get("updated") != previous["updated"]:
                raise HTTPException(409, "El supuesto cambió; vuelve a abrirlo.")
            refs = evidence(db, b.get("evidence", []), u)
            if not refs or any(not e["quote"] for e in refs):
                raise HTTPException(
                    422, "Añade al menos una cita exacta a una versión propia."
                )
            now = max(
                time.time_ns() // 1000000, (previous["updated"] + 1) if previous else 0
            )
            vals = (
                key,
                u["id"],
                clean(b.get("project", "Personal"), 60),
                clean(b.get("statement"), 2000),
                clean(b.get("subject", ""), 200, True),
                clean(b.get("period", ""), 120, True),
                clean(b.get("value", ""), 200, True),
                state,
                review,
                json.dumps(refs),
                now,
            )
            db.execute(
                "INSERT INTO memory_claims VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET project=excluded.project,statement=excluded.statement,subject=excluded.subject,period=excluded.period,value=excluded.value,state=excluded.state,review_on=excluded.review_on,evidence=excluded.evidence,updated=excluded.updated",
                vals,
            )
            db.execute(
                "INSERT INTO memory_history(owner,entity,record,at) VALUES(?,?,?,?)",
                (
                    u["id"],
                    key,
                    json.dumps(
                        dict(
                            zip(
                                [
                                    "id",
                                    "owner",
                                    "project",
                                    "statement",
                                    "subject",
                                    "period",
                                    "value",
                                    "state",
                                    "review_on",
                                    "evidence",
                                    "updated",
                                ],
                                vals,
                            )
                        )
                    ),
                    int(time.time()),
                ),
            )
        return {"id": key, "updated": now}

    @app.get("/api/creator/claims/{key}/history")
    def history(key: str, request: Request):
        u = account(request)
        with store.db() as db:
            if not db.execute(
                "SELECT 1 FROM memory_claims WHERE id=? AND owner=?", (key, u["id"])
            ).fetchone():
                raise HTTPException(404)
            return {
                "items": [
                    dict(r)
                    for r in db.execute(
                        "SELECT record,at FROM memory_history WHERE entity=? AND owner=? ORDER BY id DESC LIMIT 100",
                        (key, u["id"]),
                    )
                ]
            }

    @app.post("/api/creator/contradictions")
    async def link(request: Request):
        u = account(request, True)
        b = await payload(request)
        left, right = sorted([clean(b.get("left"), 32), clean(b.get("right"), 32)])
        if left == right or b.get("state") not in (
            "confirmed",
            "dismissed",
            "suggested",
        ):
            raise HTTPException(422)
        with store.db() as db:
            for key in (left, right):
                if not db.execute(
                    "SELECT 1 FROM memory_claims WHERE id=? AND owner=?", (key, u["id"])
                ).fetchone():
                    raise HTTPException(404)
            db.execute(
                "INSERT INTO memory_links VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner,left_id,right_id) DO UPDATE SET state=excluded.state,reason=excluded.reason,updated=excluded.updated",
                (
                    uuid.uuid4().hex,
                    u["id"],
                    left,
                    right,
                    b["state"],
                    clean(b.get("reason"), 2000),
                    int(time.time()),
                ),
            )
        return {"saved": True}

    @app.post("/api/creator/sessions")
    async def save_session(request: Request):
        u = account(request, True)
        b = await payload(request)
        with store.db() as db:
            key = tuple(
                clean(b.get(k, ""), 200, True) for k in ("agent", "device", "session")
            )
            if not key[2] or not any(
                (s["agent"], s["device"], s["session"]) == key
                for s in sessions(db, u, "")
            ):
                raise HTTPException(
                    422, "Elige una sesión registrada en tus versiones."
                )
            db.execute(
                "INSERT INTO memory_sessions VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(owner,agent,device,session) DO UPDATE SET objective=excluded.objective,summary=excluded.summary,next_step=excluded.next_step,updated=excluded.updated",
                (
                    uuid.uuid4().hex,
                    u["id"],
                    *key,
                    clean(b.get("project", ""), 60, True),
                    clean(b.get("objective", ""), 2000, True),
                    clean(b.get("summary", ""), 4000, True),
                    clean(b.get("next_step", ""), 2000, True),
                    int(time.time()),
                ),
            )
        return {"saved": True}

    @app.get("/api/creator/brief")
    def brief(request: Request):
        u = account(request)
        project = request.query_params.get("project", "")
        lines = [
            "# Continuidad · " + (project or "Mis proyectos"),
            "Corte: " + time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
            "Fuentes propias. Notas privadas excluidas. Resumen por reglas; no es una respuesta generada por IA.",
            "",
        ]
        with store.db() as db:
            lines.append("## Supuestos por revisar")
            for c in claims(db, u, project):
                if c["needs_review"] or c["state"] == "open":
                    lines.append("- " + c["statement"])
                    lines.extend(
                        "  Fuente: " + e["url"] + "\n  Cita: " + e["quote"]
                        for e in c["evidence"]
                    )
            lines.append("\n## Decisiones y resultado esperado")
            for r in db.execute(
                "SELECT * FROM creator_decisions WHERE owner=? AND (?='' OR project=?) ORDER BY updated DESC LIMIT 200",
                (u["id"], project, project),
            ):
                d = inspect_decision(db, r, u)
                lines.extend(
                    [
                        "- " + d["title"] + " · " + d["state"],
                        "  Criterio: " + d["rationale"],
                        "  Esperado: " + d["expected"],
                        "  Observado: " + (d["outcome"] or "Aún no registrado"),
                    ]
                )
                lines.extend("  Fuente: " + e["url"] for e in d["evidence"])
            lines.append("\n## Conversaciones pendientes")
            for r in db.execute(
                "SELECT * FROM artifacts WHERE owner=? AND (?='' OR space=?) ORDER BY updated DESC LIMIT 200",
                (u["id"], project, project),
            ):
                for t in threads(snapshot(db, r, u)["events"]):
                    if t.get("resolved") or t.get("entry_type") == "note":
                        continue
                    lines.extend(
                        [
                            "- "
                            + r["title"]
                            + " · "
                            + origin
                            + "/a/"
                            + r["id"]
                            + "?thread="
                            + t["thread"],
                            "  Versión: " + t["version"],
                            "  Cita: " + t.get("anchor", {}).get("quote", ""),
                            "  Comentario: " + t["text"],
                        ]
                    )
            lines.append("\n## Dónde continuar")
            for s in sessions(db, u, project):
                lines.extend(
                    [
                        "- " + " / ".join([s["agent"], s["device"], s["session"]]),
                        "  Objetivo: " + (s["objective"] or "No registrado"),
                        "  Estado: " + (s["summary"] or "No registrado"),
                        "  Siguiente paso: "
                        + (s["next_step"] or "Pendiente de definir"),
                    ]
                )
                lines.extend("  Salida: " + o["url"] for o in s["outputs"][:10])
        return {
            "text": "\n".join(lines),
            "limits": {"artifacts": 200, "decisions": 200, "session_origins": 2000},
            "private_notes": False,
        }

    @app.get("/api/creator/evidence-search")
    def evidence_search(request: Request):
        from portal.search import match_query
        from portal.workflows import outline

        u = account(request)
        q = clean(request.query_params.get("q", ""), 300)
        project = request.query_params.get("project", "")
        match = match_query(q)
        if not match:
            return {
                "items": [],
                "answer": "No hay términos que buscar.",
                "method": "literal",
            }
        with store.db() as db:
            rows = db.execute(
                "SELECT a.id,a.title,a.current_version,v.sha FROM artifact_fts JOIN artifacts a ON a.id=artifact_fts.artifact JOIN versions v ON v.id=a.current_version WHERE artifact_fts MATCH ? AND a.owner=? AND (?='' OR a.space=?) ORDER BY bm25(artifact_fts) LIMIT 20",
                (match, u["id"], project, project),
            ).fetchall()
            words = re.findall(r"\w+", normalized(q))[:16]
            items = []
            for r in rows:
                content = (store.files / (r["sha"] + ".html")).read_text()
                parsed = outline(content)
                blocks = [
                    (key, text) for key, text in parsed.ids.items() if len(text) < 8000
                ]
                scored = sorted(
                    (
                        (sum(w in normalized(text) for w in words), key, text)
                        for key, text in blocks
                    ),
                    reverse=True,
                )
                if not scored:
                    continue
                score, key, text = scored[0]
                items.append(
                    {
                        "artifact": r["id"],
                        "title": r["title"],
                        "version": r["current_version"],
                        "quote": text[:2500],
                        "reference": key,
                        "url": origin
                        + "/a/"
                        + r["id"]
                        + "?version="
                        + r["current_version"]
                        + "#"
                        + __import__("urllib.parse", fromlist=["quote"]).quote(
                            key, safe=""
                        ),
                        "matched_terms": score,
                    }
                )
            return {
                "items": items,
                "method": "Full-text AND search over owned published versions; excerpts are evidence candidates, not an inferred answer.",
                "answer": (
                    "Fuentes para revisar; verifica que sostienen la conclusión."
                    if items
                    else "No encontré evidencia con esos términos en este alcance. Prueba una búsqueda más concreta."
                ),
            }
