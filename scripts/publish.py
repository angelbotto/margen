#!/usr/bin/env python3
"""Publica HTML y recupera comentarios del portal Margen con una conexión personal."""
import argparse
import getpass
import socket
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from .private_storage import read_json as read_private_json, write_json as private_json
except ImportError:
    from private_storage import read_json as read_private_json, write_json as private_json

CONFIG=Path.home()/'.config/bottifact/portal.json'

def checked_identity(user, email):
    """Match an explicitly chosen account against the server-verified identity."""
    email=(email or '').strip().lower()
    if not email or not user or not user.get('verified'):
        raise SystemExit('Indica tu propio correo con --email y utiliza una cuenta verificada.')
    known={str(v).lower() for v in user.get('emails', []) if v}
    known.add(str(user.get('email','')).lower())
    if email not in known:
        raise SystemExit('El token pertenece a '+str(user.get('email'))+', no a '+email+'. Entra al portal con tu cuenta y crea tu propia conexión. No se cambió la configuración.')
    return {'id':user['id'],'email':user['email']}

def check_account(config, user, require=False):
    saved=config.get('account')
    if saved and (not user or saved.get('id')!=user.get('id')):
        raise SystemExit('La conexión ya no corresponde a la cuenta confirmada. Ejecuta margen connect con tu propio --email antes de continuar.')
    if require and not saved:
        raise SystemExit('Confirma primero a quién pertenece esta conexión: margen confirm-account --email TU_CORREO. No uses el correo de otra persona ni lo deduzcas del token.')

def request(base, token, path, data=None, method=None):
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':'Margen/1.0'},method=method)
    # No enviar la conexión a otro destino mediante una redirección.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=60) as response:return json.load(response)
    except urllib.error.HTTPError as e:
        try:message=json.load(e).get('detail','Error del portal')
        except (ValueError,AttributeError):message='Error del portal'
        raise SystemExit(str(e.code)+': '+str(message)) from None
    except urllib.error.URLError:raise SystemExit('No se pudo conectar al portal. Revisa la dirección y la red.') from None

def source_defaults(agent, session):
    known={name:os.environ.get(key,'') for name,key in [('Codex','CODEX_THREAD_ID'),('Claude','CLAUDE_SESSION_ID'),('Hermes','HERMES_SESSION_ID')]}
    agent=agent or os.environ.get('BOTTIFACT_AGENT','')
    active=[name for name,value in known.items() if value]
    if not agent and len(active)==1:agent=active[0]
    session=session or os.environ.get('BOTTIFACT_SESSION','') or next((value for name,value in known.items() if name.casefold()==agent.casefold()),'')
    return agent,session

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=CONFIG)
    sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('conectar',aliases=['connect']);c.add_argument('--server','--servidor',dest='servidor',required=True);c.add_argument('--token-file','--token-archivo',dest='token_archivo',type=Path);c.add_argument('--email',help='Your own verified account email, never copied from someone else’s token.')
    c=sub.add_parser('confirm-account',help='Confirm the owner of an existing personal connection without revealing its token.');c.add_argument('--email',required=True)
    c=sub.add_parser('publicar',aliases=['publish']);c.add_argument('--file','--archivo',dest='archivo',type=Path,required=True);c.add_argument('--title','--titulo',dest='titulo',required=True);c.add_argument('--space','--espacio',dest='espacio',default='Personal');c.add_argument('--artifact-id','--artefacto-id',dest='artefacto_id');c.add_argument('--visibility','--visibilidad',dest='visibilidad',choices=['private','unlisted','public']);c.add_argument('--mode','--modo',dest='modo',choices=['draft','published']);c.add_argument('--agent','--agente',dest='agente',default='');c.add_argument('--session','--sesion',dest='sesion',default='');c.add_argument('--device','--dispositivo',dest='dispositivo',default='');c.add_argument('--new','--nuevo',dest='nuevo',action='store_true',help='Crear otro enlace aun si el documento ya fue publicado desde este equipo.')
    c=sub.add_parser('comentarios',aliases=['comments']);c.add_argument('--artifact-id','--artefacto-id',dest='artefacto_id');c.add_argument('--open','--abiertos',dest='abiertos',action='store_true');c.add_argument('--kind','--tipo',dest='tipo',choices=['all','comment','note'],default='all');c.add_argument('--output','--salida',dest='salida',type=Path)
    sub.add_parser('estado',aliases=['status']);c=sub.add_parser('listar',aliases=['list']);c.add_argument('--search','--buscar',dest='buscar',default='')
    c=sub.add_parser('preferencias',aliases=['preferences']);c.add_argument('--publish-on-create','--publicar-al-crear',dest='publicar_al_crear',choices=['yes','si','no'],required=True)
    c=sub.add_parser('renombrar',aliases=['rename']);c.add_argument('--artifact-id','--artefacto-id',dest='artefacto_id',required=True);c.add_argument('--title','--titulo',dest='titulo',required=True);c.add_argument('--space','--espacio',dest='espacio',required=True)
    c=sub.add_parser('versiones',aliases=['versions']);c.add_argument('--artifact-id','--artefacto-id',dest='artefacto_id',required=True)
    c=sub.add_parser('comparar',aliases=['compare']);c.add_argument('--artifact-id','--artefacto-id',dest='artefacto_id',required=True);c.add_argument('--from','--desde',dest='desde',required=True);c.add_argument('--to','--hasta',dest='hasta',required=True)
    c=sub.add_parser('liberar',aliases=['release']);c.add_argument('--artifact-id','--artefacto-id',dest='artefacto_id',required=True);c.add_argument('--version',required=True);c.add_argument('--expected-current','--actual-esperada',dest='actual_esperada',required=True)
    c=sub.add_parser('feedback',help='Prepare a private feedback bundle for an existing session.');c.add_argument('--artifact-id',required=True);c.add_argument('--output',type=Path,required=True);c.add_argument('--agent',default='');c.add_argument('--session',default='');c.add_argument('--kind',choices=['all','comment','note'],default='all')
    c=sub.add_parser('continuity',help='Read a cited project brief; excludes private notes.');c.add_argument('--space',default='');c.add_argument('--output',type=Path)
    c=sub.add_parser('share',help='Grant verified domains access to an artifact. Requires explicit sharing authorization.');c.add_argument('--artifact-id',required=True);c.add_argument('--domain',action='append',default=[]);c.add_argument('--remove-domain',action='append',default=[]);c.add_argument('--role',choices=['viewer','commenter'],default='commenter');c.add_argument('--visibility',choices=['private','invited'])
    args=p.parse_args()
    args.command={'connect': 'conectar', 'publish': 'publicar', 'comments': 'comentarios', 'status': 'estado', 'list': 'listar', 'preferences': 'preferencias', 'rename': 'renombrar', 'versions': 'versiones', 'compare': 'comparar', 'release': 'liberar'}.get(args.command,args.command)
    if args.command=='conectar':
        base=args.servidor.rstrip('/');url=urllib.parse.urlparse(base)
        if url.scheme!='https' or not url.netloc or url.path or url.query or url.fragment or url.username:raise SystemExit('Usa el origen HTTPS del portal, sin rutas ni credenciales.')
        email=args.email
        if not email and sys.stdin.isatty():email=input('Tu correo de Margen: ').strip()
        if not email:raise SystemExit('Indica tu propio correo con --email. Cada persona necesita su conexión; el instalador no comparte cuentas.')
        token=args.token_archivo.read_text().strip() if args.token_archivo else getpass.getpass('Token personal (oculto): ')
        user=request(base,token,'/api/session')['user']
        identity=checked_identity(user,email)
        old=read_private_json(args.config, allow_plain=True) if args.config.exists() else {}
        same_account=old.get('server')==base and (old.get('account',{}).get('id')==identity['id'] or old.get('token')==token)
        private_json(args.config,{'server':base,'token':token,'account':identity,'publish_on_create':bool(old.get('publish_on_create')) if same_account else False})
        print('Conexión guardada para '+user['email']+'. No se incluye en el skill ni en los artefactos.');return
    if not args.config.exists():raise SystemExit('Primero conecta tu cuenta con: publicar.py conectar --servidor https://artifacts.example.com')
    if os.name != 'nt' and args.config.stat().st_mode&0o077:raise SystemExit('La conexión debe ser privada: chmod 600 '+str(args.config))
    config=read_private_json(args.config);base=config['server'];token=config['token']
    if args.command=='confirm-account':
        user=request(base,token,'/api/session')['user']
        identity=checked_identity(user,args.email)
        check_account(config,user)
        config['account']=identity;private_json(args.config,config)
        print('Cuenta confirmada: '+identity['email']+'. Esta conexión es personal; no la compartas.');return
    writes={'publicar','share','renombrar','liberar','preferencias'}
    if args.command in writes:
        user=request(base,token,'/api/session')['user']
        check_account(config,user,require=True)
    if args.command=='preferencias':
        config['publish_on_create']=args.publicar_al_crear in ('yes','si');private_json(args.config,config)
        print('Publicar artefactos nuevos como privados al terminar: '+('sí' if config['publish_on_create'] else 'no'));return
    if args.command=='share':
        if not re.fullmatch('[a-f0-9]{32}',args.artifact_id):raise SystemExit('Invalid artifact ID.')
        if not (args.domain or args.remove_domain or args.visibility):raise SystemExit('Choose --domain, --remove-domain or --visibility.')
        if args.visibility=='private' and args.domain:raise SystemExit('Private access cannot include a domain.')
        # The portable CLI intentionally has no portal runtime dependency.
        def domain(value):
            value=value.strip().lower().removeprefix('@')
            if len(value)>253 or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?',value):raise SystemExit('Use an exact email domain without URLs or wildcards.')
            return value
        added=[domain(d) for d in args.domain];removed=[domain(d) for d in args.remove_domain]
        if set(added)&set(removed):raise SystemExit('Do not add and remove the same domain.')
        path='/api/artifacts/'+args.artifact_id
        current=request(base,token,path)
        if not current.get('permissions',{}).get('manage'):raise SystemExit('Only the owner or portal administrator can change access.')
        if 'domain_grants' not in current:raise SystemExit('This server does not support domain sharing yet. Update the portal first.')
        domains={g['domain']:g['role'] for g in current['domain_grants']}
        for d in removed:domains.pop(d,None)
        for d in added:domains[d]=args.role
        visibility=args.visibility or ('invited' if added and current['visibility']=='private' else current['visibility'])
        body={'visibility':visibility,'comments':current['comments'],'guests':bool(current['guests']),'grants':current['grants'],'domain_grants':[{'domain':d,'role':r} for d,r in sorted(domains.items())]}
        if current.get('access_revision'):body['expected_access']=current['access_revision']
        request(base,token,path+'/access',body,method='PUT')
        saved=request(base,token,path)
        print(json.dumps({'url':base+'/a/'+args.artifact_id,'visibility':saved['visibility'],'domain_grants':saved['domain_grants'],'notice':'Existing personal grants are preserved unless private visibility is selected. No invitation email is sent.'},ensure_ascii=False,indent=2));return
    if args.command=='publicar':
        args.agente,args.sesion=source_defaults(args.agente,args.sesion)
        if args.archivo.stat().st_size>20*1024*1024:raise SystemExit('El HTML supera 20 MB.')
        content=args.archivo.read_text();match=re.search(r'<meta\s+name=[\"\']nota-documento[\"\']\s+content=[\"\']([a-zA-Z0-9_-]{1,120})[\"\']',content)
        if not match:raise SystemExit('Genera el HTML con un documento-id estable antes de publicar.')
        receipt_file=args.config.parent/'publications.json'
        receipts=json.loads(receipt_file.read_text()) if receipt_file.exists() else {}
        key=base+'|'+user['id']+'|'+match[1]
        aid=args.artefacto_id or (None if args.nuevo else receipts.get(key,{}).get('id'))
        if args.nuevo and args.artefacto_id:raise SystemExit('--nuevo y --artefacto-id no se pueden combinar.')
        if not aid and not args.nuevo:
            existing=request(base,token,'/api/artifacts?'+urllib.parse.urlencode({'document_id':match[1]}))['artifacts']
            own=[a for a in existing if a.get('owner')==user['id'] and a.get('document_id')==match[1]]
            if len(own)>1:raise SystemExit('Hay varios artefactos con ese documento-id. Elige --artefacto-id para conservar el enlace correcto.')
            if own:aid=own[0]['id']
        if aid and (len(aid)!=32 or any(x not in '0123456789abcdef' for x in aid)):raise SystemExit('ID de artefacto inválido.')
        if aid and args.visibilidad:raise SystemExit('Las revisiones conservan permisos; usa Compartir en el portal para cambiarlos.')
        body={'title':args.titulo,'space':args.espacio,'html':content,'mode':args.modo or ('draft' if aid else 'published'),'source':{'agent':args.agente,'session':args.sesion,'device':args.dispositivo or os.environ.get('BOTTIFACT_DEVICE','') or socket.gethostname()}}
        attachments=args.archivo.with_suffix('.attachments.json')
        if attachments.is_file():body['attachments']=json.loads(attachments.read_text())
        if args.visibilidad:body['visibility']=args.visibilidad
        result=request(base,token,'/api/artifacts'+('/'+aid+'/versions' if aid else ''),body)
        receipts[key]={**result,'document_id':match[1],'saved_at':int(time.time())};private_json(receipt_file,receipts)
        result['operation']='revision' if aid else 'created'
        result['account']={'id':user['id'],'email':user.get('email')}
    elif args.command in ('versiones','comparar','liberar'):
        if not re.fullmatch('[a-f0-9]{32}',args.artefacto_id):raise SystemExit('ID de artefacto inválido.')
        path='/api/artifacts/'+args.artefacto_id
        if args.command=='versiones':result=request(base,token,path)
        elif args.command=='comparar':result=request(base,token,path+'/compare?'+urllib.parse.urlencode({'from':args.desde,'to':args.hasta}))
        else:result=request(base,token,path+'/release',{'version':args.version,'expected_current':args.actual_esperada})
    elif args.command=='renombrar':
        if not re.fullmatch('[a-f0-9]{32}',args.artefacto_id):raise SystemExit('ID de artefacto inválido.')
        result=request(base,token,'/api/artifacts/'+args.artefacto_id,{'title':args.titulo,'space':args.espacio},method='PATCH')
    elif args.command=='continuity':
        text=request(base,token,'/api/creator/brief?'+urllib.parse.urlencode({'project':args.space}))['text']
        if args.output:
            fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
            with os.fdopen(fd,'w') as out:out.write(text+'\n')
            args.output.chmod(0o600);print(args.output)
        else:print(text)
        return
    elif args.command=='feedback':
        if not re.fullmatch('[a-f0-9]{32}',args.artifact_id):raise SystemExit('Invalid artifact ID.')
        try:
            from .feedback import write_handoff
        except ImportError:
            from feedback import write_handoff
        response=request(base,token,'/api/review/export?'+urllib.parse.urlencode({'artifact':args.artifact_id,'scope':'open','kind':args.kind}))
        try:result=write_handoff(response,args.output,args.agent,args.session)
        except (ValueError,OSError) as error:raise SystemExit(str(error)) from None
    elif args.command=='comentarios':
        params={'scope':'open' if args.abiertos else 'all','kind':args.tipo}
        if args.artefacto_id:params['artifact']=args.artefacto_id
        text=request(base,token,'/api/review/export?'+urllib.parse.urlencode(params))['text']
        if args.salida:args.salida.write_text(text+'\n');print(str(args.salida))
        else:print(text)
        return
    else:
        result=request(base,token,'/api/session' if args.command=='estado' else '/api/artifacts?'+urllib.parse.urlencode({'q':args.buscar}))
        if args.command=='estado':
            check_account(config,result.get('user'))
            result['account_confirmed']=bool(config.get('account'));result['publish_on_create']=bool(config.get('publish_on_create'));result['server']=base
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
