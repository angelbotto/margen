"""Versioned capabilities for independent artifact formats; originals remain downloads."""

import base64
import io
import zipfile
import re
from html.parser import HTMLParser
from pathlib import PurePosixPath
from fastapi import HTTPException

CAPABILITIES = {
    "document": {
        "label": "Artículo",
        "navigation": "continuous",
        "comments": True,
        "search": True,
    },
    "chapters": {
        "label": "Documento multipágina",
        "navigation": "chapters",
        "comments": True,
        "search": True,
    },
    "presentation": {
        "label": "Presentación",
        "navigation": "authored-slides",
        "comments": True,
        "search": True,
    },
    "board": {
        "label": "Tablero",
        "navigation": "authored-canvas",
        "comments": True,
        "search": True,
    },
    "pdf": {
        "label": "PDF",
        "navigation": "page-preview",
        "comments": True,
        "search": True,
        "original": True,
    },
    "pptx": {
        "label": "PowerPoint",
        "navigation": "slide-preview",
        "comments": True,
        "search": True,
        "original": True,
    },
    "html": {
        "label": "HTML",
        "navigation": "authored",
        "comments": True,
        "search": True,
    },
}


class Inspect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.format = ""
        self.slides = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("name") == "margen-format":
            self.format = a.get("content", "")
        if "slide" in a.get("class", "").split():
            self.slides += 1


def describe(content):
    p = Inspect()
    p.feed(content)
    kind = (
        p.format
        if p.format in CAPABILITIES
        else "presentation" if p.slides > 1 else "html"
    )
    return {
        "version": 1,
        "kind": kind,
        **CAPABILITIES[kind],
        "pages": p.slides or None,
        "editable_original": False,
    }


def attachments(value):
    if not isinstance(value, list) or len(value) > 10:
        raise HTTPException(422, "Hasta 10 adjuntos por versión.")
    result = {}
    total = 0
    for item in value:
        if not isinstance(item, dict):
            raise HTTPException(422, "Adjunto inválido.")
        name = item.get("name", "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,150}", name) or PurePosixPath(
            name
        ).suffix.lower() not in (".pdf", ".pptx"):
            raise HTTPException(
                422, "Adjunta un PDF o PPTX con un nombre de archivo simple."
            )
        try:
            data = base64.b64decode(item.get("data", ""), validate=True)
        except (ValueError, TypeError):
            raise HTTPException(422, "Adjunto inválido.")
        total += len(data)
        if total > 12 * 1024 * 1024:
            raise HTTPException(
                422, "Los originales deben ocupar menos de 12 MB en total."
            )
        if name.lower().endswith(".pdf") and not data.startswith(b"%PDF-"):
            raise HTTPException(422, "PDF inválido.")
        if name.lower().endswith(".pptx") and not data.startswith(b"PK\x03\x04"):
            raise HTTPException(422, "PPTX inválido.")
        if name.lower().endswith(".pptx"):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    if (
                        "[Content_Types].xml" not in z.namelist()
                        or "ppt/presentation.xml" not in z.namelist()
                    ):
                        raise ValueError()
            except (zipfile.BadZipFile, ValueError):
                raise HTTPException(422, "PPTX inválido.")
        if name in result:
            raise HTTPException(422, "Nombre de adjunto repetido.")
        result[name] = data
    return result


def migrate(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS version_formats(version TEXT PRIMARY KEY REFERENCES versions(id),capabilities TEXT NOT NULL)"
    )
