#!/usr/bin/env python3
"""Create an annotation-ready preview, preserving the original PDF or PPTX."""
import argparse
import base64
import html
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def convert(source, output, document_id, title):
    source = Path(source).resolve()
    output = Path(output)
    kind = source.suffix.lower().lstrip(".")
    if kind not in ("pdf", "pptx"):
        raise ValueError("Use PDF or PPTX")
    if source.stat().st_size > 12 * 1024 * 1024:
        raise ValueError("Original exceeds 12 MB")
    if not re.fullmatch("[a-zA-Z0-9_-]{1,120}", document_id):
        raise ValueError("Choose a stable document ID")
    pages = []
    visual = False
    with tempfile.TemporaryDirectory(prefix="margen-import-") as folder:
        root = Path(folder)
        pdf = source
        if kind == "pptx" and shutil.which("libreoffice"):
            subprocess.run(
                [
                    "libreoffice",
                    "-env:UserInstallation=file://" + str(root / "profile"),
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(root),
                    str(source),
                ],
                check=True,
                timeout=180,
                stdout=subprocess.DEVNULL,
            )
            pdf = root / (source.stem + ".pdf")
        if (
            pdf.suffix.lower() == ".pdf"
            and shutil.which("pdftoppm")
            and shutil.which("pdfinfo")
        ):
            info = subprocess.check_output(["pdfinfo", str(pdf)], text=True, timeout=30)
            match = re.search(r"^Pages:\s+(\d+)", info, re.M)
            if not match or int(match[1]) > 80:
                raise ValueError("Preview supports up to 80 pages")
            subprocess.run(
                [
                    "pdftoppm",
                    "-jpeg",
                    "-scale-to",
                    "1400",
                    "-jpegopt",
                    "quality=75",
                    str(pdf),
                    str(root / "page"),
                ],
                check=True,
                timeout=180,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            paths = sorted(
                root.glob("page-*.jpg"), key=lambda p: int(p.stem.split("-")[-1])
            )
            for i, path in enumerate(paths):
                text = ""
                if shutil.which("pdftotext"):
                    text = subprocess.check_output(
                        [
                            "pdftotext",
                            "-f",
                            str(i + 1),
                            "-l",
                            str(i + 1),
                            str(pdf),
                            "-",
                        ],
                        text=True,
                        timeout=30,
                    )
                pages.append(
                    '<figure id="page-'
                    + str(i + 1)
                    + '"><img alt="Página '
                    + str(i + 1)
                    + '" src="data:image/jpeg;base64,'
                    + base64.b64encode(path.read_bytes()).decode()
                    + '"><figcaption>Página '
                    + str(i + 1)
                    + "</figcaption></figure><details><summary>Texto de la página</summary><p>"
                    + html.escape(text)
                    + "</p></details>"
                )
            visual = True
        elif kind == "pptx":
            with zipfile.ZipFile(source) as z:
                slides = sorted(
                    [
                        n
                        for n in z.namelist()
                        if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)
                    ],
                    key=lambda n: int(re.search(r"\d+", n)[0]),
                )
                if (
                    len(slides) > 80
                    or sum(z.getinfo(n).file_size for n in slides) > 10 * 1024 * 1024
                ):
                    raise ValueError("Presentation preview limit exceeded")
                for i, name in enumerate(slides):
                    xml = z.read(name)
                    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
                        raise ValueError("Unsafe XML")
                    text = "\n".join(
                        e.text or ""
                        for e in ET.fromstring(xml).iter()
                        if e.tag.endswith("}t")
                    )
                    pages.append(
                        '<section id="slide-'
                        + str(i + 1)
                        + '"><h2>Diapositiva '
                        + str(i + 1)
                        + "</h2><p>"
                        + html.escape(text)
                        + "</p></section>"
                    )
        else:
            raise ValueError(
                "Install Poppler (pdfinfo, pdftoppm) for PDF page previews"
            )
    if not pages:
        raise ValueError("No pages found")
    attachment = "original." + kind
    content = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="nota-documento" content="'
        + document_id
        + '"><meta name="margen-format" content="'
        + kind
        + '"><title>'
        + html.escape(title)
        + "</title><style>body{margin:0;background:#e9e6e0;color:#282623;font:16px/1.6 system-ui;padding:24px 20px 110px}main{max-width:1080px;margin:auto}header{margin:0 0 24px}img{display:block;width:100%;height:auto}figure,section{margin:0 0 24px;background:white;padding:12px;border:1px solid #d7d1c8}p{white-space:pre-wrap}figcaption,summary{font-size:12px;color:#625c53}details{margin-bottom:24px}a{color:inherit}</style></head><body><main><header><h1>"
        + html.escape(title)
        + "</h1><p>"
        + (
            "Vista por páginas. El original conserva su formato."
            if visual
            else "Vista textual de las diapositivas; no reproduce el diseño. Instala LibreOffice y Poppler para generar vistas visuales."
        )
        + '</p><a href="'
        + attachment
        + '" data-margen-original="'
        + attachment
        + '">Descargar original</a></header>'
        + "".join(pages)
        + "</main></body></html>"
    )
    if len(content.encode()) > 18 * 1024 * 1024:
        raise ValueError("Preview exceeds size limit; reduce page count or resolution")
    output.write_text(content)
    output.with_suffix(".attachments.json").touch(mode=0o600)
    output.with_suffix(".attachments.json").chmod(0o600)
    output.with_suffix(".attachments.json").write_text(
        json.dumps(
            [
                {
                    "name": attachment,
                    "data": base64.b64encode(source.read_bytes()).decode(),
                }
            ]
        )
    )
    return {
        "file": str(output),
        "pages": len(pages),
        "visual": visual,
        "original": str(output.with_suffix(".attachments.json")),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--document-id", required=True)
    p.add_argument("--title", required=True)
    a = p.parse_args()
    print(json.dumps(convert(a.source, a.output, a.document_id, a.title)))
