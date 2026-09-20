"""Opt-in execution leases with explicit recovery and cancellation acknowledgement."""

import json
import time
from fastapi import HTTPException, Request

TTL = 180


def migrate(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS job_leases(job TEXT PRIMARY KEY,revision INTEGER NOT NULL,heartbeat INTEGER NOT NULL,expires INTEGER NOT NULL,stopped INTEGER NOT NULL DEFAULT 0)"
    )


def expire(db):
    now = int(time.time())
    rows = db.execute(
        "SELECT j.id,j.revision FROM creator_jobs j JOIN job_leases l ON l.job=j.id AND l.revision=j.revision WHERE j.status IN ('working','waiting') AND l.expires<?",
        (now,),
    ).fetchall()
    for row in rows:
        db.execute(
            "UPDATE creator_jobs SET status='failed',revision=revision+1,updated=?,result=? WHERE id=? AND revision=?",
            (
                now,
                json.dumps(
                    {
                        "summary": "El receptor perdió su señal de vida. Revisa sus archivos y confirma que se detuvo antes de reintentar."
                    }
                ),
                row["id"],
                row["revision"],
            ),
        )
        db.execute(
            "INSERT INTO creator_receipts(job,state,actor,detail,at) VALUES(?,?,?,?,?)",
            (
                row["id"],
                "failed",
                "lease",
                "Señal de vida vencida; no se reinició automáticamente.",
                now,
            ),
        )


def mount(app, store, payload, connector, job_for):
    @app.post("/api/connector/jobs/{key}/heartbeat")
    async def heartbeat(key: str, request: Request):
        b = await payload(request)
        with store.db() as db:
            c = connector(db, request)
            u = dict(
                db.execute("SELECT * FROM users WHERE id=?", (c["owner"],)).fetchone()
            )
            j = job_for(db, key, u)
            if json.loads(j["target"]).get("connector") != c["id"]:
                raise HTTPException(404)
            lease = db.execute(
                "SELECT * FROM job_leases WHERE job=?", (key,)
            ).fetchone()
            if j["status"] == "cancelled" or j["revision"] != b.get("revision"):
                if (
                    b.get("stopped") is True
                    and lease
                    and lease["revision"] == b.get("revision")
                    and not lease["stopped"]
                ):
                    db.execute("UPDATE job_leases SET stopped=1 WHERE job=?", (key,))
                    db.execute(
                        "INSERT INTO creator_receipts(job,state,actor,detail,at) VALUES(?,?,?,?,?)",
                        (
                            key,
                            "stopped",
                            c["id"],
                            "El receptor confirmó que el proceso local terminó.",
                            int(time.time()),
                        ),
                    )
                return {
                    "continue": False,
                    "status": j["status"],
                    "revision": j["revision"],
                }
            if j["status"] not in ("working", "waiting"):
                return {
                    "continue": False,
                    "status": j["status"],
                    "revision": j["revision"],
                }
            now = int(time.time())
            if lease and lease["revision"] == j["revision"] and lease["expires"] < now:
                expire(db)
                return {
                    "continue": False,
                    "status": "expired",
                    "revision": j["revision"],
                }
            if (
                b.get("stopped") is True
                and lease
                and lease["revision"] == j["revision"]
            ):
                db.execute("UPDATE job_leases SET stopped=1 WHERE job=?", (key,))
                return {"continue": True, "revision": j["revision"], "stopped": True}
            db.execute(
                "INSERT INTO job_leases VALUES(?,?,?,?,0) ON CONFLICT(job) DO UPDATE SET revision=excluded.revision,heartbeat=excluded.heartbeat,expires=excluded.expires,stopped=0",
                (key, j["revision"], now, now + TTL),
            )
            return {"continue": True, "expires": now + TTL, "revision": j["revision"]}
