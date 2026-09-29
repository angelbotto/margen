"""Owner editing, optimistic autosave and append-only attributed checkpoints."""
import copy
import hashlib
import json
import shutil
import time
import uuid
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from portal import block_source as blocks
from portal.formats import describe


def migrate(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS editor_sources(version TEXT PRIMARY KEY REFERENCES versions(id),document TEXT NOT NULL,template TEXT NOT NULL,parent TEXT,actor TEXT NOT NULL,kind TEXT NOT NULL,changes TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS editor_drafts(artifact TEXT PRIMARY KEY REFERENCES artifacts(id),owner TEXT NOT NULL REFERENCES users(id),base TEXT NOT NULL,source_version TEXT NOT NULL,revision INTEGER NOT NULL,document TEXT NOT NULL,template TEXT NOT NULL,updated INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS editor_checkpoints(artifact TEXT NOT NULL,request_id TEXT NOT NULL,revision INTEGER NOT NULL,version TEXT NOT NULL REFERENCES versions(id),PRIMARY KEY(artifact,request_id));
    ''')


def source_for(store,db,a,vid):
    if not isinstance(vid,str) or not 1<=len(vid)<=120:raise HTTPException(422,'Indica una versión válida.')
    row=db.execute('SELECT * FROM editor_sources WHERE version=?',(vid,)).fetchone()
    version=db.execute('SELECT v.*,m.title FROM versions v LEFT JOIN version_meta m ON m.version=v.id WHERE v.id=? AND v.artifact=?',(vid,a['id'])).fetchone()
    if not version:raise HTTPException(404,'Versión no disponible.')
    if row:return json.loads(row['document']),json.loads(row['template'])
    try:return blocks.import_document((store.files/(version['sha']+'.html')).read_text(),vid,version['title'] or a['title'])
    except ValueError as exc:raise HTTPException(422,str(exc))


def context_source(db,aid,vid):
    """Only immutable authorized-version references enter agent packets."""
    row=db.execute('SELECT parent,actor,kind,changes,document FROM editor_sources WHERE version=?',(vid,)).fetchone()
    if not row:return None
    return {'format':blocks.SCHEMA,'version':vid,'source_path':'/api/artifacts/'+aid+'/source?version='+vid,'parent_version':row['parent'],'actor':row['actor'],'kind':row['kind'],'changes':json.loads(row['changes']),'document':json.loads(row['document'])}


def mount(app,store,origin,account,payload,artifact_for,permissions):
    def owner(db,aid,u):
        a=artifact_for(db,aid,u,'edit')
        if a['owner']!=u['id']:raise HTTPException(403,'Sólo el autor puede editar este documento.')
        return a
    def draft_json(row,a):
        return {'artifact':a['id'],'base_version':row['base'],'source_version':row['source_version'],'revision':row['revision'],'updated':row['updated'],'document':json.loads(row['document']),'stale':row['base']!=a['current_version']}
    def fresh(row,a,body):
        if not row or type(body.get('revision')) is not int or body['revision']!=row['revision']:raise HTTPException(409,'El borrador cambió en otra pestaña. Conserva tu texto y vuelve a abrirlo.')
        if row['base']!=a['current_version']:raise HTTPException(409,'Hay una nueva versión publicada. Tu borrador se conserva; revisa los cambios antes de continuar.')

    @app.get('/api/artifacts/{aid}/source')
    def source(aid:str,request:Request):
        u=account(request)
        with store.db() as db:
            a=artifact_for(db,aid,u,'edit');vid=request.query_params.get('version') or a['current_version']
            doc,_=source_for(store,db,a,vid)
            return {'artifact':aid,'version':vid,'document':doc,'history':context_source(db,aid,vid)}

    @app.get('/api/artifacts/{aid}/editor')
    def read(aid:str,request:Request):
        u=account(request,True)
        with store.db() as db:
            a=owner(db,aid,u);row=db.execute('SELECT * FROM editor_drafts WHERE artifact=?',(aid,)).fetchone()
            if row:return draft_json(row,a)
            doc,_=source_for(store,db,a,a['current_version'])
            return {'artifact':aid,'base_version':a['current_version'],'source_version':a['current_version'],'revision':0,'document':doc,'stale':False,'updated':None}

    @app.put('/api/artifacts/{aid}/editor')
    async def save(aid:str,request:Request):
        u=account(request,True);body=await payload(request)
        with store.db() as db:
            a=owner(db,aid,u);row=db.execute('SELECT * FROM editor_drafts WHERE artifact=?',(aid,)).fetchone()
            if row:
                fresh(row,a,body);base=json.loads(row['document']);template=json.loads(row['template']);source_version=row['source_version'];revision=row['revision']
            else:
                if type(body.get('revision')) is not int or body['revision']!=0 or body.get('base_version')!=a['current_version']:raise HTTPException(409,'La versión cambió. Vuelve a abrir el documento.')
                base,template=source_for(store,db,a,a['current_version']);source_version=a['current_version'];revision=0
            try:doc=blocks.validate_document(body.get('document'),base,template)
            except (ValueError,TypeError) as exc:raise HTTPException(422,str(exc))
            encoded=json.dumps(doc,ensure_ascii=False)
            if row and json.loads(row['document'])==doc:return draft_json(row,a)
            db.execute('INSERT INTO editor_drafts VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(artifact) DO UPDATE SET revision=excluded.revision,document=excluded.document,updated=excluded.updated',
                       (aid,u['id'],a['current_version'],source_version,revision+1,encoded,json.dumps(template),int(time.time())))
            return draft_json(db.execute('SELECT * FROM editor_drafts WHERE artifact=?',(aid,)).fetchone(),a)

    @app.get('/api/artifacts/{aid}/editor/preview')
    def preview(aid:str,request:Request):
        u=account(request,True)
        with store.db() as db:
            a=owner(db,aid,u);row=db.execute('SELECT * FROM editor_drafts WHERE artifact=?',(aid,)).fetchone()
            if not row:raise HTTPException(404,'Guarda el borrador antes de abrir la vista previa.')
            content=blocks.render_document(json.loads(row['document']),json.loads(row['template']))
        return HTMLResponse(content,headers={'Content-Security-Policy':"sandbox allow-scripts allow-downloads; default-src 'none'; script-src 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; media-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"})

    @app.post('/api/artifacts/{aid}/editor/checkpoint')
    async def checkpoint(aid:str,request:Request):
        u=account(request,True);body=await payload(request);rid=body.get('request_id')
        if not isinstance(rid,str) or not 1<=len(rid)<=80:raise HTTPException(422,'Falta la identidad de esta operación.')
        with store.db() as db:
            a=owner(db,aid,u)
            previous=db.execute('SELECT * FROM editor_checkpoints WHERE artifact=? AND request_id=?',(aid,rid)).fetchone()
            if previous:
                if previous['revision']!=body.get('revision'):raise HTTPException(409,'Esta operación ya corresponde a otro borrador.')
                return {'id':aid,'version':previous['version'],'state':'draft','url':origin+'/a/'+aid+'?version='+previous['version']}
            row=db.execute('SELECT * FROM editor_drafts WHERE artifact=?',(aid,)).fetchone();fresh(row,a,body)
            if db.execute('SELECT count(*) FROM versions WHERE artifact=?',(aid,)).fetchone()[0]>=200:raise HTTPException(409,'Máximo 200 versiones por documento.')
            doc=json.loads(row['document']);template=json.loads(row['template']);parent=row['source_version']
            before,_=source_for(store,db,a,row['base'])
            change=blocks.changes(before,doc);html=blocks.render_document(doc,template)
            sha=hashlib.sha256(html.encode()).hexdigest();vid=uuid.uuid4().hex;now=int(time.time())
            path=store.files/(sha+'.html')
            if not path.exists():
                temp=store.files/(uuid.uuid4().hex+'.tmp');temp.write_text(html);temp.replace(path)
            folder=store.files/'attachments'/parent
            if folder.is_dir():shutil.copytree(folder,store.files/'attachments'/vid)
            kind='restore' if parent!=row['base'] else 'human'
            provenance={'kind':kind,'actor':u['id'],'author':u['name'],'label':'Edición en Margen','base_version':row['base'],'parent_version':row['base'],'restored_from':parent if kind=='restore' else None}
            db.execute('INSERT INTO versions VALUES(?,?,?,?)',(vid,aid,sha,now))
            db.execute('INSERT INTO version_meta VALUES(?,?,?,?,?)',(vid,'draft',doc['title'],a['space'],json.dumps(provenance)))
            db.execute('INSERT INTO version_formats VALUES(?,?)',(vid,json.dumps(describe(html))))
            db.execute('INSERT INTO editor_sources VALUES(?,?,?,?,?,?,?)',(vid,row['document'],row['template'],row['base'],u['id'],kind,json.dumps(change)))
            db.execute('INSERT INTO editor_checkpoints VALUES(?,?,?,?)',(aid,rid,row['revision'],vid))
            db.execute('INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)',(u['id'],'editor-checkpoint:'+vid,aid,now))
            return {'id':aid,'version':vid,'state':'draft','url':origin+'/a/'+aid+'?version='+vid}

    @app.get('/api/artifacts/{aid}/history')
    def history(aid:str,request:Request):
        u=account(request)
        with store.db() as db:
            a=owner(db,aid,u);items=[]
            for r in db.execute("SELECT v.id,v.created,m.state,m.source,m.title,e.parent,e.kind,e.changes,u.name AS author FROM versions v LEFT JOIN version_meta m ON m.version=v.id LEFT JOIN editor_sources e ON e.version=v.id LEFT JOIN users u ON u.id=e.actor WHERE v.artifact=? ORDER BY v.rowid DESC",(aid,)):
                item=dict(r);source=json.loads(item.pop('source') or '{}');item['author']=item['author'] or source.get('author') or source.get('agent') or 'Origen sin registrar';item['changes']=json.loads(item['changes']) if item['changes'] else [];items.append(item)
            return {'current_version':a['current_version'],'versions':items}

    @app.get('/api/artifacts/{aid}/changes')
    def diff(aid:str,request:Request):
        u=account(request)
        with store.db() as db:
            a=artifact_for(db,aid,u,'edit');left=request.query_params.get('from');right=request.query_params.get('to') or a['current_version']
            before,_=source_for(store,db,a,left);after,_=source_for(store,db,a,right)
            return {'from':left,'to':right,'changes':blocks.changes(before,after),'scope':'Bloques editoriales; los componentes conservados requieren comparación visual.'}

    @app.post('/api/artifacts/{aid}/editor/restore')
    async def restore(aid:str,request:Request):
        u=account(request,True);body=await payload(request)
        with store.db() as db:
            a=owner(db,aid,u)
            if body.get('expected_current')!=a['current_version']:raise HTTPException(409,'La versión publicada cambió.')
            row=db.execute('SELECT * FROM editor_drafts WHERE artifact=?',(aid,)).fetchone();revision=row['revision'] if row else 0
            if type(body.get('revision')) is not int or body['revision']!=revision:raise HTTPException(409,'El borrador cambió. Revísalo antes de restaurar.')
            vid=body.get('version');doc,template=source_for(store,db,a,vid)
            db.execute('INSERT OR REPLACE INTO editor_drafts VALUES(?,?,?,?,?,?,?,?)',(aid,u['id'],a['current_version'],vid,revision+1,json.dumps(doc),json.dumps(template),int(time.time())))
            db.execute('INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)',(u['id'],'editor-restore:'+vid,aid,int(time.time())))
            return draft_json(db.execute('SELECT * FROM editor_drafts WHERE artifact=?',(aid,)).fetchone(),a)
