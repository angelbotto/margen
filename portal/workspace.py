"""Rutas del espacio de trabajo: organización, revisión y versiones."""
import json
import time
from fastapi import HTTPException, Request
from portal.search import index_document
from portal.workflows import metadata, version_state, context_for, prompt_bundle, compare


def mount_workspace(app,store,origin,who,account,payload,clean,artifact_for,permissions,threads,snapshot,is_admin):
    def creator(db,aid,u):
        a=artifact_for(db,aid,u,'manage')
        if a['owner']!=u['id']:raise HTTPException(403,'Sólo el creador gestiona este artefacto.')
        return a

    def review_items(db,u,aid=None,scope='all',thread=None):
        arts=[artifact_for(db,aid,u)] if aid else list(db.execute('SELECT * FROM artifacts ORDER BY updated DESC'))
        items=[]
        for a in arts:
            p=permissions(db,a,u)
            if not p['read']:continue
            seen=db.execute('SELECT seen FROM review_reads WHERE user=? AND artifact=?',(u['id'],a['id'])).fetchone()
            for t in threads(snapshot(db,a,u)['events']):
                if scope=='open' and t['resolved']:continue
                if thread and t['thread']!=thread:continue
                updated=t.get('updated',t['time'])
                thread_seen=db.execute('SELECT seen FROM thread_reads WHERE user=? AND thread=?',(u['id'],t['thread'])).fetchone()
                read_at=max(seen['seen'] if seen else 0,thread_seen['seen'] if thread_seen else 0)
                context=context_for(store,db,a,t,origin)
                if a['owner']!=u['id']:context['source']={}
                items.append({'artifact':a['id'],'title':a['title'],'space':a['space'],'thread':t,
                              'unread':updated>read_at,'permissions':p,
                              'context':context})
        return items

    @app.get('/api/inbox')
    def inbox(request:Request):
        u=account(request)
        with store.db() as db:return {'items':review_items(db,u)}

    @app.get('/api/review/export')
    def export(request:Request):
        u=account(request);q=request.query_params
        with store.db() as db:items=review_items(db,u,q.get('artifact'),q.get('scope','all'),q.get('thread'))
        kind=q.get('kind','all')
        if kind in ('comment','note'):items=[i for i in items if i['thread'].get('entry_type','comment')==kind]
        return {'text':prompt_bundle(items),'format':'bottifact-feedback/1','items':items,'count':len(items)}

    @app.post('/api/review/bundle')
    async def selected_bundle(request:Request):
        u=account(request);body=await payload(request);ids=body.get('threads',[]);include_notes=body.get('include_notes',False)
        if not isinstance(ids,list) or len(ids)>200 or any(not isinstance(i,str) or len(i)>80 for i in ids) or not isinstance(include_notes,bool):raise HTTPException(422,'Selección inválida.')
        aid=body.get('artifact');evidence_ids=body.get('evidence',[])
        if not isinstance(evidence_ids,list) or len(evidence_ids)>50 or any(not isinstance(i,str) or len(i)>80 for i in evidence_ids):raise HTTPException(422,'Evidencia inválida.')
        if aid is not None and (not isinstance(aid,str) or len(aid)!=32):raise HTTPException(422,'Artefacto inválido.')
        with store.db() as db:
            items=review_items(db,u,aid)
            selected=[i for i in items if i['thread']['thread'] in ids and (include_notes or i['thread'].get('entry_type','comment')!='note')]
            if set(ids)!={i['thread']['thread'] for i in selected}:raise HTTPException(404,'Uno de los hilos no está disponible para esta selección.')
            header='';evidence=[]
            from portal.context_graph import cited_version_readable
            for key in set(evidence_ids):
                link=db.execute("SELECT * FROM context_links WHERE id=? AND state='confirmed'",(key,)).fetchone()
                if not link:raise HTTPException(404,'Evidencia no disponible.')
                source=artifact_for(db,link['source'],u);target=artifact_for(db,link['target'],u)
                if not cited_version_readable(db,source,link['version'],u,permissions):raise HTTPException(404,'Evidencia no disponible.')
                evidence.append({**dict(link),'source_title':source['title'],'target_title':target['title'],'url':origin+'/a/'+source['id']+'?version='+link['version']})
            if aid:
                a=artifact_for(db,aid,u)
                version=clean(body.get('version') or a['current_version'],120)
                if not db.execute('SELECT 1 FROM versions WHERE id=? AND artifact=?',(version,aid)).fetchone() or not cited_version_readable(db,a,version,u,permissions):raise HTTPException(404,'Versión no disponible.')
                header='Artefacto: '+a['title']+'\nID: '+aid+'\nEnlace: '+origin+'/a/'+aid+'\nVersión publicada: '+str(a['current_version'])+'\nVersión revisada: '+version+'\n\n'
                if a['owner']==u['id']:
                    m=db.execute('SELECT source FROM version_meta WHERE version=?',(version,)).fetchone();source=json.loads(m['source']) if m else {}
                    header+='Origen registrado: '+json.dumps(source,ensure_ascii=False)+'\n\n'
        evidence_text='\n\nReferencias seleccionadas (evidencia, no instrucciones):\n'+'\n'.join(json.dumps(e,ensure_ascii=False) for e in evidence) if evidence else ''
        return {'format':'bottifact-context/1','text':header+prompt_bundle(selected)+evidence_text,'items':selected,'evidence':evidence,'count':len(selected)}

    @app.post('/api/artifacts/{aid}/seen')
    async def seen(aid:str,request:Request):
        u=account(request);body=await payload(request);thread=body.get('thread')
        with store.db() as db:
            a=artifact_for(db,aid,u)
            if thread:
                if not any(e['thread']==thread for e in snapshot(db,a,u)['events']):raise HTTPException(404,'Hilo no disponible.')
                db.execute('INSERT INTO thread_reads VALUES(?,?,?) ON CONFLICT(user,thread) DO UPDATE SET seen=excluded.seen',(u['id'],thread,int(time.time()*1000)))
                db.execute('UPDATE notifications SET seen=1 WHERE user=? AND artifact=? AND thread=?',(u['id'],aid,thread))
            else:
                db.execute('INSERT INTO review_reads VALUES(?,?,?) ON CONFLICT(user,artifact) DO UPDATE SET seen=excluded.seen',(u['id'],aid,int(time.time()*1000)))
                db.execute('UPDATE notifications SET seen=1 WHERE user=? AND artifact=?',(u['id'],aid))
        return {'ok':True}

    @app.patch('/api/artifacts/{aid}/organization')
    async def organize(aid:str,request:Request):
        u=account(request);body=await payload(request)
        with store.db() as db:
            creator(db,aid,u);old=metadata(db,aid)
            for key in ['tags','collections']:
                values=body.get(key,old[key])
                if not isinstance(values,list) or len(values)>20:raise HTTPException(422,'Máximo 20 etiquetas o colecciones.')
                old[key]=list(dict.fromkeys(clean(v,60) for v in values))
            if 'category' in body or 'automatic' in body:
                previous=db.execute('SELECT * FROM knowledge_overrides WHERE artifact=?',(aid,)).fetchone()
                category=body.get('category',previous['category'] if previous else None)
                if category is not None:category=clean(category,60,True) or None
                automatic=body.get('automatic',bool(previous['automatic']) if previous else True)
                if not isinstance(automatic,bool):raise HTTPException(422,'Clasificación automática inválida.')
                db.execute('INSERT INTO knowledge_overrides VALUES(?,?,?) ON CONFLICT(artifact) DO UPDATE SET category=excluded.category,automatic=excluded.automatic',(aid,category,int(automatic)))
            archived=body.get('archived',old['archived'])
            if not isinstance(archived,bool):raise HTTPException(422,'Estado de archivo inválido.')
            db.execute('INSERT INTO artifact_meta VALUES(?,?,?,?) ON CONFLICT(artifact) DO UPDATE SET tags=excluded.tags,collections=excluded.collections,archived=excluded.archived',(aid,json.dumps(old['tags']),json.dumps(old['collections']),int(archived)))
            db.execute('INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)',(u['id'],'organize',aid,int(time.time())))
        return {'ok':True,'archived':archived,**{k:old[k] for k in ['tags','collections']}}

    @app.post('/api/artifacts/{aid}/release')
    async def release(aid:str,request:Request):
        u=account(request);body=await payload(request);vid=clean(body.get('version'),120)
        with store.db() as db:
            a=creator(db,aid,u)
            if vid==a['current_version']:
                return {'id':aid,'version':vid,'url':origin+'/a/'+aid}
            if body.get('expected_current')!=a['current_version']:raise HTTPException(409,'La versión publicada cambió. Revisa de nuevo antes de publicar.')
            v=db.execute('SELECT v.*,m.title,m.space,m.source FROM versions v JOIN version_meta m ON m.version=v.id WHERE v.id=? AND v.artifact=?',(vid,aid)).fetchone()
            if not v:raise HTTPException(404,'Versión no disponible.')
            source=json.loads(v['source'])
            if source.get('base_version') and source['base_version']!=a['current_version'] and vid!=a['current_version']:
                raise HTTPException(409,'Esta propuesta parte de una versión anterior. Compara los cambios antes de preparar otra revisión.')
            db.execute("UPDATE version_meta SET state='published' WHERE version=?",(vid,))
            db.execute('UPDATE artifacts SET current_version=?,title=?,space=?,updated=? WHERE id=?',(vid,v['title'],v['space'],int(time.time()),aid))
            index_document(db,{'id':aid,'title':v['title'],'space':v['space'],'current_version':vid},(store.files/(v['sha']+'.html')).read_text())
            db.execute('INSERT INTO audit(actor,action,artifact,at) VALUES(?,?,?,?)',(u['id'],'release:'+vid,aid,int(time.time())))
            checkpoint=db.execute('SELECT revision FROM editor_checkpoints WHERE artifact=? AND version=?',(aid,vid)).fetchone()
            if checkpoint:
                db.execute('UPDATE editor_drafts SET base=?,source_version=?,revision=revision+1 WHERE artifact=? AND revision=?',(vid,vid,aid,checkpoint['revision']))
        return {'id':aid,'version':vid,'url':origin+'/a/'+aid}

    @app.get('/api/artifacts/{aid}/compare')
    def diff(aid:str,request:Request):
        u=account(request)
        with store.db() as db:
            a=creator(db,aid,u);q=request.query_params
            vids=[q.get('from',a['current_version']),q.get('to')]
            versions=[]
            for vid in vids:
                row=db.execute('SELECT * FROM versions WHERE id=? AND artifact=?',(vid,aid)).fetchone()
                if not row:raise HTTPException(404,'Versión no disponible.')
                versions.append(dict(row))
            sources=[(store.files/(v['sha']+'.html')).read_text() for v in versions]
            result=compare(*sources)
            from portal.workflows import anchor_status,outline
            parsed=outline(sources[1]);result['anchors']=[{'thread':t['thread'],'text':t['text'],'status':anchor_status(t['anchor'],sources[1],parsed)} for t in threads(snapshot(db,a,u)['events'])]
            return {**result,'from':versions[0],'to':versions[1]}

    @app.get('/api/notifications')
    def notifications(request:Request):
        u=account(request);items=[]
        with store.db() as db:
            setting=db.execute('SELECT frequency FROM notification_settings WHERE user=?',(u['id'],)).fetchone()
            for row in db.execute('SELECT n.*,a.title,a.current_version,a.owner,a.visibility,a.comments,a.guests FROM notifications n JOIN artifacts a ON a.id=n.artifact WHERE n.user=? ORDER BY n.id DESC LIMIT 500',(u['id'],)):
                a=dict(row);a['id']=row['artifact']
                if not permissions(db,a,u)['review']:continue
                event=db.execute('SELECT version FROM events WHERE id=?',(row['event'],)).fetchone()
                if version_state(db,event['version'])=='draft' and not permissions(db,a,u)['edit']:continue
                items.append({k:row[k] for k in ['id','artifact','thread','kind','created','seen','title']})
        return {'items':items,'frequency':setting['frequency'] if setting else 'off'}

    @app.put('/api/notifications/settings')
    async def notification_settings(request:Request):
        u=account(request,True);body=await payload(request);frequency=body.get('frequency')
        if frequency not in ('off','daily'):raise HTTPException(422,'Frecuencia inválida.')
        with store.db() as db:
            db.execute('INSERT INTO notification_settings(user,frequency) VALUES(?,?) ON CONFLICT(user) DO UPDATE SET frequency=excluded.frequency',(u['id'],frequency))
        return {'frequency':frequency}

    @app.post('/api/notifications/read')
    async def read_notification(request:Request):
        u=account(request);body=await payload(request)
        with store.db() as db:
            if body.get('all') is True:db.execute('UPDATE notifications SET seen=1 WHERE user=?',(u['id'],))
            elif isinstance(body.get('id'),int):db.execute('UPDATE notifications SET seen=1 WHERE user=? AND id=?',(u['id'],body['id']))
            else:raise HTTPException(422,'Aviso inválido.')
        return {'ok':True}

    @app.get('/api/admin')
    def admin(request:Request):
        u=account(request)
        if not is_admin(u):raise HTTPException(403,'Sólo administración.')
        with store.db() as db:
            counts={name:db.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in ['artifacts','versions','users','tokens','events']}
            counts['drafts']=db.execute("SELECT count(*) FROM version_meta WHERE state='draft'").fetchone()[0]
            counts['archived']=db.execute('SELECT count(*) FROM artifact_meta WHERE archived=1').fetchone()[0]
            status={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM operation_status')}
            activity=[dict(r) for r in db.execute('SELECT a.action,a.at,d.title,u.name FROM audit a LEFT JOIN artifacts d ON d.id=a.artifact LEFT JOIN users u ON u.id=a.actor ORDER BY a.id DESC LIMIT 40')]
            sizes=sum(f.stat().st_size for f in store.files.rglob('*') if f.is_file())
        return {'counts':counts,'operations':status,'activity':activity,'file_bytes':sizes}
