"""Exact, verified-email domain grants. Domain access never grants editing."""

import re
import hashlib
import json
import os

DOMAIN = re.compile(
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?"
)


def normalize_domain(value):
    if not isinstance(value, str):
        raise ValueError("Escribe un dominio como empresa.com.")
    value = value.strip().lower().removeprefix("@")
    if len(value) > 253 or not DOMAIN.fullmatch(value):
        raise ValueError(
            "Usa un dominio sin enlaces, comodines ni espacios: empresa.com."
        )
    return value


def verified_domain(user):
    if not user or not user.get("verified"):
        return ""
    email = user.get("email") or ""
    if email.count("@") != 1:
        return ""
    try:
        return normalize_domain(email.rsplit("@", 1)[1])
    except ValueError:
        return ""



def owner_aliases():
    """Operator-configured addresses for one identity, never client claims."""
    return list(dict.fromkeys(e.strip().lower() for e in
        os.environ.get("BOTTIFACT_OWNER_ALIASES", "").split(",") if e.strip()))


def verified_emails(user):
    if not user or not user.get("verified"):
        return []
    email = (user.get("email") or "").strip().lower()
    aliases = owner_aliases()
    return aliases if email and email in aliases else ([email] if email else [])


def identity_bindings(user):
    emails = verified_emails(user)
    domains = sorted({verified_domain({"verified": True, "email": e}) for e in emails} - {""})
    return {"identity_emails": json.dumps(emails), "identity_domains": json.dumps(domains)}


# Collapse grants before joining artifacts: multiple matching addresses/domains
# must not duplicate rows, counts or keyset cursors. Any personal grant takes
# precedence; conflicting personal roles use the most restrictive explicit role.
_IDENTITY_GRANTS_TEMPLATE = """
identity_personal AS (
    SELECT artifact, CASE MIN(CASE role WHEN 'viewer' THEN 1 WHEN 'commenter' THEN 2 ELSE 3 END)
        WHEN 1 THEN 'viewer' WHEN 2 THEN 'commenter' ELSE 'editor' END AS role
    FROM grants WHERE {scope}email IN (SELECT value FROM json_each(:identity_emails)) GROUP BY artifact
), identity_domains AS (
    SELECT artifact, CASE MAX(CASE role WHEN 'commenter' THEN 2 ELSE 1 END)
        WHEN 2 THEN 'commenter' ELSE 'viewer' END AS role
    FROM domain_grants WHERE {scope}domain IN (SELECT value FROM json_each(:identity_domains)) GROUP BY artifact
), identity_grants AS (
    SELECT artifact,role FROM identity_personal
    UNION ALL
    SELECT d.artifact,d.role FROM identity_domains d
    WHERE NOT EXISTS(SELECT 1 FROM identity_personal p WHERE p.artifact=d.artifact)
)
"""


IDENTITY_GRANTS_CTE = _IDENTITY_GRANTS_TEMPLATE.format(scope="")

def explicit_role(db, artifact_id, user):
    bindings = {**identity_bindings(user), "artifact": artifact_id}
    row = db.execute("WITH " + _IDENTITY_GRANTS_TEMPLATE.format(scope="artifact=:artifact AND ") +
        " SELECT role FROM identity_grants WHERE artifact=:artifact", bindings).fetchone()
    return row["role"] if row else None

def parse_grants(value):
    if not isinstance(value, list) or len(value) > 25:
        raise ValueError("Máximo 25 dominios por artefacto.")
    result = {}
    for grant in value:
        if not isinstance(grant, dict) or grant.get("role") not in (
            "viewer",
            "commenter",
        ):
            raise ValueError(
                "Un dominio puede ver o comentar. La edición se asigna por correo."
            )
        domain = normalize_domain(grant.get("domain"))
        if domain in result:
            raise ValueError("Este dominio está repetido: " + domain)
        result[domain] = grant["role"]
    return result


def access_revision(db, artifact):
    """Compare-and-save token; excludes content and never grants access itself."""
    state = {key: artifact[key] for key in ("visibility", "comments", "guests")}
    state["grants"] = [
        dict(r)
        for r in db.execute(
            "SELECT email,role FROM grants WHERE artifact=? ORDER BY email",
            (artifact["id"],),
        )
    ]
    state["domains"] = [
        dict(r)
        for r in db.execute(
            "SELECT domain,role FROM domain_grants WHERE artifact=? ORDER BY domain",
            (artifact["id"],),
        )
    ]
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
