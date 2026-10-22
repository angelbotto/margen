"""Portal real (uvicorn HTTPS local, datos temporales) para revisar Guardar / Me gusta en Chromium y WebKit.

Nunca usa producción ni credenciales: cuentas y sesiones se crean en un SQLite temporal.
"""
import sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from fastapi.testclient import TestClient
from check_media_embeds import certificate, serve_portal
from contract_artifact import build

COOKIE = '__Host-bottifact'


def sections(n=4, extra='', prefix='s'):
    return ''.join(f'<section class="prosa" id="{prefix}{i}"><h2>Sección {i}</h2>' + '<p>Texto de lectura largo para desplazar.</p>' * 14 + '</section>' for i in range(1, n + 1)) + extra


GALLERY = ('<section class="pieza amplio galeria-fotografica" id="galeria" data-galeria><div class="galeria-pista" tabindex="0" role="region" aria-label="Galería">'
           + ''.join('<figure><img alt="" src="data:image/gif;base64,R0lGODlhAQABAAAAACw="><figcaption>Figura</figcaption></figure>' for _ in range(5)) + '</div></section>')


class Portal:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        cert, key = certificate(tmp)
        self.app, self.origin, self.server = serve_portal(tmp, cert, key)
        self.store = self.app.state.store
        self.clients, self.sessions = {}, {}
        for email in ('author@example.com', 'reader@example.com', 'second@example.com', 'outsider@example.com'):
            u = self.store.user(email, email.split('@')[0])
            token = self.store.session(u['id'])
            c = TestClient(self.app, base_url=self.origin, headers={'Origin': self.origin})
            c.cookies.set(COOKIE, token)
            self.clients[email.split('@')[0]] = c
            self.sessions[email.split('@')[0]] = token

    def publish(self, title, html, visibility='invited', grants=('reader@example.com', 'second@example.com')):
        a = self.clients['author']
        r = a.post('/api/artifacts', json={'title': title, 'html': html})
        assert r.status_code == 200, r.text
        aid = r.json()['id']
        self.share(aid, visibility, grants)
        return aid

    def share(self, aid, visibility='invited', grants=('reader@example.com', 'second@example.com')):
        r = self.clients['author'].put('/api/artifacts/' + aid + '/access', json={'visibility': visibility, 'grants': [{'email': e, 'role': 'viewer'} for e in grants]})
        assert r.status_code == 200, r.text

    def state(self, who, aid):
        return self.clients[who].get('/api/artifacts/' + aid + '/reader-actions')

    def act(self, who, aid, body):
        return self.clients[who].put('/api/artifacts/' + aid + '/reader-actions', json=body, headers={'X-Margen-Reader-Action': '1'})

    def context(self, browser, who, **kw):
        ctx = browser.new_context(ignore_https_errors=True, locale='es-ES', **{'viewport': {'width': 1280, 'height': 900}, **kw})
        if who:
            ctx.add_cookies([{'name': COOKIE, 'value': self.sessions[who], 'url': self.origin + '/', 'secure': True, 'httpOnly': True, 'sameSite': 'Lax'}])
        return ctx

    def close(self):
        self.server.should_exit = True
        self.tmp.cleanup()


def contract_doc(title, extra='', **kw):
    return build(title, [{'id': 'informe', 'titulo': title, 'html': sections(extra=extra)}], **kw)


def chapters_doc(title):
    pages = [{'id': p, 'titulo': p.title(), 'html': sections(3, prefix=p + '-')} for p in ('uno', 'dos', 'tres')]
    return build(title, pages)


def deck(title):
    return build(title, [{'id': 'uno', 'titulo': 'Uno', 'html': '<p>Primera.</p>'}, {'id': 'dos', 'titulo': 'Dos', 'html': '<p>Segunda.</p>'}], format='presentation')


RAW = '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="nota-documento" content="html-propio"><title>Raw</title></head><body><h1>HTML propio</h1>' + '<p>Texto.</p>' * 40 + '</body></html>'
