"""Small hostile PDFs for Poppler: compressed content/image bombs and escaped metadata."""
import sys, zlib


def build(objects, info=None):
    out, offsets = b"%PDF-1.4\n", []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += str(i).encode() + b" 0 obj\n" + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offsets)
    trailer = b"/Size %d/Root 1 0 R" % (len(objects) + 1) + (b"/Info %d 0 R" % info if info else b"")
    return out + b"trailer\n<<" + trailer + b">>\nstartxref\n%d\n%%%%EOF\n" % xref


def stream(data, extra=b""):
    return b"<</Length %d/Filter/FlateDecode%s>>stream\n" % (len(data), extra) + data + b"\nendstream"


def image_pdf(width, height, pages=1):
    """One gray image XObject of width x height zero bytes drawn on every page."""
    image = zlib.compress(b"\0" * (width * height), 9)
    objects = [b"<</Type/Catalog/Pages 2 0 R>>", b"<</Type/Pages/Kids[" + b" ".join(b"%d 0 R" % (4 + 2 * i) for i in range(pages)) + b"]/Count %d>>" % pages,
               stream(image, b"/Type/XObject/Subtype/Image/Width %d/Height %d/ColorSpace/DeviceGray/BitsPerComponent 8" % (width, height))]
    for i in range(pages):
        objects += [b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</XObject<</Im1 3 0 R>>>>/Contents %d 0 R>>" % (5 + 2 * i),
                    stream(zlib.compress(b"q 612 0 0 792 0 0 cm /Im1 Do Q"))]
    return build(objects)


def text_pdf(mib, pages=1, title=None, text=b"Pagina"):
    """Every page shares one content stream that inflates to about `mib` MiB of text operators."""
    def literal(value):
        return b"(" + value.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"
    body = b"(" + b"A" * 54 + b") Tj T* "
    content = zlib.compress(b"BT /F1 12 Tf 72 720 Td 14 TL " + literal(text) + b" Tj T* " + body * (mib * 1024 * 1024 // len(body)) + b"ET", 9)
    objects = [b"<</Type/Catalog/Pages 2 0 R>>", b"<</Type/Pages/Kids[" + b" ".join(b"%d 0 R" % (5 + i) for i in range(pages)) + b"]/Count %d>>" % pages,
               stream(content), b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"]
    objects += [b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 4 0 R>>>>/Contents 3 0 R>>"] * pages
    if title is not None:
        objects.append(b"<</Title " + literal(title) + b">>")
    return build(objects, len(objects) if title is not None else None)


if __name__ == "__main__":
    # python -I pdf_inputs.py <case>  -> runs portal.uploads.build on it and prints time and child CPU/RSS.
    import resource, time
    sys.path.insert(0, "/app")
    from portal import uploads
    raw = {"image": lambda: image_pdf(30000, 30000), "image80": lambda: image_pdf(8000, 8000, 80),
           "text": lambda: text_pdf(400), "text80": lambda: text_pdf(60, 80)}[sys.argv[1]]()
    started = time.time()
    try:
        html, _, _ = uploads.build("x.pdf", raw, None, "upload-x", "t")
        outcome = "ok html=%.1f MiB" % (len(html) / 2**20)
    except Exception as e:
        outcome = "rejected: %s" % getattr(e, "detail", e)
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    print("%s pdf=%.2f MiB wall=%.1fs child_cpu=%.1fs child_maxrss=%.0f MiB %s" % (sys.argv[1], len(raw) / 2**20, time.time() - started,
          child.ru_utime + child.ru_stime, child.ru_maxrss / 1024, outcome))
