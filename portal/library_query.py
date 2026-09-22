"""SQL-first authorized library projection and keyset windows."""

import base64
import hashlib
import json
import time
from portal.search import normalized, match_query
from portal.domain_access import identity_bindings, IDENTITY_GRANTS_CTE
from portal.knowledge import enrich
from portal.table_query import parse


def migrate(db):
    db.executescript(
        """
    CREATE TABLE IF NOT EXISTS library_projection(artifact TEXT PRIMARY KEY REFERENCES artifacts(id),category TEXT NOT NULL,auto_tags TEXT NOT NULL,classification TEXT NOT NULL,automatic INTEGER NOT NULL,category_manual INTEGER NOT NULL,description TEXT NOT NULL,reading_minutes INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS library_dirty(artifact TEXT PRIMARY KEY);
    CREATE INDEX IF NOT EXISTS artifacts_owner_updated ON artifacts(owner,updated DESC,id);
    CREATE INDEX IF NOT EXISTS grants_email_artifact ON grants(email,artifact);
    CREATE INDEX IF NOT EXISTS versions_artifact_created ON versions(artifact,created);
    CREATE TABLE IF NOT EXISTS review_threads(thread TEXT PRIMARY KEY,artifact TEXT NOT NULL,version TEXT NOT NULL,actor TEXT NOT NULL,kind TEXT NOT NULL,resolved INTEGER NOT NULL DEFAULT 0,deleted INTEGER NOT NULL DEFAULT 0);
    CREATE INDEX IF NOT EXISTS review_threads_artifact ON review_threads(artifact,deleted,resolved,kind,actor);
    CREATE TRIGGER IF NOT EXISTS library_artifact_insert AFTER INSERT ON artifacts BEGIN INSERT OR IGNORE INTO library_dirty VALUES(NEW.id);END;
    CREATE TRIGGER IF NOT EXISTS library_artifact_update AFTER UPDATE ON artifacts BEGIN INSERT OR IGNORE INTO library_dirty VALUES(NEW.id);END;
    CREATE TRIGGER IF NOT EXISTS library_override_insert AFTER INSERT ON knowledge_overrides BEGIN INSERT OR IGNORE INTO library_dirty VALUES(NEW.artifact);END;
    CREATE TRIGGER IF NOT EXISTS library_override_update AFTER UPDATE ON knowledge_overrides BEGIN INSERT OR IGNORE INTO library_dirty VALUES(NEW.artifact);END;
    CREATE TRIGGER IF NOT EXISTS review_thread_create AFTER INSERT ON events WHEN json_extract(NEW.event,'$.kind')='create' BEGIN
      INSERT OR IGNORE INTO review_threads(thread,artifact,version,actor,kind) VALUES(NEW.id,NEW.artifact,NEW.version,NEW.actor,COALESCE(json_extract(NEW.event,'$.entry_type'),'comment'));END;
    CREATE TRIGGER IF NOT EXISTS review_thread_resolve AFTER INSERT ON events WHEN json_extract(NEW.event,'$.kind')='resolve' BEGIN UPDATE review_threads SET resolved=json_extract(NEW.event,'$.resolved') WHERE thread=json_extract(NEW.event,'$.thread') AND artifact=NEW.artifact;END;
    CREATE TRIGGER IF NOT EXISTS review_thread_delete AFTER INSERT ON events WHEN json_extract(NEW.event,'$.kind')='delete' BEGIN UPDATE review_threads SET deleted=1 WHERE thread=json_extract(NEW.event,'$.thread') AND artifact=NEW.artifact;END;
    """
    )
    if not db.execute("SELECT 1 FROM operation_status WHERE key='classification_v2'").fetchone():
        db.execute('INSERT OR IGNORE INTO library_dirty SELECT id FROM artifacts')
        db.execute("INSERT INTO operation_status VALUES('classification_v2','true')")
    if not db.execute(
        "SELECT 1 FROM operation_status WHERE key='library_projection_v1'"
    ).fetchone():
        db.execute("INSERT OR IGNORE INTO library_dirty SELECT id FROM artifacts")
        for e in db.execute("SELECT * FROM events ORDER BY time,id"):
            v = json.loads(e["event"])
            kind = v.get("kind")
            if kind == "create":
                db.execute(
                    "INSERT OR IGNORE INTO review_threads VALUES(?,?,?,?,?,0,0)",
                    (
                        e["id"],
                        e["artifact"],
                        e["version"],
                        e["actor"],
                        v.get("entry_type", "comment"),
                    ),
                )
            elif kind == "resolve":
                db.execute(
                    "UPDATE review_threads SET resolved=? WHERE thread=?",
                    (int(v["resolved"]), v["thread"]),
                )
            elif kind == "delete":
                db.execute(
                    "UPDATE review_threads SET deleted=1 WHERE thread=?", (v["thread"],)
                )
        db.execute(
            "INSERT INTO operation_status VALUES('library_projection_v1','true')"
        )


def refresh(db):
    for a in db.execute(
        "SELECT a.* FROM artifacts a JOIN library_dirty d ON d.artifact=a.id"
    ).fetchall():
        x = enrich(db, a, None)
        db.execute(
            "INSERT OR REPLACE INTO library_projection VALUES(?,?,?,?,?,?,?,?)",
            (
                a["id"],
                x["category"],
                json.dumps(x["auto_tags"]),
                json.dumps(x["classification"]),
                int(x["automatic"]),
                int(x["category_manual"]),
                x["description"],
                x["reading_minutes"],
            ),
        )
        db.execute("DELETE FROM library_dirty WHERE artifact=?", (a["id"],))


def query(db, u, params, is_admin):
    refresh(db)
    uid = u["id"]
    p = {
        "uid": uid,
        **identity_bindings(u),
        "admin": int(is_admin(u)),
        "verified": int(bool(u.get("verified"))),
    }
    view = params.get("view", "")
    public = view == "public"
    sql = "WITH " + IDENTITY_GRANTS_CTE + """, authorized AS (
    SELECT a.*,ou.name AS owner_name,CASE WHEN :admin OR a.owner=:uid THEN ou.email ELSE NULL END AS owner_email,
    g.role AS explicit_role,
    CASE WHEN a.owner=:uid OR :admin THEN 'owner' ELSE g.role END AS access_role,
    COALESCE(vm.state,'published') AS version_state,CASE WHEN a.owner=:uid THEN COALESCE(vm.source,'{}') ELSE '{}' END AS source,
    COALESCE(m.tags,'[]') AS tags,COALESCE(m.collections,'[]') AS collections,COALESCE(m.archived,0) AS archived,
    COALESCE(k.category,'Sin clasificar') AS category,COALESCE(k.auto_tags,'[]') AS auto_tags,COALESCE(k.classification,'[]') AS classification,
    COALESCE(k.automatic,1) AS automatic,COALESCE(k.category_manual,0) AS category_manual,COALESCE(k.description,'') AS description,COALESCE(k.reading_minutes,1) AS reading_minutes
    FROM artifacts a JOIN users ou ON ou.id=a.owner LEFT JOIN identity_grants g ON g.artifact=a.id
    LEFT JOIN version_meta vm ON vm.version=a.current_version LEFT JOIN artifact_meta m ON m.artifact=a.id
    LEFT JOIN library_projection k ON k.artifact=a.id
    WHERE (a.owner=:uid OR :admin OR g.role IS NOT NULL OR a.visibility IN ('public','unlisted'))
    ), visible AS (SELECT * FROM authorized WHERE (version_state<>'draft' OR access_role IN ('owner','editor')) AND """
    sql += "visibility='public'" if public else "access_role IS NOT NULL"
    if view in ("mine", "archived"):
        sql += " AND owner=:uid"
    if view == "shared":
        sql += " AND owner<>:uid AND explicit_role IS NOT NULL"
    if not params.get("document_id"):
        sql += " AND archived=" + ("1" if view == "archived" else "0")
    sql += """), counted AS (SELECT v.*,
    (SELECT count(*) FROM review_threads t LEFT JOIN version_meta tm ON tm.version=t.version WHERE t.artifact=v.id AND t.deleted=0 AND t.resolved=0 AND (COALESCE(tm.state,'published')<>'draft' OR v.access_role IN ('owner','editor')) AND ((t.kind='note' AND t.actor=:uid) OR (t.kind<>'note' AND (v.access_role IS NOT NULL OR v.comments='readers')))) AS open_comments,
    CASE WHEN v.access_role IN ('owner','editor') THEN (SELECT count(*) FROM versions vr JOIN version_meta mr ON mr.version=vr.id WHERE vr.artifact=v.id AND mr.state='draft') ELSE 0 END AS drafts
    FROM visible v), searched AS (SELECT counted.*,0 AS rank,'' AS excerpt FROM counted WHERE 1=1"""
    conditions = []

    def bind(value):
        key = "v" + str(len(p))
        p[key] = value
        return ":" + key

    for param, column in [
        ("space", "space"),
        ("access", "visibility"),
        ("category", "category"),
        ("document_id", "document_id"),
    ]:
        if params.get(param):
            conditions.append(column + "=" + bind(params[param]))
    for param, col in [("collection", "collections"), ("tag", "tags")]:
        if params.get(param):
            value = bind(params[param])
            conditions.append(
                "(EXISTS(SELECT 1 FROM json_each("
                + col
                + ") WHERE value="
                + value
                + ")"
                + (
                    " OR EXISTS(SELECT 1 FROM json_each(auto_tags) WHERE value="
                    + value
                    + ")"
                    if param == "tag"
                    else ""
                )
                + ")"
            )
    if params.get("agent"):
        conditions.append(
            "norm(json_extract(source,'$.agent'))=" + bind(normalized(params["agent"]))
        )
    if params.get("review") in ("pending", "clear"):
        conditions.append(
            "open_comments" + (">0" if params["review"] == "pending" else "=0")
        )
    search = params.get("q", "")
    if len(search) > 300:
        raise ValueError("Query too long")
    if search:
        expression = match_query(search)
        words = normalized(search).split()
        meta = "norm(title||' '||space||' '||category||' '||tags||' '||auto_tags||' '||collections||' '||source)"
        matching = (
            " AND ".join("instr(" + meta + "," + bind(w) + ")>0" for w in words) or "0"
        )
        if expression:
            fts = bind(expression)
            sql = sql.replace(
                "WITH ",
                "WITH fulltext AS MATERIALIZED (SELECT artifact,bm25(artifact_fts,0,0,8,3,1) AS score,snippet(artifact_fts,4,'','',' … ',26) AS hit FROM artifact_fts WHERE artifact_fts MATCH "
                + fts
                + "), ",
                1,
            )
            sql = sql.replace(
                "0 AS rank,'' AS excerpt",
                "COALESCE(f.score,0) AS rank,COALESCE(f.hit,'') AS excerpt",
            ).replace(
                "FROM counted WHERE 1=1",
                "FROM counted LEFT JOIN fulltext f ON f.artifact=counted.id WHERE 1=1",
            )
            conditions.append("(f.artifact IS NOT NULL OR (" + matching + "))")
        else:
            conditions.append("(" + matching + ")")
    filters = parse(params.get("filters"))
    compiled = []
    cols = {
        "title": "norm(title)",
        "space": "norm(space)",
        "category": "norm(category)",
        "visibility": "norm(visibility)",
        "comments": "open_comments",
        "agent": "norm(json_extract(source,'$.agent'))",
        "updated": "date(updated,'unixepoch')",
    }
    for rule in filters["rules"]:
        col = cols[rule["column"]]
        op = rule["operator"]
        val = rule.get("value", "")
        numeric = rule["column"] == "comments"

        def value(v):
            if numeric:
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return None
            return normalized(str(v))

        if op == "empty":
            expr = "(" + col + " IS NULL OR " + col + "='')"
        elif op == "in":
            expr = (
                col + " IN (" + ",".join(bind(value(v)) for v in val) + ")"
                if isinstance(val, list) and val
                else "0"
            )
        elif op == "contains":
            expr = "instr(COALESCE(" + col + ",'')," + bind(value(val)) + ")>0"
        elif op == "between":
            expr = (
                col
                + " BETWEEN "
                + bind(value(val))
                + " AND "
                + bind(value(rule.get("upper", "")))
            )
        else:
            expr = col + {"eq": "=", "gte": ">=", "lte": "<="}[op] + bind(value(val))
        compiled.append("(" + expr + ")")
    if compiled:
        conditions.append(
            "("
            + (" OR " if filters.get("join") == "or" else " AND ").join(compiled)
            + ")"
        )
    sql += "".join(" AND " + c for c in conditions) + ") "
    summary = dict(
        db.execute(
            sql
            + "SELECT count(*) total,COALESCE(sum(open_comments),0) open_comments,COALESCE(sum(visibility<>'private'),0) shared FROM counted",
            p,
        ).fetchone()
    )
    total = db.execute(sql + "SELECT count(*) FROM searched", p).fetchone()[0]
    facets = {}
    for name, column in [
        ("spaces", "space"),
        ("categories", "category"),
        ("agents", "json_extract(source,'$.agent')"),
    ]:
        facets[name] = [
            r[0]
            for r in db.execute(
                sql
                + "SELECT DISTINCT "
                + column
                + " FROM visible WHERE "
                + column
                + " IS NOT NULL AND "
                + column
                + "<>'' ORDER BY 1",
                p,
            )
        ]
    for name, column in [("tags", "tags"), ("collections", "collections")]:
        facets[name] = [
            r[0]
            for r in db.execute(
                sql
                + "SELECT DISTINCT j.value FROM visible v,json_each(v."
                + column
                + ") j ORDER BY 1",
                p,
            )
        ]
    facets["tags"] = [
        r[0]
        for r in db.execute(
            sql
            + "SELECT j.value FROM visible v,json_each(v.tags) j UNION SELECT j.value FROM visible v,json_each(v.auto_tags) j ORDER BY 1",
            p,
        )
    ]
    sort = params.get("sort", "recent")
    columns = {
        "recent": ["updated", "id"],
        "title": ["norm(title)", "id"],
        "relevance": ["rank", "-updated", "id"],
        "comments": ["open_comments", "updated", "id"],
        "space": ["norm(space)", "norm(title)", "id"],
        "category": ["norm(category)", "norm(title)", "id"],
        "agent": ["norm(json_extract(source,'$.agent'))", "norm(title)", "id"],
    }
    if sort not in columns:
        raise ValueError("Unknown sort")
    direction = params.get("direction") or (
        "asc"
        if sort in ("title", "relevance", "space", "category", "agent")
        else "desc"
    )
    if direction not in ("asc", "desc"):
        raise ValueError("Unknown direction")
    limit = int(params.get("limit", 60))
    limit = 121 if params.get("graph") == "1" else limit
    if not 1 <= limit <= 121:
        raise ValueError("Invalid limit")
    signature = hashlib.sha256(
        json.dumps(
            {
                k: params.get(k, "")
                for k in [
                    "q",
                    "view",
                    "space",
                    "access",
                    "sort",
                    "document_id",
                    "collection",
                    "tag",
                    "category",
                    "agent",
                    "review",
                    "direction",
                    "filters",
                ]
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()[:16]
    after = ""
    keycols = columns[sort]
    if params.get("cursor"):
        if len(params["cursor"]) > 2048:
            raise ValueError("Invalid cursor")
        cursor = json.loads(base64.urlsafe_b64decode(params["cursor"]).decode())
        if cursor["scope"] != signature or len(cursor["after"]) != len(keycols):
            raise ValueError("Query changed")
        after = (
            " WHERE ("
            + ",".join(keycols)
            + ")"
            + ("<" if direction == "desc" else ">")
            + "("
            + ",".join(bind(v) for v in cursor["after"])
            + ")"
        )
    select_keys = ",".join(c + " AS key" + str(i) for i, c in enumerate(keycols))
    rows = [
        dict(r)
        for r in db.execute(
            sql
            + "SELECT *, "
            + select_keys
            + " FROM searched"
            + after
            + " ORDER BY "
            + ",".join(c + " " + direction for c in keycols)
            + " LIMIT "
            + str(limit + 1),
            p,
        )
    ]
    cursor = None
    if len(rows) > limit:
        cursor = base64.urlsafe_b64encode(
            json.dumps(
                {
                    "scope": signature,
                    "after": [
                        rows[limit - 1]["key" + str(i)] for i in range(len(keycols))
                    ],
                }
            ).encode()
        ).decode()
    items = []
    for row in rows[:limit]:
        for i in range(len(keycols)):
            row.pop("key" + str(i))
        for name in ("tags", "collections", "auto_tags", "classification", "source"):
            row[name] = json.loads(row[name])
        for name in ("archived", "automatic", "category_manual"):
            row[name] = bool(row[name])
        role = row.pop("access_role")
        row.pop("explicit_role")
        row.pop("version_state")
        row["permissions"] = {
            "read": True,
            "review": bool(role) or row["comments"] == "readers",
            "comment": role in ("owner", "editor", "commenter")
            or (not role and row["comments"] == "readers"),
            "edit": role in ("owner", "editor"),
            "manage": role == "owner",
            "role": role,
        }
        items.append(row)
    return {
        "artifacts": items,
        "total": total,
        "next_cursor": cursor,
        "summary": summary,
        **facets,
    }
