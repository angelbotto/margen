"""Portal del NAS: autorización en cada lectura/escritura y HTML aislado.

SQLite reside en disco local del NAS, nunca en un montaje SMB/NFS. Un proceso
de aplicación; transacciones y bloqueo cubren cambios de permisos y comentarios.
"""
import hashlib
import json
import os
import re
import secrets
import sqlite3
import threading
import time
import uuid
from urllib.parse import urlsplit
from contextlib import contextmanager
from pathlib import Path
from functools import lru_cache

import jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, FileResponse
from portal.workflows import migrate, metadata, version_state, visible_events, provenance, enqueue
from portal.workspace import mount_workspace
from portal.knowledge import enrich, connections, knowledge_network
from portal.context_graph import network as context_network, mount as mount_context, cited_version_readable
from portal.auth import mount_auth
from portal.preview import preview_html
from portal.search import index_document, match_query, normalized, window
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

ROOT = Path(__file__).parent
COOKIE = '__Host-bottifact'
MAX_BODY = 22 * 1024 * 1024
EMAIL = re.compile(r'^[^\s@]{1,64}@[^\s@.]+(?:\.[^\s@.]+)+$')
ID = re.compile(r'^[a-zA-Z0-9_-]{1,120}$')


def admin_emails():
    return [e.strip().lower() for e in os.environ.get("BOTTIFACT_ADMIN_EMAILS", "").split(",") if e.strip()]


def owner_aliases():
    """Alias de la misma persona, separados de la lista de administradores."""
    return [e.strip().lower() for e in os.environ.get('BOTTIFACT_OWNER_ALIASES','').split(',') if e.strip()]


def is_admin(user):
    return bool(user and user["verified"] and user.get("email") in admin_emails())


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def clean(value, maximum=200, empty=False):
    if not isinstance(value, str) or len(value) > maximum or (not empty and not value.strip()):
        raise HTTPException(422, 'Texto ausente o demasiado largo.')
    return value.strip()


async def payload(request):
    try:
        value = await request.json()
    except (ValueError, UnicodeError):
        raise HTTPException(422, 'JSON inválido.') from None
    if not isinstance(value, dict):
        raise HTTPException(422, 'Se esperaba un objeto JSON.')
    return value


from portal.domain_access import verified_domain, access_revision, parse_grants as parse_domain_grants


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.files = self.root / 'files'
        self.files.mkdir(exist_ok=True, mode=0o700)
        self.lock = threading.RLock()
        with self.db() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE,name TEXT NOT NULL,verified INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),expires INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS tokens(hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),label TEXT NOT NULL,created INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS logins(hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),expires INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,
              space TEXT NOT NULL,document_id TEXT NOT NULL,visibility TEXT NOT NULL DEFAULT 'private',
              comments TEXT NOT NULL DEFAULT 'reviewers',guests INTEGER NOT NULL DEFAULT 0,current_version TEXT,updated INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS versions(id TEXT PRIMARY KEY,artifact TEXT NOT NULL REFERENCES artifacts(id),sha TEXT NOT NULL,created INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS grants(artifact TEXT NOT NULL REFERENCES artifacts(id),email TEXT NOT NULL,role TEXT NOT NULL,PRIMARY KEY(artifact,email));
            CREATE TABLE IF NOT EXISTS domain_grants(artifact TEXT NOT NULL REFERENCES artifacts(id),domain TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('viewer','commenter')),PRIMARY KEY(artifact,domain));
            CREATE INDEX IF NOT EXISTS domain_grants_domain_artifact ON domain_grants(domain,artifact);
            CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,artifact TEXT NOT NULL REFERENCES artifacts(id),version TEXT NOT NULL REFERENCES versions(id),
              actor TEXT NOT NULL REFERENCES users(id),request_hash TEXT NOT NULL,event TEXT NOT NULL,time INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS events_artifact ON events(artifact,time);
            CREATE TABLE IF NOT EXISTS bookmarks(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,url TEXT NOT NULL,space TEXT NOT NULL,created INTEGER NOT NULL,UNIQUE(owner,url));
            CREATE TABLE IF NOT EXISTS bookmark_migrations(bookmark TEXT PRIMARY KEY,artifact TEXT NOT NULL REFERENCES artifacts(id));
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT NOT NULL,action TEXT NOT NULL,artifact TEXT,at INTEGER NOT NULL);
            CREATE VIRTUAL TABLE IF NOT EXISTS artifact_fts USING fts5(artifact UNINDEXED,version UNINDEXED,title,space,body,tokenize='unicode61 remove_diacritics 2');
            ''')
            migrate(db)
            from portal.library_query import migrate as migrate_library
            migrate_library(db)

    def refresh_search(self):
        with self.db() as db:
            revision=db.execute("SELECT value FROM operation_status WHERE key='search_revision'").fetchone()
            if not revision or revision['value']!='2':
                db.execute('DELETE FROM artifact_fts')
                db.execute("INSERT OR REPLACE INTO operation_status VALUES('search_revision','2')")
            pending=db.execute('SELECT a.*,v.sha FROM artifacts a JOIN versions v ON v.id=a.current_version LEFT JOIN artifact_fts f ON f.artifact=a.id WHERE f.artifact IS NULL OR f.version<>a.current_version OR f.title<>a.title OR f.space<>a.space').fetchall()
            for artifact in pending:
                index_document(db,artifact,(self.files/(artifact['sha']+'.html')).read_text())

    def merge_admin_aliases(self):
        """Conserva sesiones, conexiones y autoría al unir alias verificados."""
        aliases = owner_aliases()
        if not aliases: return
        with self.db() as db:
            known = [r for r in db.execute('SELECT * FROM users WHERE verified=1') if r['email'] in aliases]
            if not known: return
            canonical = db.execute('SELECT * FROM users WHERE email=? AND verified=1', (aliases[0],)).fetchone()
            if not canonical:
                uid = uuid.uuid4().hex
                db.execute('INSERT INTO users VALUES(?,?,?,1)', (uid, aliases[0], known[0]['name']))
            else: uid = canonical['id']
            for old in known:
                if old['id'] == uid: continue
                changed_before = db.total_changes
                for table, column in [('sessions','user_id'), ('tokens','user_id'), ('logins','user_id'), ('artifacts','owner'), ('events','actor'), ('audit','actor'), ('creator_jobs','owner'), ('creator_decisions','owner'), ('creator_rules','owner'), ('creator_connectors','owner'), ('creator_decision_history','actor'), ('review_threads','actor')]:
                    db.execute(f'UPDATE {table} SET {column}=? WHERE {column}=?', (uid, old['id']))
                for table in ['review_reads','thread_reads','notifications','notification_settings']:
                    # Las claves únicas del usuario canónico prevalecen; el historial original queda auditable.
                    db.execute(f'UPDATE OR IGNORE {table} SET user=? WHERE user=?',(uid,old['id']))
                db.execute('UPDATE delivery_batches SET user=? WHERE user=?',(uid,old['id']))
                # Los duplicados se conservan con su dueño histórico; la administración los ve.
                db.execute('UPDATE bookmarks SET owner=? WHERE owner=? AND url NOT IN (SELECT url FROM bookmarks WHERE owner=?)', (uid,old['id'],uid))
                if db.total_changes > changed_before:
                    db.execute('INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)', (uid,'merge-alias',old['id'],int(time.time())))

    @contextmanager
    def db(self):
        with self.lock:
            db = sqlite3.connect(self.root / 'bottifact.sqlite3', timeout=30)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA foreign_keys=ON')
            from portal.search import normalized
            db.create_function('norm',1,lambda v:normalized(str(v or '')),deterministic=True)
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                db.close()

    def user(self, email, name):
        email = clean(email, 254).lower()
        aliases = owner_aliases()
        if email in aliases: email = aliases[0]
        if not EMAIL.fullmatch(email):
            raise HTTPException(422, 'Correo inválido.')
        with self.db() as db:
            found = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
            if found:
                return dict(found)
            uid = uuid.uuid4().hex
            db.execute('INSERT INTO users VALUES(?,?,?,1)', (uid, email, clean(name, 80)))
            return dict(db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone())

    def session(self, user_id):
        token = secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE expires<?', (int(time.time()),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)', (digest(token), user_id, int(time.time()) + 86400 * 14))
        return token

    def token(self, user_id, label='Agente'):
        token = 'bf_' + secrets.token_urlsafe(40)
        with self.db() as db:
            if db.execute('SELECT count(*) FROM tokens WHERE user_id=?',(user_id,)).fetchone()[0]>=50: raise HTTPException(409,'Máximo 50 conexiones por cuenta.')
            db.execute('INSERT INTO tokens VALUES(?,?,?,?)', (digest(token), user_id, label, int(time.time())))
        return token

    def login_once(self, user_id):
        token = secrets.token_urlsafe(40)
        with self.db() as db:
            db.execute('DELETE FROM logins WHERE expires<?', (int(time.time()),))
            db.execute('INSERT INTO logins VALUES(?,?,?)', (digest(token), user_id, int(time.time()) + 300))
        return token


def role(db, artifact, user):
    if not user:
        return None
    if artifact['owner'] == user['id'] or is_admin(user):
        return 'owner'
    grant = db.execute('SELECT role FROM grants WHERE artifact=? AND email=?',
                       (artifact['id'], user.get('email') or '')).fetchone() if user['verified'] else None
    if grant:
        return grant['role']
    domain = verified_domain(user)
    grant = db.execute('SELECT role FROM domain_grants WHERE artifact=? AND domain=?', (artifact['id'], domain)).fetchone() if domain else None
    return grant['role'] if grant else None


def permissions(db, artifact, user):
    r = role(db, artifact, user)
    read = bool(r) or artifact['visibility'] in ('public', 'unlisted')
    if version_state(db,artifact['current_version'])=='draft' and r not in ('owner','editor'):read=False
    review = read and (bool(r) or artifact['comments'] == 'readers')
    comment = review and bool(user) and (r in ('owner', 'editor', 'commenter') or
              (r is None and artifact['comments'] == 'readers' and (user['verified'] or artifact['guests'])))
    return {'read': read, 'review': review, 'comment': bool(comment), 'edit': r in ('owner', 'editor'), 'manage': r == 'owner', 'role': r}


def artifact_for(db, aid, user, capability='read'):
    a = db.execute('SELECT * FROM artifacts WHERE id=?', (aid,)).fetchone()
    if not a or not permissions(db, a, user)[capability]:
        raise HTTPException(404, 'Artefacto no disponible para esta cuenta.')
    return dict(a)


def snapshot(db, a, user=None):
    p=permissions(db,a,user)
    return {'format':'nota-revision','version':2,'document':a['document_id'],
            'events':visible_events(db,a,user,p['review'],p['edit'])}


def threads(events):
    result = {}
    for e in events:
        if e['kind'] == 'create':
            result[e['thread']] = {**e, 'replies': [], 'resolved': False, 'deleted': False, 'assignee': ''}
        t = result.get(e['thread'])
        if not t:
            continue
        t['updated']=e['time']
        if e['kind'] == 'reply': t['replies'].append(e)
        if e['kind'] == 'edit': t['text'] = e['text']
        if e['kind'] == 'resolve': t['resolved'] = e['resolved']
        if e['kind'] == 'assign': t['assignee'] = e['assignee']
        if e['kind'] == 'delete': t['deleted'] = True
    return [t for t in result.values() if not t['deleted']]


def create_app(data=None, origin=None, issuer=None, audience=None):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    store = Store(data or os.environ.get('BOTTIFACT_DATA', '/tmp/bottifact-portal'))
    store.merge_admin_aliases()
    store.refresh_search()
    app.state.store = store
    origin = (origin or os.environ.get('BOTTIFACT_ORIGIN', 'http://localhost:8788')).rstrip('/')
    from .settings import validate_origin
    origin=validate_origin(origin)
    origins = {origin, *filter(None, os.environ.get('BOTTIFACT_EXTRA_ORIGINS', '').split(','))}
    issuer = (issuer or os.environ.get('BOTTIFACT_ISSUER', '')).rstrip('/')
    audience = audience or os.environ.get('BOTTIFACT_AUDIENCE', '')
    jwks = jwt.PyJWKClient(issuer + '/cdn-cgi/access/certs', cache_keys=True, lifespan=300) if issuer and audience else None
    from collections import deque
    from portal.telemetry import Metrics
    metrics=Metrics(store.root)
    rate = {}
    rate_lock = threading.Lock()

    def who(request):
        auth = request.headers.get('authorization', '')
        with store.db() as db:
            if auth.startswith('Bearer '):
                row = db.execute('SELECT u.* FROM tokens t JOIN users u ON u.id=t.user_id WHERE t.hash=?', (digest(auth[7:]),)).fetchone()
                if not row: raise HTTPException(401, 'Conexión del agente inválida o revocada.')
                return {**dict(row), 'agent': True}
            session = request.cookies.get(COOKIE, '')
            row = db.execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.hash=? AND s.expires>?',
                             (digest(session), int(time.time()))).fetchone() if session else None
            return {**dict(row), 'agent': False} if row else None

    def account(request, browser=False):
        u = who(request)
        if not u or not u['verified']: raise HTTPException(401, 'Inicia sesión con tu correo.')
        if browser and u['agent']: raise HTTPException(403, 'Esta acción requiere tu sesión en el portal.')
        return u

    def set_session(response, uid):
        response.set_cookie(COOKIE, store.session(uid), max_age=86400 * 14, secure=True, httponly=True, samesite='lax', path='/')
        return response

    @app.middleware('http')
    async def guard(request, call_next):
        # Cabeceras y Origin no se aceptan como prueba de identidad.
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            auth = request.headers.get('authorization', '')
            if not auth.startswith('Bearer ') and request.headers.get('origin') not in origins:
                return JSONResponse({'detail': 'Origen no permitido.'}, status_code=403)
            try: size = int(request.headers.get('content-length', '0'))
            except ValueError: size = -1
            if size < 0 or size > MAX_BODY: return JSONResponse({'detail':'Tamaño no permitido.'}, status_code=413)
            chunks=[];received=0
            async for chunk in request.stream():
                received+=len(chunk)
                if received>MAX_BODY: return JSONResponse({'detail':'Tamaño no permitido.'},status_code=413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
            # Máximo 90 escrituras/minuto por conexión; sin guardar direcciones en disco.
            key = request.headers.get('cf-connecting-ip') or request.client.host
            now = int(time.time() // 60)
            with rate_lock:
                for old in [k for k, v in rate.items() if v[0] != now]: rate.pop(old, None)
                count = rate.get(key, (now, 0))[1] + 1
                if count > 90 or len(rate) > 10000:
                    return JSONResponse({'detail':'Demasiados cambios. Espera un minuto.'}, status_code=429, headers={'Retry-After':'60'})
                rate[key] = (now, count)
        started=time.perf_counter()
        status=500
        try:
            response = await call_next(request)
            status=response.status_code
        finally:
            route=getattr(request.scope.get('route'),'path','other')
            try:
                await run_in_threadpool(metrics.record,route,(time.perf_counter()-started)*1000,status)
            except sqlite3.Error:
                pass  # Telemetry must not prevent reading or publishing.
        response.headers['Cache-Control'] = 'private, no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        if 'Content-Security-Policy' not in response.headers:
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        analytics = analytics_configuration()
        if analytics and "sandbox" not in response.headers.get('Content-Security-Policy',''):
            policy = response.headers.get('Content-Security-Policy','')
            response.headers['Content-Security-Policy'] = policy.replace("script-src 'self';", "script-src 'self' " + analytics['origin'] + ";").replace("connect-src 'self';", "connect-src 'self' " + analytics['origin'] + ";")
        return response

    from portal.analytics import mount as mount_analytics, configuration as analytics_configuration
    mount_analytics(app, store, account, who, artifact_for, payload)
    mount_auth(app, store, origin, set_session, payload, clean, EMAIL)

    @app.get('/health')
    def health(): return {'service':'bottifact', 'status':'ok', 'storage':'nas-local'}

    @app.get('/api/operations/performance')
    def performance(request:Request):
        u=account(request,True)
        if not is_admin(u):raise HTTPException(403)
        return metrics.report()

    @app.get('/api/session')
    def session(request: Request):
        u = who(request)
        return {'user': {**{k:u[k] for k in ('id','email','name','verified')}, 'admin':is_admin(u),
                         'emails':owner_aliases() if u['verified'] and u['email'] in owner_aliases() else [u['email']]} if u else None}

    @app.post('/api/guest')
    async def guest(request: Request):
        if who(request): raise HTTPException(409, 'Ya tienes una sesión. Ciérrala para cambiar de persona.')
        body = await payload(request)
        aid = clean(body.get('artifact'), 120)
        with store.db() as db:
            a = artifact_for(db, aid, None)
            if not a['guests'] or a['comments'] != 'readers': raise HTTPException(403, 'El autor requiere iniciar sesión para comentar.')
            uid = uuid.uuid4().hex
            db.execute('INSERT INTO users VALUES(?,NULL,?,0)', (uid, clean(body.get('name'), 80)))
        return set_session(JSONResponse({'ok':True}), uid)

    @app.post('/api/logout')
    def logout(request: Request):
        with store.db() as db: db.execute('DELETE FROM sessions WHERE hash=?', (digest(request.cookies.get(COOKIE, '')),))
        response = JSONResponse({'ok':True});response.delete_cookie(COOKIE, path='/', secure=True, httponly=True, samesite='lax')
        return response

    @app.get('/auth/login')
    def login(request: Request):
        if not audience: raise HTTPException(503, 'El acceso por correo está pendiente de configuración.')
        try:
            token = request.headers.get('cf-access-jwt-assertion', '')
            key = jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(token, key, algorithms=['RS256'], audience=audience, issuer=issuer,
                                options={'require':['exp','iat','sub','email','iss','aud']}, leeway=15)
            if claims.get('type') != 'app': raise ValueError('Tipo de sesión inválido')
            u = store.user(claims['email'], claims.get('name') or claims['email'].split('@')[0])
        except Exception:
            raise HTTPException(401, 'No pudimos verificar la sesión de correo.') from None
        target = request.query_params.get('next', '/')
        if not re.fullmatch(r'/(?:a/[a-f0-9]{32})?', target): target = '/'
        return set_session(RedirectResponse(target, status_code=303), u['id'])

    @app.get('/auth/bootstrap')
    def bootstrap(request: Request):
        # Sólo puede emitir este enlace de un uso el administrador mediante SSH.
        token = request.query_params.get('code','')
        with store.db() as db:
            found = db.execute('SELECT * FROM logins WHERE hash=? AND expires>?', (digest(token), int(time.time()))).fetchone()
            if not found: raise HTTPException(401, 'Enlace vencido o utilizado.')
            db.execute('DELETE FROM logins WHERE hash=?', (digest(token),))
        return set_session(RedirectResponse('/', status_code=303), found['user_id'])

    @app.post('/api/tokens')
    async def new_token(request: Request):
        u = account(request, True);body = await payload(request)
        return {'token':store.token(u['id'], clean(body.get('label','Agente'),80))}

    @app.get('/api/tokens')
    def tokens(request: Request):
        u = account(request, True)
        with store.db() as db:
            return {'tokens':[dict(r) for r in db.execute('SELECT hash,label,created FROM tokens WHERE user_id=?', (u['id'],))]}

    @app.delete('/api/tokens/{key}')
    def revoke_token(key: str, request: Request):
        u = account(request, True)
        with store.db() as db: db.execute('DELETE FROM tokens WHERE hash=? AND user_id=?', (key,u['id']))
        return {'ok':True}

    @app.get('/api/artifacts')
    def artifacts(request: Request):
        u = account(request);view = request.query_params.get('view');public = view == 'public'
        params=request.query_params;query=clean(params.get('q',''),300,True)
        with store.db() as db:
            has_bookmarks=db.execute('SELECT 1 FROM bookmarks WHERE (owner=? OR ?) AND id NOT IN (SELECT bookmark FROM bookmark_migrations) LIMIT 1',(u['id'],is_admin(u))).fetchone()
            if not has_bookmarks:
                from portal.library_query import query as library_query
                try: result=library_query(db,u,params,is_admin)
                except (ValueError,TypeError,KeyError,UnicodeError):raise HTTPException(422,'Búsqueda o cursor inválido.') from None
                if params.get('graph')=='1':
                    nodes=result['artifacts'][:120]
                    return {'nodes':nodes,'edges':connections(nodes),'total':result['total'],'truncated':result['total']>len(nodes),'network':context_network(db,nodes,u)}
                return result
            rows = []
            for a in db.execute('SELECT * FROM artifacts WHERE owner=? OR ? OR visibility IN (\'public\',\'unlisted\') OR id IN (SELECT artifact FROM grants WHERE email=?) OR id IN (SELECT artifact FROM domain_grants WHERE domain=?) ORDER BY updated DESC',(u['id'],is_admin(u),u.get('email') or '',verified_domain(u))):
                r = role(db,a,u)
                explicit = db.execute('SELECT 1 FROM grants WHERE artifact=? AND email=? UNION SELECT 1 FROM domain_grants WHERE artifact=? AND domain=?', (a['id'],u.get('email') or '',a['id'],verified_domain(u))).fetchone()
                in_view = (view not in ('mine','archived') or a['owner']==u['id']) and (view!='shared' or (a['owner']!=u['id'] and explicit))
                if permissions(db,a,u)['read'] and ((public and a['visibility']=='public') or (not public and r and in_view)):
                    p = permissions(db,a,u)
                    notes = threads(snapshot(db,a,u)['events']) if p['review'] else []
                    meta=metadata(db,a['id'])
                    if not params.get('document_id') and bool(meta['archived']) != (view=='archived'):continue
                    drafts=db.execute("SELECT count(*) FROM versions v JOIN version_meta m ON m.version=v.id WHERE v.artifact=? AND m.state='draft'",(a['id'],)).fetchone()[0] if p['edit'] else 0
                    owner=db.execute('SELECT name,email FROM users WHERE id=?',(a['owner'],)).fetchone()
                    rows.append({**dict(a),**meta,**enrich(db,a,u),'owner_name':owner['name'],'owner_email':owner['email'] if is_admin(u) or a['owner']==u['id'] else None,'drafts':drafts,'permissions':p,'open_comments':sum(not n['resolved'] for n in notes)})
            if u and not public and view!='shared':
                for b in db.execute('SELECT * FROM bookmarks WHERE (owner=? OR ?) AND id NOT IN (SELECT bookmark FROM bookmark_migrations) ORDER BY created DESC',(u['id'],is_admin(u))):
                    if view in ('mine','archived') and b['owner']!=u['id']:continue
                    rows.append({**dict(b),'external':True,'category':'Enlaces','visibility':'external','updated':b['created'],'open_comments':0,'permissions':{'read':True,'review':False,'comment':False,'edit':False,'manage':False,'role':'owner'}})
            summary={'total':len(rows),'open_comments':sum(a['open_comments'] for a in rows),'shared':sum(a['visibility'] not in ('private','external') for a in rows)}
            spaces=sorted({a['space'] for a in rows})
            agents=sorted({a.get('source',{}).get('agent','') for a in rows}-{''})
            collections=sorted({v for a in rows for v in a.get('collections',[])})
            tags=sorted({v for a in rows for v in a.get('tags',[])+a.get('auto_tags',[])})
            rows=[a for a in rows if (not params.get('collection') or params['collection'] in a.get('collections',[])) and (not params.get('tag') or params['tag'] in a.get('tags',[])+a.get('auto_tags',[]))]
            categories=sorted({a.get('category','Sin clasificar') for a in rows})
            if params.get('category'):rows=[a for a in rows if a.get('category')==params['category']]
            if query:
                expression=match_query(query)
                hits={r['artifact']:{'excerpt':r['excerpt'],'rank':r['rank']} for r in db.execute("SELECT artifact,bm25(artifact_fts,0,0,8,3,1) AS rank,snippet(artifact_fts,4,'','',' … ',26) AS excerpt FROM artifact_fts WHERE artifact_fts MATCH ?",(expression,))} if expression else {}
                words=normalized(query).split()
                def metadata_match(a):
                    value=normalized(' '.join(a.get('tags',[])+a.get('auto_tags',[])+a.get('collections',[])+[a.get('category',''),a['title'],a['space']]+list(a.get('source',{}).values())))
                    return all(w in value for w in words)
                rows=[{**a,**hits.get(a['id'],{'excerpt':'','rank':0})} for a in rows if a['id'] in hits or metadata_match(a)]
            rows=[a for a in rows if (not params.get('space') or a['space']==params['space']) and (not params.get('access') or a['visibility']==params['access'])]
            if params.get('agent'):rows=[a for a in rows if a.get('source',{}).get('agent','').casefold()==params['agent'].casefold()]
            if params.get('review')=='pending':rows=[a for a in rows if a['open_comments']>0]
            if params.get('review')=='clear':rows=[a for a in rows if a['open_comments']==0]
            if params.get('document_id'):rows=[a for a in rows if a.get('document_id')==params['document_id']]
            from portal.table_query import parse as parse_filters, filter_rows
            try:rows=filter_rows(rows,parse_filters(params.get('filters')))
            except (ValueError,TypeError,KeyError):raise HTTPException(422,'Filtros inválidos.') from None
            total=len(rows)
            if params.get('graph')=='1':
                rows=[a for a in rows if not a.get('external')]
                total=len(rows)
                nodes=sorted(rows,key=lambda a:(-a['updated'],a['id']))[:120]
                return {'nodes':nodes,'edges':connections(nodes),'total':total,'truncated':total>len(nodes),'network':context_network(db,nodes,u)}
            try:rows,cursor=window(rows,params)
            except (ValueError,TypeError,KeyError,UnicodeError):raise HTTPException(422,'Búsqueda o cursor inválido.') from None
            return {'artifacts':rows,'total':total,'next_cursor':cursor,'summary':summary,'spaces':spaces,'collections':collections,'tags':tags,'categories':categories,'agents':agents}

    @app.post('/api/bookmarks')
    async def bookmark(request: Request):
        u=account(request);body=await payload(request);url=clean(body.get('url'),2000);parsed=urlsplit(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password: raise HTTPException(422,'Usa un enlace HTTPS sin credenciales.')
        title=clean(body.get('title'),200);space=clean(body.get('space','Sitio anterior'),60)
        with store.db() as db:
            found=db.execute('SELECT id FROM bookmarks WHERE owner=? AND url=?',(u['id'],url)).fetchone()
            if found:return {'id':found['id'],'url':url}
            if db.execute('SELECT count(*) FROM bookmarks WHERE owner=?',(u['id'],)).fetchone()[0]>=500:raise HTTPException(409,'Máximo 500 enlaces.')
            bid='link-'+uuid.uuid4().hex
            db.execute('INSERT INTO bookmarks VALUES(?,?,?,?,?,?)',(bid,u['id'],title,url,space,int(time.time())))
        return {'id':bid,'url':url}

    async def publish(request, aid=None):
        u = account(request);body = await payload(request)
        content = body.get('html')
        if not isinstance(content,str) or not content.strip() or len(content.encode()) > 20*1024*1024:
            raise HTTPException(422,'El HTML debe ocupar menos de 20 MB.')
        match = re.search(r'<meta\s+name=[\"\']nota-documento[\"\']\s+content=[\"\']([a-zA-Z0-9_-]{1,120})[\"\']',content)
        if not match: raise HTTPException(422,'Genera el archivo con Margen y un documento-id estable.')
        docid = match[1];title = clean(body.get('title'),200);space = clean(body.get('space','Personal'),60)
        from portal.formats import attachments as validate_attachments
        original_files=validate_attachments(body.get('attachments',[]))
        if aid and 'attachments' not in body:
            with store.db() as db:
                prior_artifact=artifact_for(db,aid,u,'edit')
                folder=store.files/'attachments'/prior_artifact['current_version']
                if folder.is_dir():original_files={f.name:f.read_bytes() for f in folder.iterdir() if f.is_file() and not f.is_symlink()}
        if original_files:
            digest=hashlib.sha256(b''.join(name.encode()+hashlib.sha256(blob).digest() for name,blob in sorted(original_files.items()))).hexdigest()
            content=re.sub(r'<!-- margen-originals:[a-f0-9]{64} -->','',content)+'<!-- margen-originals:'+digest+' -->'
        data = content.encode();sha = hashlib.sha256(data).hexdigest();version = uuid.uuid4().hex
        mode=body.get('mode','published')
        if mode not in ('draft','published'):raise HTTPException(422,'Estado de versión inválido.')
        source=provenance(body,clean)
        visibility=body.get('visibility','private')
        if visibility not in ('private','unlisted','public'): raise HTTPException(422,'Visibilidad inválida.')
        if aid and 'visibility' in body: raise HTTPException(422,'Una revisión conserva los permisos. Cámbialos desde Compartir.')
        with store.db() as db:
            if aid:
                a = artifact_for(db,aid,u,'edit')
                if db.execute('SELECT count(*) FROM versions WHERE artifact=?',(aid,)).fetchone()[0]>=200: raise HTTPException(409,'Máximo 200 versiones por documento.')
                visibility=a['visibility']
                if a['document_id'] != docid: raise HTTPException(409,'Esta revisión pertenece a otro documento-id.')
                if mode=='published' and a['owner']!=u['id']:
                    if 'mode' in body:raise HTTPException(403,'Sólo el creador publica una versión compartida.')
                    mode='draft'
                previous=db.execute("SELECT v.id,v.sha,m.title AS saved_title,m.space AS saved_space FROM versions v LEFT JOIN version_meta m ON m.version=v.id WHERE v.artifact=? AND COALESCE(m.state,'published')=? ORDER BY v.rowid DESC LIMIT 1",(aid,mode)).fetchone()
                if previous and previous['sha']==sha and (previous['saved_title'] or a['title'])==title and (previous['saved_space'] or a['space'])==space:
                    return {'id':aid,'version':previous['id'],'url':origin+'/a/'+aid,'visibility':visibility,'state':mode,'preview_url':origin+'/a/'+aid+('?version='+previous['id'] if mode=='draft' else '')}
            else:
                if db.execute('SELECT count(*) FROM artifacts WHERE owner=?',(u['id'],)).fetchone()[0] >= int(os.environ.get('MARGEN_MAX_ARTIFACTS','10000')):
                    raise HTTPException(409,'El espacio alcanzó el límite de documentos configurado.')
                aid = uuid.uuid4().hex
                db.execute('INSERT INTO artifacts(id,owner,title,space,document_id,updated,visibility) VALUES(?,?,?,?,?,?,?)',
                           (aid,u['id'],title,space,docid,int(time.time()),visibility))
            file = store.files/(sha+'.html')
            if not file.exists():
                temporary = store.files/(uuid.uuid4().hex+'.tmp');temporary.write_bytes(data);temporary.replace(file)
            for name,blob in original_files.items():
                folder=store.files/'attachments'/version;folder.mkdir(parents=True,exist_ok=True,mode=0o700);(folder/name).write_bytes(blob)
            db.execute('INSERT INTO versions VALUES(?,?,?,?)',(version,aid,sha,int(time.time())))
            db.execute('INSERT INTO version_meta VALUES(?,?,?,?,?)',(version,mode,title,space,json.dumps(source)))
            from portal.formats import describe
            db.execute('INSERT INTO version_formats VALUES(?,?)',(version,json.dumps(describe(content))))
            if mode=='published' or not db.execute('SELECT current_version FROM artifacts WHERE id=?',(aid,)).fetchone()[0]:
                db.execute('UPDATE artifacts SET title=?,space=?,current_version=?,updated=? WHERE id=?',(title,space,version,int(time.time()),aid))
                index_document(db,{'id':aid,'title':title,'space':space,'current_version':version},content)
            db.execute('INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)',(u['id'],'publish',aid,int(time.time())))
        return {'id':aid,'version':version,'url':origin+'/a/'+aid,'visibility':visibility,'state':mode,'preview_url':origin+'/a/'+aid+('?version='+version if mode=='draft' else '')}

    @app.post('/api/artifacts')
    async def create_artifact(request: Request): return await publish(request)

    @app.post('/api/artifacts/{aid}/versions')
    async def add_version(aid: str, request: Request): return await publish(request,aid)

    @app.patch('/api/artifacts/{aid}')
    async def rename_artifact(aid: str, request: Request):
        u=account(request);body=await payload(request)
        title=clean(body.get('title'),200);space=clean(body.get('space'),60)
        with store.db() as db:
            a=artifact_for(db,aid,u,'manage')
            if a['owner']!=u['id']:raise HTTPException(403,'Sólo el creador puede cambiar el nombre.')
            db.execute('UPDATE artifacts SET title=?,space=?,updated=? WHERE id=?',(title,space,int(time.time()),aid))
            db.execute('UPDATE artifact_fts SET title=?,space=? WHERE artifact=?',(title,space,aid))
            db.execute('INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)',(u['id'],'rename',aid,int(time.time())))
        return {'id':aid,'title':title,'space':space,'url':origin+'/a/'+aid}

    @app.get('/api/formats')
    def formats():
        from portal.formats import CAPABILITIES
        return {'version':1,'formats':CAPABILITIES}

    @app.get('/api/artifacts/{aid}')
    def artifact(aid: str, request: Request):
        u = who(request)
        with store.db() as db:
            a = artifact_for(db,aid,u);p = permissions(db,a,u)
            owner=bool(u and u['id']==a['owner'])
            fmt=db.execute('SELECT capabilities FROM version_formats WHERE version=?',(a['current_version'],)).fetchone()
            return {**a,**metadata(db,aid),**enrich(db,a,u),'format':json.loads(fmt['capabilities']) if fmt else None,'permissions':p,'versions':[{**dict(v),'source':v['source'] if owner else '{}'} for v in db.execute("SELECT v.id,v.created,COALESCE(m.state,'published') AS state,m.source FROM versions v LEFT JOIN version_meta m ON m.version=v.id WHERE v.artifact=? ORDER BY v.rowid DESC",(aid,)) if cited_version_readable(db,a,v['id'],u,permissions)],
                    'grants':[dict(g) for g in db.execute('SELECT email,role FROM grants WHERE artifact=?',(aid,))] if p['manage'] else [],
                    'access_revision':access_revision(db,a) if p['manage'] else None,
                    'domain_grants':[dict(g) for g in db.execute('SELECT domain,role FROM domain_grants WHERE artifact=? ORDER BY domain',(aid,))] if p['manage'] else []}

    @app.put('/api/artifacts/{aid}/access')
    async def access(aid: str, request: Request):
        u = account(request,True);body = await payload(request)
        visibility = body.get('visibility');scope = body.get('comments','reviewers');guests = body.get('guests',False)
        if visibility not in ['private','invited','unlisted','public'] or scope not in ['reviewers','readers'] or not isinstance(guests,bool):
            raise HTTPException(422,'Configuración de acceso inválida.')
        grants = body.get('grants',[])
        if not isinstance(grants,list) or len(grants)>100: raise HTTPException(422,'Máximo 100 invitados.')
        try:
            domains = parse_domain_grants(body['domain_grants']) if 'domain_grants' in body else None
        except ValueError as error:
            raise HTTPException(422,str(error)) from None
        unique = {}
        for g in grants:
            if not isinstance(g,dict): raise HTTPException(422,'Invitado inválido.')
            email = clean(g.get('email'),254).lower();r = g.get('role')
            if not EMAIL.fullmatch(email) or r not in ['viewer','commenter','editor']: raise HTTPException(422,'Invitado o permiso inválido.')
            unique[email] = r
        with store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            a = artifact_for(db,aid,u,'manage')
            if 'expected_access' in body and body['expected_access'] != access_revision(db,a):
                raise HTTPException(409,'Los permisos cambiaron. Cierra y vuelve a abrir Compartir antes de guardar.')
            # Privado significa sólo propietario, aunque antes tuviera invitados.
            db.execute('DELETE FROM grants WHERE artifact=?',(aid,))
            if visibility != 'private':
                db.executemany('INSERT INTO grants VALUES(?,?,?)',[(aid,e,r) for e,r in unique.items()])
            # Older clients omit domain_grants; preserve that audience unless explicitly private.
            if domains is not None or visibility == 'private':
                db.execute('DELETE FROM domain_grants WHERE artifact=?',(aid,))
                if visibility != 'private':
                    db.executemany('INSERT INTO domain_grants VALUES(?,?,?)',[(aid,d,r) for d,r in domains.items()])
            db.execute('UPDATE artifacts SET visibility=?,comments=?,guests=? WHERE id=?',(visibility,scope,int(guests),aid))
            db.execute('INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)',(u['id'],'access:'+visibility,aid,int(time.time())))
        return {'ok':True}

    @app.get('/api/artifacts/{aid}/review')
    def review(aid: str, request: Request):
        u = who(request)
        with store.db() as db:
            a = artifact_for(db,aid,u);p = permissions(db,a,u)
            return {'snapshot':snapshot(db,a,u),
                    'permissions':p,'author':u['name'] if u else '', 'actor':u['id'] if u else '', 'verified':bool(u and u['verified']),'artifact':{'id':aid,'title':a['title'],'url':origin+'/a/'+aid,'version':a['current_version']}}

    @app.post('/api/artifacts/{aid}/review')
    async def add_review(aid: str, request: Request):
        u = who(request)
        if not u: raise HTTPException(401,'Indica tu nombre o inicia sesión para comentar.')
        body = await payload(request);kind = body.get('kind');event_id = clean(body.get('id'),80);version = clean(body.get('version'),120)
        if not ID.fullmatch(event_id) or kind not in ['create','reply','edit','resolve','assign','delete']: raise HTTPException(422,'Comentario inválido.')
        request_hash = digest(json.dumps(body,sort_keys=True,separators=(',',':')))
        with store.db() as db:
            a = artifact_for(db,aid,u);p = permissions(db,a,u)
            personal=body.get('entry_type')=='note'
            if kind!='create':
                original=db.execute('SELECT event,actor FROM events WHERE id=? AND artifact=?',(body.get('thread'),aid)).fetchone()
                personal=bool(original and json.loads(original['event']).get('entry_type')=='note')
                if personal and original['actor']!=u['id']:raise HTTPException(404,'Nota no disponible.')
            if not (personal and u['verified']) and not p['comment']:raise HTTPException(404,'No puedes comentar en este documento.')
            old = db.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
            if old:
                if old['artifact']!=aid or old['actor']!=u['id'] or old['request_hash']!=request_hash: raise HTTPException(409,'Identificador en conflicto.')
                return review(aid,request)
            if not db.execute('SELECT 1 FROM versions WHERE id=? AND artifact=?',(version,aid)).fetchone(): raise HTTPException(409,'Versión desconocida.')
            if version_state(db,version)=='draft' and not p['edit']:raise HTTPException(404,'Versión no disponible.')
            entries = snapshot(db,a,u)['events']
            if db.execute('SELECT count(*) FROM events WHERE artifact=?',(aid,)).fetchone()[0]>=2000: raise HTTPException(409,'Esta revisión alcanzó 2000 cambios. Exporta el historial.')
            thread = event_id if kind=='create' else clean(body.get('thread'),80)
            if kind!='create':
                original = db.execute('SELECT actor,event FROM events WHERE artifact=? AND id=?',(aid,thread)).fetchone()
                if not original or json.loads(original['event'])['kind']!='create': raise HTTPException(404,'Hilo no disponible.')
                if kind in ['resolve','assign','delete'] and not (p['edit'] or personal): raise HTTPException(403,'Sólo el autor del documento y sus editores pueden gestionar hilos.')
                if kind=='edit' and not (p['edit'] or original['actor']==u['id']): raise HTTPException(403,'Sólo puedes editar tus comentarios.')
            e = {'id':event_id,'thread':thread,'kind':kind,'author':u['name'],'time':max(int(time.time()*1000),max([x['time'] for x in entries],default=0)+1),
                 'version':version,'actor':u['id'],'verified':bool(u['verified'])}
            if kind in ['create','reply','edit']: e['text'] = clean(body.get('text'),4000)
            if kind=='resolve':
                if not isinstance(body.get('resolved'),bool): raise HTTPException(422,'Estado inválido.')
                e['resolved']=body['resolved']
            if kind=='assign': e['assignee']=clean(body.get('assignee',''),80,True)
            if kind=='create':
                entry_type=body.get('entry_type','comment')
                if entry_type not in ('comment','note'):raise HTTPException(422,'Tipo inválido.')
                e['entry_type']=entry_type
                e['session']=clean(body.get('session',''),200,True)
                an=body.get('anchor',{})
                if not isinstance(an,dict): raise HTTPException(422,'Punto inválido.')
                anchor={k:clean(an.get(k,''),n,True) for k,n in [('reference',200),('tag',20),('text',4000),('quote',1200),('page',300),('section',300),('prefix',300),('suffix',300)]}
                for k in ['x','y']:
                    val=an.get(k)
                    if not isinstance(val,(int,float)) or isinstance(val,bool) or not 0<=val<=1: raise HTTPException(422,'Punto inválido.')
                    anchor[k]=val
                e['anchor']=anchor
            db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(event_id,aid,version,u['id'],request_hash,json.dumps(e,separators=(',',':')),e['time']))
            enqueue(db,a,e,permissions)
        return review(aid,request)

    mount_workspace(app,store,origin,who,account,payload,clean,artifact_for,permissions,threads,snapshot,is_admin)
    mount_context(app,store,origin,account,payload,clean,artifact_for,permissions)
    from portal.creator import mount as mount_creator
    mount_creator(app,store,origin,account,payload,clean,artifact_for,permissions,threads,snapshot)

    @lru_cache(maxsize=32)
    def static_preview(sha,title):
        return preview_html((store.files/(sha+'.html')).read_text(),title)

    @app.get('/api/artifacts/{aid}/preview')
    def preview(aid: str, request: Request):
        with store.db() as db:
            a=artifact_for(db,aid,who(request))
            v=db.execute('SELECT sha FROM versions WHERE id=? AND artifact=?',(a['current_version'],aid)).fetchone()
        return HTMLResponse(static_preview(v['sha'],a['title']),headers={'Content-Security-Policy':"sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src 'none'; script-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"})

    @app.get('/api/artifacts/{aid}/attachments/{vid}/{path:path}')
    def attachment(aid: str, vid: str, path: str, request: Request):
        with store.db() as db:
            a=artifact_for(db,aid,who(request))
            if version_state(db,vid)=='draft' and not permissions(db,a,who(request))['edit']:raise HTTPException(404)
            if not db.execute('SELECT 1 FROM versions WHERE id=? AND artifact=?',(vid,aid)).fetchone(): raise HTTPException(404)
        root=(store.files/'attachments'/vid).resolve();file=(root/path).resolve()
        if not file.is_relative_to(root) or not file.is_file(): raise HTTPException(404)
        return FileResponse(file,filename=file.name,media_type='application/octet-stream',headers={'Content-Security-Policy':"sandbox; default-src 'none'"})

    @app.get('/api/artifacts/{aid}/render')
    def render(aid: str, request: Request):
        u=who(request)
        with store.db() as db:
            a=artifact_for(db,aid,u);vid=request.query_params.get('version') or a['current_version']
            if not cited_version_readable(db,a,vid,u,permissions):raise HTTPException(404,'Versión no disponible.')
            v=db.execute('SELECT * FROM versions WHERE id=? AND artifact=?',(vid,aid)).fetchone()
            if not v: raise HTTPException(404,'Versión no encontrada.')
            content=(store.files/(v['sha']+'.html')).read_text()
        from urllib.parse import quote
        content=re.sub(r'href="([^"]+)" data-margen-original="([^"]+)"',lambda m:'data-bottifact-link href="/api/artifacts/'+aid+'/attachments/'+vid+'/'+quote(m[2],safe='')+'"',content)
        # El iframe y la cabecera CSP fuerzan origen opaco, incluso al abrir esta URL fuera del portal.
        bridge=(ROOT/'static/bridge.js').read_text()
        # Actualiza sólo el adaptador de revisión de la vista; conserva el HTML fuente en disco.
        revision=(ROOT/'static/review.js').read_text()
        content=re.sub(r'(<script\s+data-nota-modulo=[\"\'](?:revision|packages/core/components/review)\.js[\"\'][^>]*>).*?</script>',
                       lambda m:m[1]+revision+'</script>',content,flags=re.S)
        reader_controls=(ROOT/'static/reader-controls.js').read_text()
        script='<script>'+(ROOT/'static/interface.js').read_text()+'\n'+bridge+'\n'+reader_controls+'</script><style>'+(ROOT/'static/review-additions.css').read_text()+'</style>'
        head=re.search(r'<head(?:\s[^>]*)?>',content,re.I)
        position=head.end() if head else (re.match(r'\s*<!doctype[^>]*>',content,re.I).end() if re.match(r'\s*<!doctype[^>]*>',content,re.I) else 0)
        result=content[:position]+script+content[position:]
        return HTMLResponse(result,headers={'Content-Security-Policy':"sandbox allow-scripts allow-downloads; default-src 'none'; script-src 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; media-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"})

    @app.get('/login')
    def login_page(): return HTMLResponse((ROOT/'static/login.html').read_text())

    @app.get('/install')
    def install_page(): return HTMLResponse((ROOT/'static/install.html').read_text().replace('https://artifacts.botto.is',__import__('html').escape(origin,quote=True)))

    @app.get('/install.sh')
    def shell_installer():
        path=ROOT/'install.sh' if (ROOT/'install.sh').exists() else ROOT.parent/'scripts/install.sh'
        return Response(path.read_text().replace('https://artifacts.botto.is',origin),media_type='text/plain')

    @app.get('/install.py')
    def installer():
        path=ROOT/'install.py' if (ROOT/'install.py').exists() else ROOT.parent/'scripts/update.py'
        return Response(path.read_text().replace("ORIGIN = 'https://artifacts.botto.is'",'ORIGIN = '+repr(origin)),media_type='text/x-python')

    @app.get('/downloads/{name}')
    def download(name: str):
        if name not in ('bottifact-portable.zip','bottifact-portable.sha256','stable.json','stable.json.sig','preview.json','preview.json.sig','bottifact-preview.zip','bottifact-preview.sha256'): raise HTTPException(404)
        path=Path(os.environ.get('BOTTIFACT_RELEASES','/releases'))/name
        if not path.is_file(): raise HTTPException(503,'Paquete pendiente de publicación.')
        return FileResponse(path, filename=name)

    @app.get('/')
    @app.get('/a/{aid}')
    def page(request: Request, aid: str=''):
        if not aid and not (who(request) or {}).get('verified'): return RedirectResponse('/login', status_code=303)
        content=(ROOT/'static/index.html').read_text()
        if aid:content=content.replace('<body class="portal-app">','<body class="portal-app reading">').replace('<section id="library">','<section id="library" hidden>')
        return HTMLResponse(content)

    app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
    return app


app=create_app()
