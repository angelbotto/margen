"""Authorized neural narration: immutable sessions, streaming, bounded private cache.
Provider calls are impossible unless explicitly configured. No credential discovery.
"""
import asyncio
import hashlib
import json
import threading
import time
import uuid
from http.client import HTTPException as HTTPTransportError
from decimal import Decimal, ROUND_CEILING
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from starlette.concurrency import run_in_threadpool
from portal.context_graph import cited_version_readable
from portal.narration_providers import Configuration, Provider, PROFILES, prosody, request_data
from portal.narration_text import manifest, select_blocks

MAX_AUDIO=8*1024*1024

class Narration:
    def __init__(self,store,config=None):
        self.store=store;self.config=config or Configuration.environment();self.provider=Provider(self.config)
        self.lock=threading.RLock();self.sessions={}
        with store.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS narration_cache(
              key TEXT PRIMARY KEY, artifact TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
              version TEXT NOT NULL REFERENCES versions(id) ON DELETE CASCADE,
              created INTEGER NOT NULL, used INTEGER NOT NULL, audio BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS narration_usage(
              day INTEGER NOT NULL, user TEXT NOT NULL, chars INTEGER NOT NULL, micro_usd INTEGER NOT NULL,
              PRIMARY KEY(day,user));
            ''')
            self.trim(db)

    def trim(self,db):
        now=int(time.time())
        db.execute('DELETE FROM narration_cache WHERE created<?',(now-self.config.cache_seconds,))
        rows=db.execute('SELECT key,length(audio) AS size FROM narration_cache ORDER BY used DESC').fetchall();size=0
        for row in rows:
            size+=row['size']
            if size>self.config.cache_bytes:db.execute('DELETE FROM narration_cache WHERE key=?',(row['key'],))
        db.execute('DELETE FROM narration_usage WHERE day<?',(int(time.time()//86400)-31,))

    def stop(self,session):
        session['cancelled']=True
        for entry in session['entries']:
            response=entry.pop('response',None)
            if response:
                try:response.close()
                except Exception:pass
        session['blocks']=[]

    def sweep(self):
        now=time.time()
        for sid,s in list(self.sessions.items()):
            if s['expires']<now or s['cancelled']:
                self.stop(s);self.sessions.pop(sid,None)

    def reserve(self,text,body):
        # UTF-8 request bytes are a conservative envelope above text characters,
        # including markup/metadata. Unit price must be explicitly approved.
        units=max(len(text),len(body))
        return int((Decimal(units)*Decimal(self.config.price_per_million)).to_integral_value(rounding=ROUND_CEILING))


def mount(app,store,account,payload,artifact_for,permissions):
    service=Narration(store);app.state.narration=service

    def document(request,aid,version):
        user=account(request,browser=True)
        with store.db() as db:
            a=artifact_for(db,aid,user)
            v=db.execute('SELECT * FROM versions WHERE id=? AND artifact=?',(version,aid)).fetchone()
            if not v or not cited_version_readable(db,a,version,user,permissions):raise HTTPException(404,'Versión no disponible.')
            return user,a,dict(v)

    def enabled():
        if not service.config.enabled:raise HTTPException(503,service.config.reason)

    def session_for(request,aid,sid):
        user=account(request,browser=True)
        with service.lock:
            service.sweep();s=service.sessions.get(sid)
            if not s or s['user']!=user['id'] or s['artifact']!=aid or s['cancelled']:raise HTTPException(404,'Lectura no disponible. Inicia de nuevo.')
        _,_,v=document(request,aid,s['version'])
        if v['sha']!=s['sha']:raise HTTPException(409,'El documento cambió. Inicia de nuevo.')
        enabled()
        return s

    @app.get('/api/artifacts/{aid}/narration')
    def configuration(aid:str,version:str,request:Request):
        document(request,aid,version)
        return service.config.public()

    @app.get('/api/artifacts/{aid}/narration/manifest')
    def source_manifest(aid:str,version:str,request:Request):
        _,_,v=document(request,aid,version);enabled()
        source=(store.files/(v['sha']+'.html')).read_text()
        return {'version':version,'sha':v['sha'],'blocks':[{k:b[k] for k in ('id','text','anchors','kind')} for b in manifest(source)]}

    @app.post('/api/artifacts/{aid}/narration/sessions')
    async def create_session(aid:str,request:Request):
        body=await payload(request);user,_,v=document(request,aid,body.get('version'));enabled()
        if body.get('confirmed') is not True:raise HTTPException(422,'Confirma el procesamiento externo en el portal.')
        voice=next((v for v in service.config.voices if v['id']==body.get('voice')),None)
        if not voice or body.get('profile') not in PROFILES:raise HTTPException(422,'Elige voz y estilo de lectura.')
        if body.get('sha')!=v['sha']:raise HTTPException(409,'La versión cambió. Revisa la selección.')
        try:blocks=select_blocks((store.files/(v['sha']+'.html')).read_text(),body.get('blocks'))
        except ValueError as e:raise HTTPException(422,str(e)) from None
        with service.lock:
            service.sweep()
            active=[s for s in service.sessions.values() if not s['cancelled']]
            if len(active)>=16 or sum(s['user']==user['id'] for s in active)>=2:raise HTTPException(429,'Hay demasiadas lecturas abiertas. Detén una antes de continuar.')
            sid=uuid.uuid4().hex
            session={'id':sid,'artifact':aid,'version':v['id'],'sha':v['sha'],'user':user['id'],'voice':voice,'profile':body['profile'],
                     'blocks':blocks,'entries':[{'state':'new'} for _ in blocks], 'expires':time.time()+3600,'cancelled':False,
                     'config':service.config.fingerprint()}
            service.sessions[sid]=session
        return {'id':sid,'count':len(blocks),'characters':sum(len(b['text']) for b in blocks)}

    @app.delete('/api/artifacts/{aid}/narration/sessions/{sid}')
    async def cancel(aid:str,sid:str,request:Request):
        # Cancellation needs ownership, even if document access has just been revoked.
        user=account(request,browser=True)
        with service.lock:
            s=service.sessions.get(sid)
            if not s or s['user']!=user['id'] or s['artifact']!=aid:raise HTTPException(404)
            s['cancelled']=True
        await run_in_threadpool(service.stop,s)
        return {'ok':True}

    @app.delete('/api/artifacts/{aid}/narration/cache')
    async def purge(aid:str,request:Request):
        user=account(request,browser=True)
        with service.lock:
            with store.db() as db:
                artifact_for(db,aid,user,'manage')
                sessions=[s for s in service.sessions.values() if s['artifact']==aid]
                for s in sessions:s['cancelled']=True
                db.execute('PRAGMA secure_delete=ON');db.execute('DELETE FROM narration_cache WHERE artifact=?',(aid,))
        for s in sessions:await run_in_threadpool(service.stop,s)
        return {'ok':True}

    @app.post('/api/artifacts/{aid}/narration/sessions/{sid}/blocks/{index}')
    async def prepare(aid:str,sid:str,index:int,request:Request):
        s=session_for(request,aid,sid)
        with service.lock:
            if s['cancelled'] or not 0<=index<len(s['entries']):raise HTTPException(404)
            entry=s['entries'][index]
            if entry['state']!='new':raise HTTPException(409,'Este fragmento ya fue solicitado; no se volverá a generar.')
            if any(e['state'] in ('opening','ready','streaming') for e in s['entries']):raise HTTPException(409,'Termina el fragmento actual antes de pedir el siguiente.')
            if sum(e['state'] in ('opening','ready','streaming') for x in service.sessions.values() for e in x['entries'])>=2:raise HTTPException(429,'El servicio está ocupado. Intenta más tarde.')
            block=s['blocks'][index];entry['state']='opening'
            key=hashlib.sha256(json.dumps([aid,s['version'],s['sha'],block,s['voice'],s['profile'],s['config']],sort_keys=True).encode()).hexdigest()
            entry['key']=key
        try:
            with store.db() as db:
                service.trim(db)
                cached=db.execute('SELECT length(audio) AS size FROM narration_cache WHERE key=?',(key,)).fetchone()
                if cached:entry['cached']=True
                else:
                    _,provider_body,_=request_data(service.config,block,s['voice'],s['profile'])
                    cost=service.reserve(block['text'],provider_body);day=int(time.time()//86400);chars=len(block['text'])
                    totals=db.execute('SELECT coalesce(sum(chars),0) AS chars,coalesce(sum(micro_usd),0) AS cost FROM narration_usage WHERE day=?',(day,)).fetchone()
                    own=db.execute('SELECT chars FROM narration_usage WHERE day=? AND user=?',(day,s['user'])).fetchone()
                    if totals['chars']+chars>service.config.daily_chars or (own['chars'] if own else 0)+chars>service.config.user_chars or totals['cost']+cost>service.config.daily_micro_usd:raise HTTPException(429,'Se alcanzó el límite de narración. No se generó este fragmento.')
                    db.execute('INSERT INTO narration_usage VALUES(?,?,?,?) ON CONFLICT(day,user) DO UPDATE SET chars=chars+excluded.chars,micro_usd=micro_usd+excluded.micro_usd',(day,s['user'],chars,cost))
            if not entry.get('cached'):
                response=await run_in_threadpool(service.provider.open,block,s['voice'],s['profile'])
                with service.lock:entry['response']=response
            session_for(request,aid,sid)
            if await request.is_disconnected():raise HTTPException(409,'Lectura cancelada.')
            with service.lock:
                if s['cancelled']:raise HTTPException(409,'Lectura cancelada.')
                entry['state']='ready'
            # An unclaimed provider stream cannot remain open indefinitely.
            def expire_ready():
                with service.lock:
                    pending=entry['state']=='ready'
                    if pending:s['cancelled']=True
                if pending:service.stop(s)
            timer=threading.Timer(20,expire_ready);timer.daemon=True;timer.start()
            return {'url':f'/api/artifacts/{aid}/narration/sessions/{sid}/audio/{index}','pause_ms':prosody(block,s['profile'])['pause_ms']}
        except BaseException as e:
            entry['state']='failed';response=entry.pop('response',None)
            if response:await run_in_threadpool(response.close)
            if isinstance(e,(HTTPException,asyncio.CancelledError)):raise
            raise HTTPException(502,'El proveedor no pudo preparar el audio. No se cambió a otra voz.') from None

    @app.get('/api/artifacts/{aid}/narration/sessions/{sid}/status/{index}')
    def status(aid:str,sid:str,index:int,request:Request):
        s=session_for(request,aid,sid)
        with service.lock:
            if not 0<=index<len(s['entries']):raise HTTPException(404)
            return {'state':s['entries'][index]['state']}

    @app.get('/api/artifacts/{aid}/narration/sessions/{sid}/audio/{index}')
    async def audio(aid:str,sid:str,index:int,request:Request):
        s=session_for(request,aid,sid)
        with service.lock:
            if s['cancelled'] or not 0<=index<len(s['entries']):raise HTTPException(404)
            entry=s['entries'][index]
            if entry['state'] not in ('ready','complete'):raise HTTPException(409,'Audio no preparado o ya en reproducción.')
            if request.headers.get('range') not in (None,'bytes=0-'):raise HTTPException(416,'No se admite búsqueda en audio en curso.')
            key=entry['key'];block=s['blocks'][index]
            with store.db() as db:
                cached=db.execute('SELECT audio FROM narration_cache WHERE key=? AND created>=?',(key,int(time.time())-service.config.cache_seconds)).fetchone()
                if cached:db.execute('UPDATE narration_cache SET used=? WHERE key=?',(int(time.time()),key))
            if cached:
                entry['state']='complete'
                return Response(bytes(cached['audio']),media_type='audio/mpeg',headers={'Cache-Control':'private, no-store'})
            if entry.get('cached') or entry['state']=='complete':raise HTTPException(410,'El audio expiró. Inicia una nueva lectura.')
            response=entry.get('response')
            if not response:raise HTTPException(410,'La lectura fue cancelada.')
            entry['state']='streaming'
        async def stream():
            output=bytearray();complete=False
            try:
                while True:
                    session_for(request,aid,sid)
                    if await request.is_disconnected():break
                    part=await run_in_threadpool(getattr(response,'read1',response.read),16384)
                    if not part:
                        if getattr(response,'length',None) not in (None,0):raise ValueError('Audio incompleto.')
                        complete=bool(output);break
                    session_for(request,aid,sid)
                    output.extend(part)
                    if len(output)>MAX_AUDIO:raise ValueError('Audio demasiado largo.')
                    yield part
                if complete and output:
                    session_for(request,aid,sid)
                    with service.lock:
                        if not s['cancelled']:
                            with store.db() as db:
                                now=int(time.time());db.execute('INSERT OR REPLACE INTO narration_cache VALUES(?,?,?,?,?,?)',(key,aid,s['version'],now,now,bytes(output)));service.trim(db)
                            entry['state']='complete'
            except (HTTPException,HTTPTransportError,ValueError,OSError):
                # The media element receives an interrupted stream, not provider error text.
                complete=False
            finally:
                response.close();entry.pop('response',None)
                if not complete:entry['state']='failed'
        return StreamingResponse(stream(),media_type='audio/mpeg',headers={'Cache-Control':'private, no-store','Accept-Ranges':'none'})
