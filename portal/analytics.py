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


def mount(app, store, account, who, artifact_for, payload, snapshot, threads):
    from portal.umami import UmamiReports
    from portal.workflows import version_state
    reports = UmamiReports(configuration)
    app.state.umami_reports = reports
    with store.db() as db:
        db.executescript(
            """CREATE TABLE IF NOT EXISTS artifact_visits(artifact TEXT NOT NULL REFERENCES artifacts(id),day TEXT NOT NULL,views INTEGER NOT NULL,PRIMARY KEY(artifact,day));
        CREATE TABLE IF NOT EXISTS analytics_preferences(owner TEXT PRIMARY KEY REFERENCES users(id),enabled INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS reader_activity_preferences(owner TEXT PRIMARY KEY REFERENCES users(id),shared INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS artifact_activity_preferences(artifact TEXT PRIMARY KEY REFERENCES artifacts(id),shared INTEGER NOT NULL);"""
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


    def shared(db, a):
        row = db.execute("SELECT shared FROM artifact_activity_preferences WHERE artifact=?", (a["id"],)).fetchone()
        if row is None:
            row = db.execute("SELECT shared FROM reader_activity_preferences WHERE owner=?", (a["owner"],)).fetchone()
        return bool(row and row["shared"])

    @app.put("/api/artifacts/{aid}/activity")
    async def activity_preferences(aid: str, request: Request):
        u = account(request, True)
        body = await payload(request)
        if type(body.get("shared")) is not bool:
            raise HTTPException(422, "Elige si quieres mostrar la actividad.")
        with store.db() as db:
            a = artifact_for(db, aid, u)
            if u["id"] != a["owner"]:
                raise HTTPException(404)
            db.execute("INSERT INTO artifact_activity_preferences VALUES(?,?) ON CONFLICT(artifact) DO UPDATE SET shared=excluded.shared", (aid, int(body["shared"])))
        return {"shared": body["shared"]}

    @app.get("/api/artifacts/{aid}/activity")
    def activity(aid: str, request: Request):
        u = who(request)
        try:
            days = int(request.query_params.get("days", "30"))
        except ValueError:
            raise HTTPException(422, "Período inválido.") from None
        if days not in (7, 30, 90, 365):
            raise HTTPException(422, "Período inválido.")
        now = int(time.time())
        today = time.strftime("%Y-%m-%d", time.gmtime(now))
        since = time.strftime("%Y-%m-%d", time.gmtime(now - (days - 1) * 86400))
        with store.db() as db:
            a = artifact_for(db, aid, u)
            owner = bool(u and u["id"] == a["owner"])
            sharing = shared(db, a)
            if not owner and not sharing:
                return {"visible": False}
            on = enabled(db, a["owner"])
            views = db.execute("SELECT coalesce(sum(views),0) FROM artifact_visits WHERE artifact=? AND day>=? AND day<=?", (aid, since, today)).fetchone()[0]
            # Same review authorization as the reader; personal notes and draft threads never count.
            conversations = [t for t in threads(snapshot(db, a, u)["events"]) if t.get("entry_type", "comment") == "comment" and version_state(db, t["version"]) != "draft"]
            participants = {}
            messages = 0
            for thread in conversations:
                for event in [thread, *thread["replies"]]:
                    messages += 1
                    actor = event.get("actor")
                    if actor:
                        participants[actor] = {"name": event.get("author", "Participante")[:80], "verified": bool(event.get("verified"))}
        from datetime import datetime, timezone
        start = int(datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        stats = reports.stats(aid, start, now * 1000) if on else None
        people = sorted(participants.values(), key=lambda p: p["name"].casefold())
        return {"visible": True, "shared": sharing, "owner": owner, "enabled": on,
                "days": days, "since": since, "until": today, "timezone": "UTC",
                "views": stats["views"] if stats else views if on else None,
                "visitors": stats["visitors"] if stats else None,
                "source": "umami" if stats else "margen" if on else None,
                "updated_at": now, "cache_seconds": 300,
                "comments": len(conversations), "messages": messages,
                "participant_count": len(people), "participants": people[:30], "participant_limit": 30}

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

    @app.get("/api/creator/analytics/summary")
    def summary(request: Request):
        """Aggregate in SQL before limiting ranking rows; never sum a truncated feed."""
        u = account(request)
        try:
            days = int(request.query_params.get("days", "30"))
        except ValueError:
            raise HTTPException(422, "Período inválido.") from None
        if days not in (7, 30, 90, 365):
            raise HTTPException(422, "Período inválido.")
        project = request.query_params.get("project", "")
        today = time.strftime("%Y-%m-%d", time.gmtime())
        since = time.strftime("%Y-%m-%d", time.gmtime(time.time() - (days - 1) * 86400))
        with store.db() as db:
            where = "a.owner=? AND (?='' OR a.space=?) AND v.day>=? AND v.day<=?"
            args = (u["id"], project, project, since, today)
            daily = [
                dict(r)
                for r in db.execute(
                    f"SELECT v.day,sum(v.views) AS views FROM artifact_visits v JOIN artifacts a ON a.id=v.artifact WHERE {where} GROUP BY v.day ORDER BY v.day",
                    args,
                )
            ]
            ranking = [
                dict(r)
                for r in db.execute(
                    f"SELECT a.id,a.title,a.space,sum(v.views) AS views,max(v.day) AS last_day FROM artifact_visits v JOIN artifacts a ON a.id=v.artifact WHERE {where} GROUP BY a.id ORDER BY views DESC,a.title LIMIT 100",
                    args,
                )
            ]
            active = db.execute(
                f"SELECT count(DISTINCT a.id) FROM artifact_visits v JOIN artifacts a ON a.id=v.artifact WHERE {where}",
                args,
            ).fetchone()[0]
            spaces = [
                dict(r)
                for r in db.execute(
                    "SELECT space,count(*) AS artifacts FROM artifacts WHERE owner=? GROUP BY space ORDER BY space",
                    (u["id"],),
                )
            ]
            return {
                "enabled": enabled(db, u["id"]),
                "umami": configuration(),
                "days": days,
                "since": since,
                "until": today,
                "timezone": "UTC",
                "daily": daily,
                "total": sum(r["views"] for r in daily),
                "active_artifacts": active,
                "ranking": ranking,
                "ranking_limit": 100,
                "spaces": spaces,
                "unit": "page_opens",
                "retention_days": 365,
            }

    @app.put("/api/creator/analytics")
    async def preferences(request: Request):
        u = account(request, True)
        b = await payload(request)
        if not isinstance(b.get("enabled"), bool):
            raise HTTPException(422)
        if "share_with_readers" in b and type(b["share_with_readers"]) is not bool:
            raise HTTPException(422)
        with store.db() as db:
            if "share_with_readers" in b:
                db.execute("INSERT INTO reader_activity_preferences VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET shared=excluded.shared", (u["id"], int(b["share_with_readers"])))
            db.execute(
                "INSERT INTO analytics_preferences VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET enabled=excluded.enabled",
                (u["id"], int(b["enabled"])),
            )
        return {"enabled": b["enabled"]}
