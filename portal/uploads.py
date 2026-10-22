"""Importación administrativa de HTML, PDF y sitios estáticos ZIP.

Cada subida se convierte en un único HTML autocontenido y pasa por publish(): mismos
permisos, versiones, expected_current y el render aislado (origen opaco, sin red).
Nunca se sirve contenido subido desde el origen del portal ni se ejecuta código del ZIP.
Contrato y límites: docs/upload-contract.md.
"""

import base64
import hashlib
import html as html_module
import mimetypes
import os
import posixpath
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time
import unicodedata
import uuid
import zipfile
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool

MiB = 1024 * 1024
LIMITS = {
    "upload_bytes": 15 * MiB,
    "html_bytes": 15 * MiB,
    "output_bytes": 20 * MiB,
    "pdf_bytes": 12 * MiB,
    "pdf_pages": 80,
    "zip_bytes": 15 * MiB,
    "zip_entries": 400,
    "zip_total_bytes": 50 * MiB,
    "zip_entry_bytes": 20 * MiB,
    "zip_ratio": 100,
}
# Plazo de toda la conversión (metadatos, páginas y texto) y memoria virtual por proceso
# de Poppler. Producción: contenedor de 768 MiB y /tmp tmpfs de 32 MiB, un PDF a la vez.
PDF_TIMEOUT = 90
PDF_CHILD_MEMORY = 384 * MiB
DOCUMENT_ID = re.compile(r'<meta\s+name=["\']nota-documento["\']\s+content=["\']([a-zA-Z0-9_-]{1,120})["\']')
ASSET_TYPES = {
    ".html": "text/html", ".htm": "text/html", ".css": "text/css", ".js": "text/javascript",
    ".mjs": "text/javascript", ".json": "application/json", ".txt": "text/plain",
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif", ".ico": "image/x-icon",
    ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf", ".otf": "font/otf",
    ".mp3": "audio/mpeg", ".mp4": "video/mp4", ".webm": "video/webm",
}
# Archivos de servidor o de compilación: un sitio estático no los necesita y no se ejecutan.
DENIED_NAMES = {"package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "netlify.toml",
                "_redirects", "_headers", ".htaccess", "vercel.json", "dockerfile", "makefile"}
# Atributos que cargan o navegan a otra página: si apuntan a una página del ZIP, el
# documento publicado quedaría roto (una página por artefacto).
NAVIGATING = {"src": ("iframe", "frame", "embed"), "data": ("object",), "action": ("form",), "formaction": ("button", "input")}
SKIPPED = re.compile(r"(^|/)(__MACOSX/|\.DS_Store$|Thumbs\.db$)")
PDF_SLOTS = threading.BoundedSemaphore(1)
UPLOAD_SLOTS = threading.BoundedSemaphore(2)


def reject(message):
    raise HTTPException(422, message)


def decode(body):
    name = body.get("name")
    if not isinstance(name, str) or not 0 < len(name) <= 150 or "/" in name or "\\" in name or any(ord(c) < 32 for c in name):
        reject("Nombre de archivo inválido.")
    data = body.get("data")
    if not isinstance(data, str) or not data or len(data) > (LIMITS["upload_bytes"] + 2) // 3 * 4 + 4:
        reject("El archivo debe ocupar menos de 15 MB.")
    try:
        raw = base64.b64decode(data, validate=True)
    except (ValueError, TypeError):
        reject("El archivo no está codificado en base64.")
    if not raw or len(raw) > LIMITS["upload_bytes"]:
        reject("El archivo debe ocupar menos de 15 MB.")
    entry = body.get("entry")
    if entry is not None and (not isinstance(entry, str) or not 0 < len(entry) <= 512):
        reject("Página de entrada inválida.")
    return name, raw, entry


def kind_of(name, raw):
    suffix = PurePosixPath(name).suffix.lower()
    if suffix == ".pdf":
        if not raw.startswith(b"%PDF-"):
            reject("El archivo .pdf no es un PDF.")
        return "pdf"
    if suffix == ".zip":
        if not raw.startswith(b"PK\x03\x04"):
            reject("El archivo .zip no es un ZIP.")
        return "zip"
    if suffix in (".html", ".htm"):
        if raw.startswith((b"%PDF-", b"PK\x03\x04")):
            reject("El archivo .html contiene un PDF o un ZIP.")
        return "html"
    reject("Sube un archivo HTML, PDF o ZIP.")


def text_of(raw, label):
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    if b"\x00" in raw:
        reject(label + " contiene bytes nulos.")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        reject(label + " debe estar guardado como UTF-8.")


HEAD_TAGS = {"html", "head", "title", "meta", "link", "style", "script", "base", "noscript", "template"}


class Metadata(HTMLParser):
    """Título, documento-id y posición de <head> leídos como HTML: nunca dentro de
    comentarios, script, style ni template. Se detiene al llegar al cuerpo."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.template = 0
        self.active, self.text = None, ""
        self.values = {"title": "", "h1": ""}
        self.document_id = None
        self.head = None
        self.body = False
        self.done = False

    def handle_starttag(self, tag, attrs, closed=False):
        if tag == "template" and not closed:
            self.template += 1
        if self.template:
            return
        if tag == "head" and self.head is None and not self.body:
            line, column = self.getpos()
            self.head = (line, column, len(self.get_starttag_text()))
        elif tag == "body" or (tag not in HEAD_TAGS and not self.body):
            # Como el navegador: una etiqueta que no va en <head> abre el cuerpo.
            self.body = True
            self.done = bool(self.values["title"])
        elif tag == "meta" and self.document_id is None:
            values = dict(attrs)
            if values.get("name") == "nota-documento" and re.fullmatch(r"[a-zA-Z0-9_-]{1,120}", values.get("content") or ""):
                self.document_id = values["content"]
        if tag in self.values and not self.values[tag] and not closed:
            self.active, self.text = tag, ""

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, True)

    def handle_endtag(self, tag):
        if tag == "template" and self.template:
            self.template -= 1
        elif tag == self.active:
            # Sólo un elemento cerrado cuenta: un <title> sin cierre no es el título.
            self.values[tag], self.active = self.text, None
            self.done = self.body and bool(self.values["title"] or self.values["h1"])

    def handle_data(self, data):
        if self.active and not self.template:
            self.text = (self.text + data[:200])[:200]


def metadata(content):
    parser = Metadata()
    # Parsing incremental: el cuerpo de una página grande no se recorre. HTMLParser es
    # lineal y libera el GIL entre bloques, al contrario que una regex sobre todo el texto.
    for start in range(0, len(content), 65536):
        parser.feed(content[start:start + 65536])
        if parser.done or (parser.body and start >= 65536 * 4):
            break
    else:
        parser.close()
    head = None
    if parser.head:
        line, column, length = parser.head
        offset = 0
        for _ in range(line - 1):
            offset = content.index("\n", offset) + 1
        head = offset + column + length
    title = " ".join((parser.values["title"] or parser.values["h1"]).split())
    return {"title": title[:200], "document_id": parser.document_id, "head": head}


def title_of(content, fallback):
    return metadata(content)["title"] or fallback[:200]


def with_document_id(content, document_id):
    """Conserva el documento-id declarado o inserta uno al abrir el <head> real.
    publish() lee la primera coincidencia textual: debe ser la misma identidad."""
    found = metadata(content)
    if found["document_id"]:
        out, document_id = content, found["document_id"]
    else:
        meta = '<meta name="nota-documento" content="' + document_id + '">'
        doctype = re.match(r"\s*<!doctype[^>]{0,1024}>", content, re.I)
        position = found["head"] if found["head"] is not None else doctype.end() if doctype else 0
        out = content[:position] + meta + content[position:]
    first = DOCUMENT_ID.search(out)
    if not first or first[1] != document_id:
        reject('El HTML tiene un nota-documento dentro de un comentario o script, o con un formato que el portal no lee. '
               'Escribe <meta name="nota-documento" content="…"> en el <head> o quítalo.')
    return out


def declared_id(content):
    return metadata(content)["document_id"]


def warnings_for(content):
    content = content[:32768]  # Advisory only; CSP enforces the entire document.
    found = []
    if re.search(r"""\b(?:src|href)\s*=\s*["']?(?:https?:)?//""", content, re.I):
        found.append("Hay recursos remotos: el lector no los descarga y la mayoría quedarán bloqueados.")
    if re.search(r"<form\b", content, re.I):
        found.append("Los formularios no envían datos desde el lector.")
    if re.search(r"<meta[^>]+http-equiv\s*=\s*[\"']?refresh", content, re.I):
        found.append("La página tiene una redirección automática (meta refresh).")
    if re.search(r"\bfetch\s*\(|XMLHttpRequest", content):
        found.append("El JavaScript que pide datos por red no funcionará: el lector no tiene conexión.")
    return found


# --- PDF -------------------------------------------------------------------

def poppler():
    tools = {name: shutil.which(name) for name in ("pdfinfo", "pdftoppm", "pdftotext")}
    return tools if all(tools.values()) else None


PDF_HEAVY = ("El PDF es demasiado pesado para generar la vista previa en este servidor (memoria, tiempo o tamaño). "
             "Reduce la resolución de sus imágenes, divídelo en partes o súbelo como adjunto de un HTML.")
PDF_SLOW = "El PDF tardó demasiado en procesarse (máximo " + str(PDF_TIMEOUT) + " s por documento). Divídelo en partes o reduce sus imágenes."


def bounded_run(command, folder, deadline):
    """Ejecuta Poppler con límites del sistema, entorno vacío y grupo de procesos propio.
    deadline es compartido por toda la conversión, metadatos incluidos."""
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        reject(PDF_SLOW)
    # ulimit en un sh intermedio evita preexec_fn dentro del servidor multihilo. La memoria
    # por proceso deja sitio al portal dentro de los 768 MiB del contenedor.
    limits = ("ulimit -t " + str(min(60, int(seconds) + 1)) + "; ulimit -f 4096; ulimit -n 64; ulimit -v "
              + str(PDF_CHILD_MEMORY // 1024) + " 2>/dev/null; exec \"$@\"")
    # stdout/stderr are bounded files too, never an unbounded PIPE allocation.
    with tempfile.TemporaryFile(dir=folder) as output, tempfile.TemporaryFile(dir=folder) as errors:
        process = subprocess.Popen(["/bin/sh", "-c", limits, "sh", *command], cwd=folder, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=errors, start_new_session=True)
        try:
            process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            reject(PDF_SLOW)
        if process.returncode != 0:
            errors.seek(0)
            detail = errors.read(4096).decode("utf-8", "replace").lower()
            # Señal (CPU, tamaño de archivo, abort por memoria) o falta de memoria declarada.
            if process.returncode < 0 or process.returncode >= 128 or "memory" in detail or "bad_alloc" in detail:
                reject(PDF_HEAVY)
            reject("No se pudo leer el PDF; puede estar dañado o protegido con contraseña.")
        output.seek(0)
        return output.read(65536).decode("utf-8", "replace")


def pdf_info(raw, folder, tools, deadline):
    source = Path(folder) / "original.pdf"
    source.write_bytes(raw)
    info = bounded_run([tools["pdfinfo"], str(source)], folder, min(deadline, time.monotonic() + 30))
    pages = re.search(r"^Pages:\s+(\d+)", info, re.M)
    if not pages or not 0 < int(pages[1]) <= LIMITS["pdf_pages"]:
        reject("La vista previa admite PDF de 1 a 80 páginas.")
    title = re.search(r"^Title:\s+(.+)$", info, re.M)
    return source, int(pages[1]), (title[1].strip() if title else "")


def inspect_pdf(name, raw):
    if len(raw) > LIMITS["pdf_bytes"]:
        reject("El PDF debe ocupar menos de 12 MB.")
    tools = poppler()
    report = {"kind": "pdf", "pages": None, "preview": "visual" if tools else "none", "warnings": []}
    title = ""
    if tools:
        if not PDF_SLOTS.acquire(blocking=False):
            raise HTTPException(503, "Hay otros PDF en proceso. Intenta en un momento.")
        try:
            with tempfile.TemporaryDirectory(prefix="margen-upload-") as folder:
                _, report["pages"], title = pdf_info(raw, folder, tools, time.monotonic() + 30)
        finally:
            PDF_SLOTS.release()
    else:
        report["warnings"].append("Este servidor no tiene Poppler: no puede generar la vista previa del PDF.")
    report["title"] = title[:200] or PurePosixPath(name).stem[:200]
    report["files"] = [{"path": "original.pdf", "size": len(raw), "type": "application/pdf", "role": "original"}]
    return report


def build_pdf(name, raw, document_id, title):
    tools = poppler()
    if not tools:
        reject("Este servidor no tiene Poppler: no puede generar la vista previa del PDF.")
    if not PDF_SLOTS.acquire(blocking=False):
        raise HTTPException(503, "Hay otros PDF en proceso. Intenta en un momento.")
    try:
        with tempfile.TemporaryDirectory(prefix="margen-upload-") as folder:
            root = Path(folder)
            deadline = time.monotonic() + PDF_TIMEOUT
            source, count, _ = pdf_info(raw, folder, tools, deadline)
            scale = "1400" if count <= 20 else "1000"
            pages, used = [], 8192
            # One page on disk at a time fits the production 32 MiB tmpfs,
            # including a 12 MiB original. Reserve output before base64 encoding.
            for i in range(1, count + 1):
                path = root / "page.jpg"
                bounded_run([tools["pdftoppm"], "-f", str(i), "-l", str(i), "-singlefile", "-jpeg", "-scale-to", scale,
                             "-jpegopt", "quality=72", str(source), str(root / "page")], folder, deadline)
                if not path.is_file(): reject("No se pudo generar la vista previa del PDF.")
                text = bounded_run([tools["pdftotext"], "-f", str(i), "-l", str(i), "-enc", "UTF-8", str(source), "-"], folder, deadline).strip()
                used += ((path.stat().st_size + 2) // 3) * 4 + len(html_module.escape(text).encode()) + 512
                if used > LIMITS["output_bytes"]: reject("La vista previa del PDF supera 20 MB.")
                pages.append('<figure id="page-' + str(i) + '"><img alt="Página ' + str(i) + '" src="data:image/jpeg;base64,'
                             + base64.b64encode(path.read_bytes()).decode() + '"><figcaption>Página ' + str(i) + "</figcaption></figure>"
                             + ("<details><summary>Texto de la página</summary><p>" + html_module.escape(text) + "</p></details>" if text else ""))
                path.unlink()
    finally:
        PDF_SLOTS.release()
    escaped = html_module.escape(title)
    # Misma presentación que scripts/import_document.py.
    content = ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               '<meta name="nota-documento" content="' + document_id + '"><meta name="margen-format" content="pdf"><title>' + escaped + "</title>"
               "<style>body{margin:0;background:#e9e6e0;color:#282623;font:16px/1.6 system-ui;padding:24px 20px 110px}main{max-width:1080px;margin:auto}"
               "header{margin:0 0 24px}img{display:block;width:100%;height:auto}figure{margin:0 0 24px;background:white;padding:12px;border:1px solid #d7d1c8}"
               "p{white-space:pre-wrap}figcaption,summary{font-size:12px;color:#625c53}details{margin-bottom:24px}a{color:inherit}</style></head>"
               "<body><main><header><h1>" + escaped + "</h1><p>Vista por páginas. El original conserva su formato.</p>"
               '<a href="original.pdf" data-margen-original="original.pdf">Descargar original</a></header>' + "".join(pages) + "</main></body></html>")
    if len(content.encode()) > LIMITS["output_bytes"]:
        reject("La vista previa del PDF supera 20 MB; reduce el número de páginas.")
    return content, [{"name": "original.pdf", "data": base64.b64encode(raw).decode()}]


# --- ZIP -------------------------------------------------------------------

def safe_path(name):
    if not name or len(name) > 512 or "\\" in name or name.startswith("/") or re.match(r"[A-Za-z]:", name) or any(ord(c) < 32 or ord(c) == 127 for c in name):
        reject("El ZIP contiene una ruta no permitida: " + name[:120])
    parts = name.rstrip("/").split("/")
    if any(part in ("", ".", "..") or len(part) > 255 for part in parts):
        reject("El ZIP contiene una ruta no permitida: " + name[:120])
    return "/".join(parts)


def read_zip(raw):
    if len(raw) > LIMITS["zip_bytes"]:
        reject("El ZIP debe ocupar menos de 15 MB.")
    try:
        archive = zipfile.ZipFile(BytesIO(raw))
        infos = archive.infolist()
    except (zipfile.BadZipFile, zipfile.LargeZipFile, ValueError, OSError):
        reject("ZIP inválido o dañado.")
    if not infos or len(infos) > LIMITS["zip_entries"]:
        reject("El ZIP debe tener entre 1 y 400 entradas.")
    files, skipped, seen, total = {}, [], set(), 0
    for info in infos:
        if info.flag_bits & 0x1:
            reject("El ZIP está cifrado.")
        mode = info.external_attr >> 16
        if info.create_system == 3 and stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
            reject("El ZIP contiene enlaces simbólicos o archivos especiales: " + info.filename[:120])
        path = safe_path(info.filename)
        key = unicodedata.normalize("NFC", path).casefold()
        if key in seen:
            reject("El ZIP repite el nombre " + path[:120] + ".")
        seen.add(key)
        if info.is_dir():
            continue
        if SKIPPED.search(path):
            skipped.append({"path": path, "size": info.file_size, "type": "", "role": "skipped"})
            continue
        base = PurePosixPath(path).name.lower()
        suffix = PurePosixPath(path).suffix.lower()
        if base in DENIED_NAMES or "node_modules" in path.split("/") or base.startswith("."):
            reject("Sólo se aceptan sitios estáticos ya compilados; el ZIP incluye " + path[:120] + ".")
        if suffix not in ASSET_TYPES:
            reject("Tipo de archivo no permitido en el ZIP: " + path[:120] + ". Se aceptan HTML, CSS, JS, JSON, imágenes, fuentes y medios.")
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            reject("Compresión no soportada en " + path[:120] + ".")
        if info.file_size > LIMITS["zip_entry_bytes"]:
            reject("El archivo " + path[:120] + " supera 20 MB.")
        if info.file_size > MiB and info.file_size > LIMITS["zip_ratio"] * max(info.compress_size, 1):
            reject("El ZIP tiene una compresión anómala en " + path[:120] + ".")
        total += info.file_size
        if total > LIMITS["zip_total_bytes"]:
            reject("El ZIP descomprimido supera 50 MB.")
        files[path] = info
    if total > LIMITS["zip_ratio"] * len(raw) and total > MiB:
        reject("El ZIP tiene una compresión anómala.")
    if not files:
        reject("El ZIP no contiene archivos.")
    contents = {}
    for path, info in files.items():
        try:
            with archive.open(info) as stream:
                data = stream.read(info.file_size + 1)
        except (zipfile.BadZipFile, ValueError, OSError, EOFError, NotImplementedError):
            reject("ZIP dañado en " + path[:120] + ".")
        if len(data) != info.file_size:
            reject("ZIP dañado en " + path[:120] + ".")
        contents[path] = data
    # Un ZIP de una carpeta publica la carpeta como raíz del sitio.
    tops = {p.split("/", 1)[0] for p in contents}
    if len(tops) == 1 and all("/" in p for p in contents):
        prefix = next(iter(tops)) + "/"
        contents = {p[len(prefix):]: v for p, v in contents.items()}
    return contents, skipped


def is_local(ref):
    ref = ref.strip()
    if not ref or ref.startswith(("#", "//")) or urlsplit(ref).scheme:
        return False
    return True


def script_text(code):
    # "<!--" seguido de "<script" deja al parser HTML en estado double-escaped y se
    # traga el resto de la página; "</script" lo cerraría antes de tiempo.
    return re.sub(r"<(/script|!--)", r"<\\\1", code, flags=re.I)


def resolve(ref, base):
    path = unquote(urlsplit(ref.strip()).path)
    if not path:
        return None
    joined = path.lstrip("/") if path.startswith("/") else posixpath.join(posixpath.dirname(base), path)
    normal = posixpath.normpath(joined)
    return None if normal.startswith("../") or normal == ".." else normal


class Tags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.styles, self.scripts = [], [], {}

    def handle_starttag(self, tag, attrs):
        if len(self.tags) >= 30000:
            reject("La página contiene demasiados elementos para importar (máximo 30 000).")
        self.tags.append((self.getpos(), self.get_starttag_text(), tag, attrs))

    handle_startendtag = handle_starttag

    def handle_data(self, data):
        if self.lasttag == "style" and self.cdata_elem == "style":
            self.styles.append((self.getpos(), data))
        elif self.cdata_elem == "script" and self.tags and self.tags[-1][2] == "script":
            # Cuerpo del último <script>: se descarta si su src se incrusta.
            index = len(self.tags) - 1
            pos, text = self.scripts.get(index, (self.getpos(), ""))
            self.scripts[index] = (pos, text + data)


class Site:
    """Incrusta como data: los recursos locales de la página de entrada; no descarga nada."""

    def __init__(self, contents, entry):
        self.contents, self.entry = contents, entry
        self.used, self.missing, self.pages = set(), set(), set()
        self.warnings = []
        self.remaining = LIMITS["output_bytes"] - len(contents[entry])
        self.encoded = {}
        self.css_imports = 0
        self.inlined_script = False

    def spend(self, size):
        # Conservative work/output budget, charged BEFORE each expansion, including
        # repeated references. A compressed-size check cannot bound this work.
        self.remaining -= size
        if self.remaining < 0:
            reject("El sitio con sus recursos incrustados supera el límite de expansión de 20 MB.")

    def data_uri(self, path):
        self.used.add(path)
        kind = ASSET_TYPES.get(PurePosixPath(path).suffix.lower()) or mimetypes.guess_type(path)[0] or "application/octet-stream"
        self.spend(5 + len(kind) + 8 + ((len(self.contents[path]) + 2) // 3) * 4)
        if path not in self.encoded:
            self.encoded[path] = "data:" + kind + ";base64," + base64.b64encode(self.contents[path]).decode()
        return self.encoded[path]

    def asset(self, ref, base):
        if not is_local(ref):
            return ref
        path = resolve(ref, base)
        if path is None or path not in self.contents:
            self.missing.add(ref.strip()[:200])
            return ref
        if PurePosixPath(path).suffix.lower() in (".html", ".htm"):
            self.pages.add(path)
            return ref
        return self.data_uri(path)

    def page(self, ref, base):
        """Devuelve la página del ZIP a la que navega ref (about/, /about, about.html…), o None."""
        if not is_local(ref):
            return None
        path = resolve(ref, base)
        if path is None:
            return None
        directory = "" if path == "." else path + "/"
        for candidate in (path, path + ".html", path + ".htm", directory + "index.html", directory + "index.htm"):
            if candidate in self.contents and PurePosixPath(candidate).suffix.lower() in (".html", ".htm"):
                return candidate
        return None

    def navigates(self, ref, base):
        target = self.page(ref, base)
        if target and target != base:
            self.pages.add(target)
        return target is not None

    def css(self, text, base, depth=0):
        self.spend(len(text.encode()))
        if text.lower().count("@import") > 128:
            reject("El sitio contiene demasiadas importaciones CSS (máximo 128).")
        def imported(match):
            self.css_imports += 1
            if self.css_imports > 128:
                reject("El sitio contiene demasiadas importaciones CSS (máximo 128).")
            ref = match[1] or match[2]
            path = resolve(ref, base) if is_local(ref) else None
            if path in self.contents and path.endswith(".css") and depth < 4:
                self.used.add(path)
                return self.css(text_of(self.contents[path], path), path, depth + 1)
            if is_local(ref):
                self.missing.add(ref[:200])
            return match[0]
        text = re.sub(r"""@import\s+(?:url\(\s*["']?([^"'()]+)["']?\s*\)|["']([^"']+)["'])[^;]*;""", imported, text, flags=re.I)
        return re.sub(r"""url\(\s*(["']?)([^"'()]+)\1\s*\)""", lambda m: 'url("' + self.asset(m[2], base) + '")' if is_local(m[2]) else m[0], text, flags=re.I)

    def srcset(self, value, base):
        out = []
        for item in value.split(","):
            bits = item.strip().split(None, 1)
            if bits:
                out.append(" ".join([self.asset(bits[0], base), *bits[1:]]))
        return ", ".join(out)

    def tag(self, raw, tag, attrs, base):
        values = dict(attrs)
        changed, suffix = False, ""
        rel = (values.get("rel") or "").lower().split()
        if tag == "link" and "stylesheet" in rel and values.get("href") and is_local(values["href"]):
            path = resolve(values["href"], base)
            if path in self.contents and path.endswith(".css"):
                self.used.add(path)
                css = self.css(text_of(self.contents[path], path), path)
                media = ' media="' + html_module.escape(values["media"], quote=True) + '"' if values.get("media") else ""
                return "<style" + media + ">" + re.sub(r"</style", r"<\\/style", css, flags=re.I) + "</style>"
            self.missing.add(values["href"][:200])
            return raw
        if tag == "script" and values.get("src") and is_local(values["src"]):
            path = resolve(values["src"], base)
            if path in self.contents and PurePosixPath(path).suffix.lower() in (".js", ".mjs"):
                self.used.add(path)
                if (values.get("type") or "").lower() == "module" and re.search(rb"^\s*(import|export)\b", self.contents[path], re.M):
                    self.warnings.append("Los módulos JavaScript que importan otros archivos no se pueden incrustar: " + path[:120] + ".")
                code = text_of(self.contents[path], path)
                self.spend(len(self.contents[path]))
                attrs = [(k, v) for k, v in attrs if k != "src"]
                suffix = script_text(code)
                changed = self.inlined_script = True
            else:
                self.missing.add(values["src"][:200])
        if tag == "base" and values.get("href") is not None:
            href = values["href"].strip()
            if not is_local(href) or resolve(href.rstrip("/") + "/x", base) != posixpath.normpath(posixpath.join(posixpath.dirname(base), "x")):
                reject("La página usa <base href=\"" + href[:120] + "\">, que cambia cómo se resuelven sus enlaces. Quítalo antes de subir el ZIP.")
        if tag == "meta" and (values.get("http-equiv") or "").lower() == "refresh":
            target = re.search(r"url\s*=\s*['\"]?([^'\";]+)", values.get("content") or "", re.I)
            if target:
                self.navigates(target[1], base)
        for i, (key, value) in enumerate(attrs):
            if value is None:
                continue
            new = value
            if key in ("src", "poster") and tag in ("img", "source", "video", "audio", "input", "track", "embed"):
                new = self.asset(value, base)
            elif key == "srcset" and tag in ("img", "source"):
                new = self.srcset(value, base)
            elif key == "href" and tag == "link" and set(rel) & {"icon", "apple-touch-icon", "shortcut"}:
                new = self.asset(value, base)
            elif (key in ("src", "data", "action", "formaction") and tag in NAVIGATING.get(key, ())) \
                    or (key == "href" and tag == "link" and set(rel) & {"next", "prev", "alternate"}):
                self.navigates(value, base)
            elif key in ("href", "xlink:href") and tag in ("a", "area") and is_local(value) and not self.navigates(value, base):
                path = resolve(value, base)
                if path in self.contents:
                    new = self.data_uri(path)
                elif path:
                    self.missing.add(value.strip()[:200])
            elif key == "href" and tag in ("image", "use") and is_local(value) and not value.startswith("#"):
                new = self.asset(value, base)
            elif key == "style" and "url(" in value.lower():
                new = self.css(value, base)
            if new != value:
                attrs[i] = (key, new)
                changed = True
        if not changed:
            return raw
        rebuilt = "<" + tag + "".join(" " + k if v is None else " " + k + '="' + html_module.escape(v, quote=True) + '"' for k, v in attrs)
        rebuilt += ("/>" if raw.rstrip().endswith("/>") and tag != "script" else ">")
        return rebuilt + suffix

    def render(self):
        content = text_of(self.contents[self.entry], self.entry)
        parser = Tags()
        parser.feed(content)
        parser.close()
        # HTMLParser cuenta líneas sólo por "\n".
        starts = [0] + [m.end() for m in re.finditer("\n", content)]
        offset = lambda pos: starts[pos[0] - 1] + pos[1]
        edits = []
        for index, (pos, raw, tag, attrs) in enumerate(parser.tags):
            if raw is None:
                continue
            self.inlined_script = False
            new = self.tag(raw, tag, list(attrs), self.entry)
            if new != raw:
                start = offset(pos)
                if content[start:start + len(raw)] == raw:
                    edits.append((start, start + len(raw), new))
            if self.inlined_script and index in parser.scripts:
                body_pos, body = parser.scripts[index]
                start = offset(body_pos)
                if content[start:start + len(body)] == body:
                    edits.append((start, start + len(body), ""))
        for pos, data in parser.styles:
            new = self.css(data, self.entry)
            if new != data:
                start = offset(pos)
                if content[start:start + len(data)] == data:
                    edits.append((start, start + len(data), new))
        # Join once. Repeated full-string slicing used quadratic memory/CPU.
        chunks, cursor, total = [], 0, 0
        for start, end, new in sorted(edits):
            if start < cursor:
                reject("No se pudieron resolver los recursos de esta página.")
            before = content[cursor:start]
            total += len(before.encode()) + len(new.encode())
            if total > LIMITS["output_bytes"]:
                reject("El sitio con sus recursos incrustados supera 20 MB.")
            chunks.extend((before, new))
            cursor = end
        total += len(content[cursor:].encode())
        if total > LIMITS["output_bytes"]:
            reject("El sitio con sus recursos incrustados supera 20 MB.")
        chunks.append(content[cursor:])
        return "".join(chunks)


def entry_of(contents, requested):
    pages = sorted(p for p in contents if PurePosixPath(p).suffix.lower() in (".html", ".htm"))
    if not pages:
        reject("El ZIP no contiene ninguna página HTML.")
    if requested is not None:
        if requested not in pages:
            reject("La página de entrada no existe en el ZIP.")
        return requested, pages
    if "index.html" in contents:
        return "index.html", pages
    if len(pages) == 1:
        return pages[0], pages
    return None, pages


def zip_site(name, raw, requested):
    contents, skipped = read_zip(raw)
    entry, pages = entry_of(contents, requested)
    if entry is None:
        reject("El ZIP tiene varias páginas y ningún index.html. Indica cuál es la página de entrada: " + ", ".join(pages[:10]) + ".")
    site = Site(contents, entry)
    content = site.render()
    linked = sorted(site.pages - {entry})
    if linked:
        reject("La página " + entry + " enlaza, incrusta o redirige a otras páginas del ZIP (" + ", ".join(linked[:5])
               + "). Margen publica una página por documento: combina el sitio en una sola página o sube cada página por separado.")
    if len(content.encode()) > LIMITS["output_bytes"]:
        reject("El sitio con sus recursos incrustados supera 20 MB.")
    warnings = list(dict.fromkeys(site.warnings + warnings_for(content)))
    if site.missing:
        warnings.append("Faltan " + str(len(site.missing)) + " recursos locales enlazados: " + ", ".join(sorted(site.missing)[:5]) + ".")
    unlinked = [p for p in pages if p != entry]
    if unlinked:
        warnings.append("Sólo se publica " + entry + "; no se incluyen las otras páginas: " + ", ".join(unlinked[:5]) + ".")
    unused = [p for p in contents if p not in site.used and p != entry and p not in pages]
    if unused:
        warnings.append(str(len(unused)) + " archivos no están enlazados desde " + entry + " y no se incluyen (por ejemplo, datos que el JavaScript pide en tiempo de ejecución).")
    if skipped:
        warnings.append("Se omitieron archivos del sistema (" + str(len(skipped)) + ").")
    files = [{"path": p, "size": len(contents[p]), "type": ASSET_TYPES.get(PurePosixPath(p).suffix.lower(), ""),
              "role": "entry" if p == entry else "page" if p in pages else "asset" if p in site.used else "unused"} for p in sorted(contents)]
    return {"content": content, "entry": entry, "files": files + skipped, "warnings": warnings,
            "title": title_of(content, PurePosixPath(name).stem)}


# --- Contrato ----------------------------------------------------------------

def inspect(name, raw, entry):
    kind = kind_of(name, raw)
    report = {"name": name, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "entry": None,
              "pages": None, "preview": None, "document_id": None, "limits": LIMITS}
    if kind == "pdf":
        report.update(inspect_pdf(name, raw))
        return report
    if kind == "zip":
        site = zip_site(name, raw, entry)
        report.update(kind="zip", title=site["title"], entry=site["entry"], files=site["files"], warnings=site["warnings"])
        found = declared_id(site["content"])
    else:
        content = text_of(raw, "El HTML")
        report.update(kind="html", title=title_of(content, PurePosixPath(name).stem), warnings=warnings_for(content),
                      files=[{"path": name, "size": len(raw), "type": "text/html", "role": "entry"}])
        found = declared_id(content)
    report["document_id"] = found
    return report


def build(name, raw, entry, document_id, title):
    """Devuelve (html, adjuntos, título por defecto). Revalida todo: nunca reutiliza inspect."""
    kind = kind_of(name, raw)
    if kind == "pdf":
        if len(raw) > LIMITS["pdf_bytes"]:
            reject("El PDF debe ocupar menos de 12 MB.")
        fallback = PurePosixPath(name).stem[:200]
        content, attachments = build_pdf(name, raw, document_id, title or fallback)
        return content, attachments, fallback
    if kind == "zip":
        site = zip_site(name, raw, entry)
        content, fallback = site["content"], site["title"]
    else:
        content = text_of(raw, "El HTML")
        fallback = title_of(content, PurePosixPath(name).stem)
    return with_document_id(content, document_id), [], fallback


def mount(app, store, account, payload, clean, artifact_for, publish):
    @app.post("/api/uploads/inspect")
    async def inspect_upload(request: Request):
        account(request)
        if not UPLOAD_SLOTS.acquire(blocking=False):
            raise HTTPException(503, "Hay otros archivos en proceso. Intenta en un momento.")
        try:
            name, raw, entry = decode(await payload(request))
            return await run_in_threadpool(inspect, name, raw, entry)
        finally:
            UPLOAD_SLOTS.release()

    @app.post("/api/uploads")
    async def upload(request: Request):
        u = account(request)
        if not UPLOAD_SLOTS.acquire(blocking=False):
            raise HTTPException(503, "Hay otros archivos en proceso. Intenta en un momento.")
        try:
            body = await payload(request)
            if "visibility" in body:
                reject("Las subidas son privadas. Cambia el acceso desde Compartir.")
            name, raw, entry = decode(body)
            aid = body.get("artifact")
            title = clean(body["title"], 200) if body.get("title") is not None else None
            if aid is not None:
                if not isinstance(aid, str) or not re.fullmatch(r"[a-f0-9]{32}", aid):
                    raise HTTPException(404, "Documento no encontrado.")
                with store.db() as db:
                    artifact = artifact_for(db, aid, u, "edit")
                    document_id = artifact["document_id"]
                    if body.get("expected_current") != artifact["current_version"]:
                        raise HTTPException(409, "Lee la versión actual y envía expected_current antes de subir una revisión.")
            else:
                document_id = "upload-" + uuid.uuid4().hex[:24]
            content, attachments, fallback = await run_in_threadpool(build, name, raw, entry, document_id, title)
            found = DOCUMENT_ID.search(content)
            if aid is not None and found and found[1] != document_id:
                raise HTTPException(409, "El archivo declara otro documento-id (" + found[1] + "). Súbelo como documento nuevo.")
            if "attachments" in body:
                if attachments:
                    reject("El PDF ya conserva su original; no añadas adjuntos.")
                # Originales PDF/PPTX junto al HTML; publish() los valida con formats.attachments.
                attachments = body["attachments"]
            forwarded = {"html": content, "title": title or fallback, "space": body.get("space", "Personal"), "attachments": attachments}
            for key in ("expected_current", "source", "mode"):
                if key in body:
                    forwarded[key] = body[key]
            return await publish(request, aid, forwarded)
        finally:
            UPLOAD_SLOTS.release()
