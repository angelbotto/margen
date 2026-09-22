"""Exact, verified-email domain grants. Domain access never grants editing."""

import re
import hashlib
import json

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
