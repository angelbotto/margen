"""Owner-scoped aggregate visit counts and optional, explicitly configured Umami."""

import os
import re
import time
from urllib.parse import urlsplit
from fastapi import HTTPException, Request


def configuration():
    url = os.environ.get("MARGEN_UMAMI_URL", "").rstrip("/")
    website = os.environ.get("MARGEN_UMAMI_WEBSITE_ID", "")
    p = urlsplit(url)
    if (
        p.scheme != "https"
        or not p.hostname
        or p.username
        or p.password
        or p.path
        or p.query
        or p.fragment
        or not re.fullmatch(
            r"[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}", website
        )
    ):
        return None
    return {"origin": url, "website": website}


def mount(app, store, account, who, artifact_for, payload):
    with store.db() as db:
        db.executescript(
            """CREATE TABLE IF NOT EXISTS artifact_visits(artifact TEXT NOT NULL REFERENCES artifacts(id),day TEXT NOT NULL,views INTEGER NOT NULL,PRIMARY KEY(artifact,day));
        CREATE TABLE IF NOT EXISTS analytics_preferences(owner TEXT PRIMARY KEY REFERENCES users(id),enabled INTEGER NOT NULL);"""
        )

    def enabled(db, owner):
        row = db.execute(
            "SELECT enabled FROM analytics_preferences WHERE owner=?", (owner,)
        ).fetchone()
        return (
            bool(row["enabled"])
            if row
            else os.environ.get("MARGEN_ANALYTICS_ENABLED") == "1"
        )

    @app.get("/api/artifacts/{aid}/analytics-config")
    def config(aid: str, request: Request):
        u = who(request)
        with store.db() as db:
            a = artifact_for(db, aid, u)
            on = enabled(db, a["owner"]) and not (
                u and (u["id"] == a["owner"] or u.get("agent"))
            )
            return {"enabled": on, "umami": configuration() if on else None}

    @app.post("/api/artifacts/{aid}/visit")
    async def visit(aid: str, request: Request):
        u = who(request)
        with store.db() as db:
            a = artifact_for(db, aid, u)
            if (
                not enabled(db, a["owner"])
                or (u and (u["id"] == a["owner"] or u.get("agent")))
                or request.headers.get("dnt") == "1"
                or request.headers.get("sec-gpc") == "1"
            ):
                return {"recorded": False}
            # Counts are page opens, never unique people. The browser sends once per load.
            day = time.strftime("%Y-%m-%d", time.gmtime())
            db.execute(
                "INSERT INTO artifact_visits VALUES(?,?,1) ON CONFLICT(artifact,day) DO UPDATE SET views=views+1",
                (aid, day),
            )
            db.execute(
                "DELETE FROM artifact_visits WHERE day<?",
                (time.strftime("%Y-%m-%d", time.gmtime(time.time() - 365 * 86400)),),
            )
        return {"recorded": True}

    @app.get("/api/creator/analytics")
    def analytics(request: Request):
        u = account(request)
        with store.db() as db:
            rows = [
                dict(r)
                for r in db.execute(
                    "SELECT a.id,a.title,a.space,v.day,v.views FROM artifact_visits v JOIN artifacts a ON a.id=v.artifact WHERE a.owner=? AND (?='' OR a.space=?) ORDER BY v.day DESC LIMIT 2000",
                    (
                        u["id"],
                        request.query_params.get("project", ""),
                        request.query_params.get("project", ""),
                    ),
                )
            ]
            return {
                "enabled": enabled(db, u["id"]),
                "umami": configuration(),
                "rows": rows,
                "limit": 2000,
                "unit": "Page opens; excludes owner, not unique visitors",
                "retention_days": 365,
            }

    @app.put("/api/creator/analytics")
    async def preferences(request: Request):
        u = account(request, True)
        b = await payload(request)
        if not isinstance(b.get("enabled"), bool):
            raise HTTPException(422)
        with store.db() as db:
            db.execute(
                "INSERT INTO analytics_preferences VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET enabled=excluded.enabled",
                (u["id"], int(b["enabled"])),
            )
        return {"enabled": b["enabled"]}
