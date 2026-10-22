#!/usr/bin/env python3
"""Build a small chapters document through the shared contract with edge-case code blocks."""
import sys
from html import escape
from pathlib import Path
import os
ROOT = Path(os.environ.get('MARGEN_ROOT') or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT / 'scripts'))
from contract_artifact import build

def block(i, code, lang='javascript', attrs='data-lineas', raw=False):
    body = code if raw else escape(code)
    return (f'<div class="codigo"><div class="cab"><span>{lang}</span></div><pre tabindex="0" aria-label="Código {i}">'
            f'<code id="c{i}" data-lenguaje="{lang}" {attrs}>{body}</code></pre></div>')

cases = [
 block(1, 'const a = 1;\nconst b = 2;\n'),                                   # trailing newline
 block(2, 'if (x) {\n\treturn "tab\\there";\n}\n// ñandú 🧪 é́ 漢字 →'),  # tabs + unicode
 block(3, 'const <mark>uno = 1;\nconst dos</mark> = 2;', raw=True),          # mark across lines
 block(4, 'const <a href="#s1"><mark>enlace</mark></a> = 3;', raw=True),        # nested overlay
 block(5, 'texto plano', lang='cobol'),                                      # unknown language
 block(6, 'línea\r\nwindows', lang='text'),
 block(7, '<mark>// ver <a href="#s1">enlace</a></mark>\nx = 1;', raw=True),   # link inside mark
]
hidden = [block(20, 'def oculto():\n    return 1', lang='python')]
details = ('<details id="det"><summary>Ver</summary>' + block(30, 'SELECT 1 -- dentro de details', lang='sql') + '</details>')
pages = [{"id": "uno", "titulo": "Uno", "html": '<section class="seccion" id="s1"><h2>Código</h2><p>Casos.</p></section>' + ''.join(cases) + details},
         {"id": "dos", "titulo": "Dos", "html": '<section class="seccion" id="s2"><h2>Oculto</h2></section>' + ''.join(hidden)}]
html = build('Fixture código', pages, description='fixture', document_id='review-code-fixture', format='chapters', theme='editorial', mode='dark', date='2026-10-22')
Path(sys.argv[1]).write_text(html)
