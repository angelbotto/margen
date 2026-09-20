"""Respaldos consistentes e íntegros; restauración sólo en un destino nuevo."""
import argparse
from contextlib import closing
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def status(root,key,value):
    with closing(sqlite3.connect(Path(root)/'bottifact.sqlite3',timeout=30)) as db:
        db.execute('INSERT INTO operation_status VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,json.dumps(value)))
        db.commit()


def verify(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    for name,expected in manifest['files'].items():
        file=(folder/name).resolve()
        if not file.is_relative_to(folder.resolve()) or not file.is_file() or file.is_symlink() or sha(file)!=expected:raise ValueError('Archivo inválido en respaldo: '+name)
    with closing(sqlite3.connect('file:'+str(folder/'bottifact.sqlite3')+'?mode=ro',uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('La base restaurada no pasó la integridad.')
        for (digest,) in db.execute('SELECT DISTINCT sha FROM versions'):
            if not __import__('re').fullmatch('[a-f0-9]{64}',digest) or sha(folder/'files'/(digest+'.html'))!=digest:raise ValueError('Versión incompleta.')
        counts={table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ['artifacts','versions','events','grants']}
    return {'ok':True,'at':int(time.time()),'counts':counts,'files':len(manifest['files'])}


def restore(source,target):
    source=Path(source);target=Path(target)
    verify(source)
    if target.exists():raise ValueError('La restauración requiere un destino nuevo; nunca sobrescribe producción.')
    shutil.copytree(source,target)
    try:return verify(target)
    except BaseException:
        shutil.rmtree(target);raise


def backup(root,destination,config=None):
    root=Path(root);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True,mode=0o700)
    started=time.time();stage=Path(tempfile.mkdtemp(prefix='.pending-',dir=destination));os.chmod(stage,0o700)
    try:
        with closing(sqlite3.connect(root/'bottifact.sqlite3',timeout=30)) as src,closing(sqlite3.connect(stage/'bottifact.sqlite3')) as out:src.backup(out)
        telemetry=root/'telemetry.sqlite3'
        if telemetry.exists():
            with closing(sqlite3.connect(telemetry)) as src,closing(sqlite3.connect(stage/'telemetry.sqlite3')) as out:src.backup(out)
        files=stage/'files';files.mkdir()
        with closing(sqlite3.connect(stage/'bottifact.sqlite3')) as db:
            versions=list(db.execute('SELECT id,sha FROM versions'))
        for vid,digest in versions:
            if not __import__('re').fullmatch('[a-f0-9]{64}',digest):raise ValueError('Digest de versión inválido.')
            target=files/(digest+'.html')
            if not target.exists():shutil.copyfile(root/'files'/(digest+'.html'),target)
            attachments=root/'files'/'attachments'/vid
            if attachments.exists():shutil.copytree(attachments,files/'attachments'/vid)
        if config and Path(config).is_file():shutil.copyfile(config,stage/'config.env');os.chmod(stage/'config.env',0o600)
        manifest={'format':'bottifact-backup/1','created':int(time.time()),'files':{str(f.relative_to(stage)):sha(f) for f in stage.rglob('*') if f.is_file()}}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2));verified=verify(stage)
        final=destination/('snapshot-'+time.strftime('%Y%m%d-%H%M%S')+'-'+os.urandom(3).hex());stage.rename(final)
        status(root,'backup',{'ok':True,'at':int(time.time()),'name':final.name,'detail':str(verified['files'])+' archivos verificados · '+str(round(time.time()-started,1))+' s'})
        # Rehearsal on a separate directory, with full hashes and SQLite integrity.
        with tempfile.TemporaryDirectory(prefix='.restore-',dir=destination) as tmp:
            proof=restore(final,Path(tmp)/'data')
        status(root,'restore',{**proof,'detail':'Restauración aislada: archivos, versiones, comentarios y permisos verificados.'})
        managed=sorted(destination.glob('snapshot-*'),key=lambda p:p.name,reverse=True)
        for old in managed[7:]:
            if old.is_dir() and not old.is_symlink():shutil.rmtree(old)
        return final
    except BaseException:
        if stage.exists():shutil.rmtree(stage)
        status(root,'backup',{'ok':False,'at':int(time.time()),'detail':'Falló el respaldo o su verificación. Revisar operación.'})
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    b=sub.add_parser('create');b.add_argument('--data',default='/data');b.add_argument('--output',default='/backups');b.add_argument('--config')
    b=sub.add_parser('verify');b.add_argument('source')
    b=sub.add_parser('restore');b.add_argument('source');b.add_argument('target')
    a=p.parse_args()
    print(backup(a.data,a.output,a.config) if a.action=='create' else json.dumps(verify(a.source) if a.action=='verify' else restore(a.source,a.target)))
