"""Discover bundled recipes and moderate immutable community source packages.

Approval lists a contribution; it never installs or executes third-party code.
"""
import base64
import hashlib
import json
import re
import sqlite3
import time
import uuid
import threading
from collections import OrderedDict
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from portal.community_markup import static_component
from portal.community_themes import FONTS, theme_css, apply_theme, visual_component

ROOT = Path(__file__).parent
COLORS = {'papel', 'panel', 'panel-2', 'tinta', 'tinta-2', 'tinta-3', 'naranja', 'verde', 'rojo', 'azul'}
LIMIT = 150_000
PREVIEW_CSP = ("sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
               "font-src data:; script-src 'none'; object-src 'none'; base-uri 'none'; "
               "form-action 'none'; frame-ancestors 'self'")
# Same pinned build the artifact contract embeds; integrity binds the exact bytes.
THREE = ('https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js',
         'sha512-vnmn/Qqn6aG0POAc9mIGzjq0IybrvxJXYDafNvp9JSnDGxeF3pbkSqLvf+YGd5ku63pT7sa/jxHn7/d0mU8+tA==')
NEEDS_THREE = {'scene.js', 'globe.js', 'fleet.js'}


@lru_cache(maxsize=1)
def bundled():
    return {item['id']: item for item in json.loads((ROOT / 'developers-catalog.json').read_text())['items']}


@lru_cache(maxsize=1)
def preview_runtime():
    # This generated map contains only reviewed repository assets, not user data.
    return json.loads((ROOT / 'developers-runtime.json').read_text())


def bundled_preview_scripts(key):
    trusted = bundled().get(key)
    if not trusted or trusted['kind'] != 'component':
        return []
    assets = preview_runtime()
    return [assets[name].replace('</script', '<\\/script') for name in trusted.get('preview_runtime', []) if name in assets]


def bundled_needs_three(key):
    trusted = bundled().get(key) or {}
    return trusted.get('kind') == 'component' and bool(NEEDS_THREE & set(trusted.get('preview_runtime', [])))


def migrate(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS developer_submissions(
      id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),slug TEXT NOT NULL,
      version TEXT NOT NULL,package TEXT NOT NULL,sha TEXT NOT NULL,status TEXT NOT NULL,
      review TEXT NOT NULL DEFAULT '',reviewer TEXT,revision INTEGER NOT NULL DEFAULT 1,
      created INTEGER NOT NULL,updated INTEGER NOT NULL,visibility TEXT NOT NULL DEFAULT 'private',UNIQUE(owner,slug,version));
    CREATE INDEX IF NOT EXISTS developer_submission_status ON developer_submissions(status,created);
    CREATE TABLE IF NOT EXISTS developer_reviews(
      id INTEGER PRIMARY KEY,submission TEXT NOT NULL,actor TEXT NOT NULL,
      status TEXT NOT NULL,note TEXT NOT NULL,at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS developer_favorites(
      owner TEXT NOT NULL REFERENCES users(id),item TEXT NOT NULL,PRIMARY KEY(owner,item));
    ''')


def validate_package(body, clean):
    if len(json.dumps(body, ensure_ascii=False).encode()) > LIMIT:
        raise HTTPException(413, 'El aporte debe ocupar menos de 150 KB.')
    package = body.get('package')
    if not isinstance(package, dict):
        raise HTTPException(422, 'Sube un paquete JSON de Margen.')
    if set(package) - {'schema', 'slug', 'version', 'kind', 'title', 'description', 'license', 'source_url', 'content', 'typography', 'credits', 'design'}:
        raise HTTPException(422, 'El paquete incluye campos desconocidos.')
    if type(package.get('schema')) is not int or package['schema'] != 1:
        raise HTTPException(422, 'Usa el esquema 1.')
    result = {key: clean(package.get(key), maximum) for key, maximum in (
        ('slug', 64), ('version', 32), ('title', 100), ('description', 3000), ('license', 40))}
    if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', result['slug']):
        raise HTTPException(422, 'El identificador usa minúsculas, números y guiones.')
    if not re.fullmatch(r'\d{1,5}\.\d{1,5}\.\d{1,5}', result['version']):
        raise HTTPException(422, 'Usa una versión como 1.0.0.')
    if result['license'] not in {'MIT', 'Apache-2.0', 'BSD-3-Clause', 'CC0-1.0'}:
        raise HTTPException(422, 'Selecciona una licencia admitida.')
    url = clean(package.get('source_url', ''), 600, True)
    try:
        parsed = urlsplit(url)
        valid_url = not url or (parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password)
    except ValueError:
        valid_url = False
    if not valid_url or any(ord(c) < 33 for c in url):
        raise HTTPException(422, 'El enlace de origen debe ser HTTPS y no incluir credenciales.')
    kind = package.get('kind')
    content = package.get('content')
    if kind == 'theme':
        if not isinstance(content, dict) or set(content) != {'light', 'dark'}:
            raise HTTPException(422, 'El tema necesita paletas light y dark.')
        for palette in content.values():
            if not isinstance(palette, dict) or set(palette) != COLORS:
                raise HTTPException(422, 'Incluye los diez colores de la plantilla en cada modo.')
            if any(not isinstance(v, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', v) for v in palette.values()):
                raise HTTPException(422, 'Los colores deben ser valores hexadecimales #RRGGBB.')
    elif kind == 'component':
        content = clean(content, 100_000)
    else:
        raise HTTPException(422, 'El aporte debe ser un tema o un componente HTML/SVG.')
    credits = clean(package.get('credits', ''), 3000, True)
    design = package.get('design')
    if design is not None:
        if kind != 'component' or not isinstance(design, dict) or set(design) != {'kind', 'text'} or design.get('kind') not in {'card', 'steps', 'diagram'}:
            raise HTTPException(422, 'Diseño visual inválido.')
        design = {'kind': design['kind'], 'text': clean(design.get('text'), 6000)}
        content = visual_component(design['kind'], result['title'], design['text'])
    typography = package.get('typography', {'heading': 'instrument', 'body': 'geist'})
    if not isinstance(typography, dict) or set(typography) != {'heading', 'body'} or any(not isinstance(v, str) or v not in FONTS for v in typography.values()):
        raise HTTPException(422, 'Elige las tipografías de la biblioteca.')
    return dict(result, schema=1, kind=kind, content=content, source_url=url, typography=typography, credits=credits, **({'design': design} if design else {}))


def visual_preview_html(item, mode):
    css = (ROOT / 'developers-preview.css').read_text() + (ROOT / 'developers-fonts.css').read_text()
    if item['kind'] == 'theme':
        css += theme_css(item)
        markup = '<section class="prosa"><p class="ceja">Tu tema, tu forma de contar</p><h1>Las ideas necesitan espacio.</h1><p>Así se leerá tu documento. Español e inglés: imaginación, información, thoughtful design.</p><h2>Una decisión bien explicada</h2><p>El contraste, la tipografía y el ritmo acompañan el contenido.</p><blockquote>Una cita para destacar lo importante.</blockquote></section>'
    else:
        markup = static_component(item['content'])
    css += 'body{padding:24px;margin:0}main.hoja{display:block;max-width:700px;margin:auto;padding:0}main.hoja>*{width:100%;max-width:100%}svg{max-width:100%}*{animation:none!important}'
    # Defense in depth; the response also carries the full sandbox CSP.
    policy = PREVIEW_CSP.replace("frame-ancestors 'self'", '').replace('sandbox;', '')
    return '<!doctype html><html lang="es" data-margen-community-theme data-color-mode="' + mode + '"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="' + escape(policy, quote=True) + '"><style>' + css + '</style></head><body><main class="hoja">' + markup + '</main></body></html>'


def mount(app, store, who, account, payload, clean, is_admin, artifact_for, publish):
    previews = OrderedDict()
    preview_lock = threading.Lock()
    with store.db() as db:
        migrate(db)

    def entry(row):
        return {**json.loads(row['package']), 'id': row['id'], 'author': row['author'],
                'origin': 'community', 'status': row['status'], 'sha': row['sha'],
                'revision': row['revision'], 'created': row['created'], 'updated': row['updated'], 'visibility': row['visibility']}

    def find(db, key, user):
        if key in bundled():
            return dict(bundled()[key])
        row = db.execute('SELECT s.*,u.name AS author FROM developer_submissions s JOIN users u ON u.id=s.owner WHERE s.id=?', (key,)).fetchone()
        if not row or (row['status'] != 'approved' and row['visibility'] != 'unlisted' and not (user and (row['owner'] == user['id'] or is_admin(user)))):
            raise HTTPException(404, 'Aporte no disponible.')
        return entry(row)

    def decorate(db, item, user, detail=False):
        result = dict(item)
        if not detail:
            result.pop('content', None)
        result['favorites'] = db.execute('SELECT count(*) FROM developer_favorites WHERE item=?', (item['id'],)).fetchone()[0]
        result['mine'] = bool(user and db.execute('SELECT 1 FROM developer_submissions WHERE id=? AND owner=?', (item['id'], user['id'])).fetchone())
        result['favorite'] = bool(user and db.execute('SELECT 1 FROM developer_favorites WHERE item=? AND owner=?', (item['id'], user['id'])).fetchone())
        return result

    @app.get('/api/developers/catalog')
    def catalog(request: Request):
        user = who(request)
        with store.db() as db:
            items = list(bundled().values())
            rows = db.execute("SELECT s.*,u.name AS author FROM developer_submissions s JOIN users u ON u.id=s.owner WHERE s.status='approved' ORDER BY s.updated DESC LIMIT 201").fetchall()
            items += [entry(row) for row in rows[:200]]
            return {'items': [decorate(db, i, user) for i in items], 'community_truncated': len(rows) > 200,
                    'can_submit': bool(user and user['verified']), 'admin': is_admin(user)}

    @app.get('/api/developers/items/{key}')
    def detail(key: str, request: Request):
        with store.db() as db:
            user = who(request)
            return decorate(db, find(db, key, user), user, True)

    @app.get('/api/developers/items/{key}/download')
    def download(key: str, request: Request):
        with store.db() as db:
            item = find(db, key, who(request))
        package = {k: item[k] for k in ('slug', 'version', 'kind', 'title', 'description', 'license', 'source_url', 'content', 'typography', 'design') if k in item}
        package['schema'] = 1
        if not re.fullmatch(r'\d{1,5}\.\d{1,5}\.\d{1,5}', package['version']):
            package['version'] = '1.0.0'
        package['credits'] = (item.get('credits', '') + '\n' + item['author'] + ' · ' + item.get('source_url', '')).strip()[:3000]
        return Response(json.dumps(package, ensure_ascii=False, indent=2), media_type='application/json',
                        headers={'Content-Disposition': 'attachment; filename="margen-' + item['id'] + '.json"'})

    @app.get('/api/developers/items/{key}/preview')
    def preview(key: str, request: Request):
        with store.db() as db:
            item = find(db, key, who(request))
        mode = 'dark' if request.query_params.get('mode') == 'dark' else 'light'
        scripts = bundled_preview_scripts(key)
        css = (ROOT / 'developers-preview.css').read_text() + (ROOT / 'developers-fonts.css').read_text()
        if item['kind'] == 'theme':
            css += theme_css(item)
            markup = '<section class="prosa"><p class="ceja">Una idea para compartir</p><h2>El espacio también cuenta.</h2><p>Un tema acompaña el contenido: texto legible, una paleta propia y lugar para pensar.</p><blockquote>Prueba sus colores en claro y oscuro.</blockquote></section>'
        else:
            # Bundled recipes are repository source; only community markup is rebuilt statically.
            markup = bundled()[key]['content'] if key in bundled() else static_component(item['content'])
        css += 'html,body{margin:0;min-height:0}body{padding:24px;overflow-wrap:anywhere}body>main{display:block;max-width:100%;margin:0;padding:0}*{animation:none!important;transition:none!important}img,svg,canvas{max-width:100%}a,button,input,select,textarea{pointer-events:none}'
        html = '<!doctype html><html lang="es" data-margen-community-theme data-color-mode="' + mode + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>' + css + '</style></head><body><main class="hoja">' + markup + '</main></body></html>'
        policy = PREVIEW_CSP
        if scripts:
            # Runtime controls stay usable; recipe links would only navigate the preview frame.
            html = html.replace('a,button,input,select,textarea{pointer-events:none}', 'a[href]{pointer-events:none}')
            hashes = ' '.join("'sha256-" + base64.b64encode(hashlib.sha256(source.encode()).digest()).decode() + "'" for source in scripts)
            three = bundled_needs_three(key)
            policy = policy.replace('sandbox;', 'sandbox allow-scripts;').replace("script-src 'none'", 'script-src ' + hashes + (' ' + THREE[0] if three else ''))
            library = '<script src="' + THREE[0] + '" integrity="' + THREE[1] + '" crossorigin="anonymous"></script>' if three else ''
            html = html.replace('</body>', library + ''.join('<script>' + source + '</script>' for source in scripts) + '</body>')
        return HTMLResponse(html, headers={'Content-Security-Policy': policy})

    @app.put('/api/developers/items/{key}/favorite')
    async def favorite(key: str, request: Request):
        user = account(request)
        body = await payload(request)
        if type(body.get('favorite')) is not bool:
            raise HTTPException(422, 'Indica si quieres guardar el aporte.')
        with store.db() as db:
            item = find(db, key, user)
            if item['status'] not in {'bundled', 'approved'}:
                raise HTTPException(409, 'El aporte todavía no está en el catálogo.')
            if body['favorite']:
                db.execute('INSERT OR IGNORE INTO developer_favorites VALUES(?,?)', (user['id'], key))
            else:
                db.execute('DELETE FROM developer_favorites WHERE owner=? AND item=?', (user['id'], key))
            return decorate(db, item, user)

    @app.get('/api/developers/submissions')
    def submissions(request: Request):
        user = account(request)
        all_submissions = request.query_params.get('scope') == 'review'
        if all_submissions and not is_admin(user):
            raise HTTPException(403, 'Sólo administración puede revisar aportes de otros autores.')
        with store.db() as db:
            rows = db.execute('SELECT s.*,u.name AS author FROM developer_submissions s JOIN users u ON u.id=s.owner ' +
                              ('' if all_submissions else 'WHERE s.owner=? ') + 'ORDER BY s.created DESC LIMIT 201',
                              () if all_submissions else (user['id'],)).fetchall()
            return {'items': [{**{k: v for k, v in entry(row).items() if k != 'content'}, 'review': row['review']} for row in rows[:200]],
                    'truncated': len(rows) > 200}

    @app.post('/api/developers/submissions')
    async def submit(request: Request):
        user = account(request)
        body = await payload(request)
        publication = body.get('publication', 'review')
        if publication not in {'private', 'shared', 'review'}:
            raise HTTPException(422, 'Elige guardar, compartir por enlace o enviar al catálogo.')
        if publication != 'private' and (body.get('rights_accepted') is not True or body.get('public_listing_accepted') is not True):
            raise HTTPException(422, 'Confirma los derechos y la publicación de tu nombre y aporte.')
        package = validate_package(body, clean)
        serialized = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        state = 'pending' if publication == 'review' else 'draft'
        visibility = 'unlisted' if publication == 'shared' else 'private'
        key = uuid.uuid4().hex
        now = int(time.time())
        with store.db() as db:
            if db.execute("SELECT count(*) FROM developer_submissions WHERE owner=? AND status IN ('pending','draft')", (user['id'],)).fetchone()[0] >= 10:
                raise HTTPException(429, 'Tienes diez borradores o aportes pendientes. Retira uno antes de crear otro.')
            try:
                db.execute('INSERT INTO developer_submissions(id,owner,slug,version,package,sha,status,created,updated,visibility) VALUES(?,?,?,?,?,?,?,?,?,?)',
                           (key, user['id'], package['slug'], package['version'], serialized, hashlib.sha256(serialized.encode()).hexdigest(), state, now, now, visibility))
            except sqlite3.IntegrityError:
                raise HTTPException(409, 'Ya enviaste esa versión. Usa una nueva versión para los cambios.') from None
        return {'id': key, 'status': state, 'url': '/?view=developers&item=' + key}

    @app.put('/api/developers/submissions/{key}/review')
    async def review(key: str, request: Request):
        user = account(request)
        if not is_admin(user):
            raise HTTPException(403, 'Sólo administración puede publicar o devolver aportes.')
        body = await payload(request)
        status = body.get('status')
        note = clean(body.get('note', ''), 2000, status == 'approved')
        if status not in {'approved', 'changes_requested', 'withdrawn'} or type(body.get('revision')) is not int:
            raise HTTPException(422, 'Revisión inválida.')
        with store.db() as db:
            row = db.execute('SELECT * FROM developer_submissions WHERE id=?', (key,)).fetchone()
            if not row:
                raise HTTPException(404, 'Aporte no disponible.')
            if row['revision'] != body['revision']:
                raise HTTPException(409, 'Otra persona revisó este aporte. Recarga antes de decidir.')
            if status in {'approved', 'changes_requested'} and row['status'] != 'pending':
                raise HTTPException(409, 'Sólo se revisan aportes enviados al catálogo por su autor.')
            if row['status'] == status:
                raise HTTPException(409, 'El aporte ya tiene ese estado.')
            now = int(time.time())
            db.execute('UPDATE developer_submissions SET status=?,review=?,reviewer=?,revision=revision+1,updated=?,visibility=? WHERE id=?',
                       (status, note, user['id'], now, 'public' if status == 'approved' else 'private', key))
            db.execute('INSERT INTO developer_reviews(submission,actor,status,note,at) VALUES(?,?,?,?,?)', (key, user['id'], status, note, now))
        return {'id': key, 'status': status, 'revision': row['revision'] + 1}

    @app.put('/api/developers/submissions/{key}/publication')
    async def publication(key: str, request: Request):
        user = account(request)
        body = await payload(request)
        action = body.get('publication')
        if action not in {'shared', 'private', 'review'} or type(body.get('revision')) is not int:
            raise HTTPException(422, 'Publicación inválida.')
        if action != 'private' and (body.get('rights_accepted') is not True or body.get('public_listing_accepted') is not True):
            raise HTTPException(422, 'Confirma que puedes compartir públicamente este aporte.')
        with store.db() as db:
            row = db.execute('SELECT * FROM developer_submissions WHERE id=? AND owner=?', (key, user['id'])).fetchone()
            if not row:
                raise HTTPException(404, 'Aporte no disponible.')
            if row['revision'] != body['revision']:
                raise HTTPException(409, 'El aporte cambió. Recarga antes de compartir.')
            status = 'pending' if action == 'review' else ('withdrawn' if action == 'private' else 'draft')
            visibility = 'unlisted' if action == 'shared' else 'private'
            db.execute('UPDATE developer_submissions SET status=?,visibility=?,revision=revision+1,updated=? WHERE id=?', (status, visibility, int(time.time()), key))
        return {'id': key, 'status': status, 'visibility': visibility, 'url': '/?view=developers&item=' + key}

    @app.post('/api/developers/visual-component')
    async def component(request: Request):
        account(request)
        body = await payload(request)
        kind = body.get('kind')
        if kind not in {'card', 'steps', 'diagram'}:
            raise HTTPException(422, 'Elige tarjeta, pasos o diagrama.')
        return {'content': visual_component(kind, clean(body.get('title'), 100), clean(body.get('text'), 6000))}

    @app.post('/api/developers/preview')
    async def preview_package(request: Request):
        user = account(request)
        item = validate_package(await payload(request), clean)
        mode = 'dark' if request.query_params.get('mode') == 'dark' else 'light'
        token = uuid.uuid4().hex
        now = time.monotonic()
        with preview_lock:
            for old in [key for key, value in previews.items() if now - value[0] > 300]:
                previews.pop(old, None)
            owned = [key for key, value in previews.items() if value[1] == user['id']]
            for old in owned[:-3]:
                previews.pop(old, None)
            while len(previews) >= 128:
                previews.popitem(last=False)
            previews[token] = (now, user['id'], item, mode)
        return {'url': '/api/developers/previews/' + token}

    @app.get('/api/developers/previews/{token}')
    def live_preview(token: str, request: Request):
        user = account(request)
        with preview_lock:
            saved = previews.get(token)
        if not saved or saved[1] != user['id'] or time.monotonic() - saved[0] > 300:
            raise HTTPException(404, 'La vista previa caducó. Cambia un campo para actualizarla.')
        return HTMLResponse(visual_preview_html(saved[2], saved[3]), headers={'Content-Security-Policy': PREVIEW_CSP})


    @app.get('/api/developers/targets')
    def targets(request: Request):
        user = account(request)
        with store.db() as db:
            rows = db.execute('SELECT id,title,current_version FROM artifacts WHERE owner=? ORDER BY updated DESC LIMIT 201', (user['id'],)).fetchall()
            return {'items': [dict(row) for row in rows[:200]], 'truncated': len(rows) > 200}

    @app.post('/api/developers/items/{key}/use')
    async def use(key: str, request: Request):
        user = account(request)
        body = await payload(request)
        with store.db() as db:
            item = find(db, key, user)
            if item['kind'] == 'theme' and body.get('artifact'):
                aid = clean(body.get('artifact'), 120)
                a = artifact_for(db, aid, user, 'edit')
                if a['owner'] != user['id']:
                    raise HTTPException(403, 'Sólo puedes aplicar temas a tus propios artefactos.')
                if body.get('expected_current') != a['current_version']:
                    raise HTTPException(409, 'El documento cambió. Recarga antes de aplicar el tema.')
                version = db.execute('SELECT sha FROM versions WHERE id=?', (a['current_version'],)).fetchone()
                content = apply_theme((store.files / (version['sha'] + '.html')).read_text(), item)
                data = {'html': content, 'title': a['title'], 'space': a['space'], 'mode': 'draft', 'expected_current': a['current_version']}
            else:
                aid = None
                title = clean(body.get('title', item['title']), 200)
                content = (ROOT / 'developers-shell.html').read_text()
                content = content.replace('margen-community-starter', 'community-' + uuid.uuid4().hex)
                markup = (static_component(item['content']) if item['kind'] == 'component' else '<section class="prosa"><h2>Tu próximo documento</h2><p>Edita este contenido para empezar.</p></section>')
                content = content.replace('<p id="community-slot">Contenido inicial.</p>', markup)
                if item['kind'] == 'theme':
                    content = apply_theme(content, item)
                data = {'html': content, 'title': title, 'space': 'Personal', 'visibility': 'private'}
        return await publish(request, aid, body=data)
