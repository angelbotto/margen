#!/usr/bin/env python3
"""Instala o actualiza Margen para Claude Code, Codex y Hermes. Python 3.10+."""
import argparse
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from urllib.parse import urlsplit

ORIGIN = 'https://artifacts.botto.is'
AGENT_TARGETS = {'codex': ('.agents', 'Codex'), 'claude': ('.claude', 'Claude Code'), 'hermes': ('.hermes', 'Hermes')}


def parse_agents(value):
    if value == 'all': return list(AGENT_TARGETS)
    selected = [part.strip().lower() for part in value.split(',')]
    if not selected or any(part not in AGENT_TARGETS for part in selected):
        raise ValueError('Choose --agents codex,claude,hermes (one or more), or all.')
    return [name for name in AGENT_TARGETS if name in selected]
TRUSTED_RELEASE_KEY = '-----BEGIN PUBLIC KEY-----\nMIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEA3ClxdiyMbuMX4b6GwSRp\n1ZFFlHtRzoSuqCKWYJ8Dv45z3BUvHTtJV/cjxoBOA6dJR8CbkN+bdValTRZCgdQr\n+42Diu/rt4AFzJsF229+NDZLPA3FN43hPV3YApBNqulsJYGKtN/+jJOixMuWhxzz\nqgD1OfJkc9yXdRmt0ZXLGchUR5mprPYQOB6zWcAGswUyEDwZBiHLw9fvZnMYYDqs\n/ensu1QobwCj2CIZaxzI0SVvdWD6DQzejEyLceNMVmNkRymrBKR8JtWC0eSPIDBJ\nQ6wlg3M4NgwkBpB8EBBcA0fmHYGT5XXIHMVv5GJPNo2Si/3LWNJmEz5jayeJRksK\nTU7HF1wit30NQV0cS227jcAquI4bAjsO29mfk1R1h2CEoLoJYEZeSleIXcdh9djR\n0evuv0HGuHwxFQ3SMUHqluzECrCW6HQ+3D/PyACL4D42P4WtHRuU0J69dmVdcNN/\nw2kUrUpVenAT4ea+OXQ94L2xELlGdnqX1Vr71xehGVPDAgMBAAE=\n-----END PUBLIC KEY-----\n'



@contextmanager
def update_lock(path):
    """OS-owned locks are released on crash; never leave a permanent lock file."""
    with path.open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0, 2)
            if not handle.tell():
                handle.write(b'0'); handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise BlockingIOError('Another update is running') from error
            try: yield
            finally:
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try: yield
            finally: fcntl.flock(handle, fcntl.LOCK_UN)


def rsa_public_parameters(pem):
    """Decode an RSA SubjectPublicKeyInfo; signature verification stays in .NET."""
    def tlv(data, offset, tag):
        if offset + 2 > len(data) or data[offset] != tag: raise ValueError('Invalid RSA public key')
        size = data[offset + 1]; start = offset + 2
        if size & 128:
            n = size & 127
            if not 1 <= n <= 4 or start + n > len(data): raise ValueError('Invalid DER length')
            size = int.from_bytes(data[start:start+n], 'big'); start += n
        end = start + size
        if end > len(data): raise ValueError('Truncated RSA public key')
        return data[start:end], end
    if len(pem) > 16384 or not pem.startswith('-----BEGIN PUBLIC KEY-----'): raise ValueError('Expected RSA PUBLIC KEY PEM')
    der = base64.b64decode(''.join(pem.splitlines()[1:-1]), validate=True)
    seq, end = tlv(der, 0, 48)
    if end != len(der): raise ValueError('Trailing public key data')
    algorithm, offset = tlv(seq, 0, 48)
    if algorithm != bytes.fromhex('06092a864886f70d0101010500'): raise ValueError('Expected RSA key')
    bits, end = tlv(seq, offset, 3)
    if end != len(seq) or not bits or bits[0] != 0: raise ValueError('Invalid RSA bit string')
    integers, end = tlv(bits, 1, 48)
    if end != len(bits): raise ValueError('Trailing RSA data')
    modulus, offset = tlv(integers, 0, 2)
    exponent, end = tlv(integers, offset, 2)
    if end != len(integers) or not modulus or not exponent: raise ValueError('Invalid RSA parameters')
    return [base64.b64encode(v.lstrip(b'\0')).decode('ascii') for v in (modulus, exponent)]


def windows_verify(raw, signature, key, root):
    modulus, exponent = rsa_public_parameters(key)
    data = {'modulus':modulus, 'exponent':exponent,
            'data':base64.b64encode(raw).decode(), 'signature':base64.b64encode(signature).decode()}
    path = root/'verification.json'; path.write_text(json.dumps(data), encoding='utf-8')
    # Constant program + environment path, never interpolate paths/keys as code.
    program = """$ErrorActionPreference='Stop'
$v=Get-Content -LiteralPath $env:MARGEN_VERIFY_FILE -Raw | ConvertFrom-Json
$rsa=New-Object System.Security.Cryptography.RSACryptoServiceProvider
try {
$rsa.FromXmlString('<RSAKeyValue><Modulus>'+$v.modulus+'</Modulus><Exponent>'+$v.exponent+'</Exponent></RSAKeyValue>')
if (-not $rsa.VerifyData([Convert]::FromBase64String($v.data),'SHA256',[Convert]::FromBase64String($v.signature))) { exit 1 }
} finally { $rsa.Dispose() }
"""
    encoded = base64.b64encode(program.encode('utf-16le')).decode('ascii')
    return subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
        env={**os.environ,'MARGEN_VERIFY_FILE':str(path)}, capture_output=True)

def verify_release(raw, signature, key, expected, channel):
    with tempfile.TemporaryDirectory(prefix='margen-signature-') as folder:
        root=Path(folder)
        for name,data in [('manifest',raw),('signature',signature),('key',key.encode())]: (root/name).write_bytes(data)
        check = windows_verify(raw, signature, key, root) if os.name == 'nt' else subprocess.run(['openssl','dgst','-sha256','-verify',str(root/'key'),'-signature',str(root/'signature'),str(root/'manifest')],capture_output=True)
        if check.returncode:raise ValueError('Release signature is invalid; installation was not changed.')
    manifest=json.loads(raw)
    if manifest.get('schema')!=1 or manifest.get('channel')!=channel or manifest.get('sha256')!=expected or manifest.get('package')!=('bottifact-preview.zip' if channel=='preview' else 'bottifact-portable.zip'):raise ValueError('Release manifest does not match the selected download.')
    if manifest.get('compatibility',{}).get('skill_contract',0)>4:raise ValueError('This release needs a newer installer; review the upgrade guide.')
    return manifest



def fetch(path, limit):
    req = urllib.request.Request(ORIGIN + path, headers={'User-Agent': 'Margen/1.0'})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs): return None
    with urllib.request.build_opener(NoRedirect).open(req, timeout=60) as response:
        data = response.read(limit + 1)
    if len(data) > limit: raise ValueError('La descarga supera el tamaño esperado.')
    return data


def extract(data, expected, destination):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('La descarga no coincide con SHA-256. No se ha cambiado la instalación. Intenta de nuevo.')
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(i.file_size for i in archive.infolist()) > 200 * 1024 * 1024: raise ValueError('Paquete demasiado grande.')
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'bottifact' or '\\' in item.filename or any(':' in part or part.endswith((' ','.')) or part.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for part in path.parts) or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Ruta no permitida en el paquete.')
        archive.extractall(destination)


def main():
    os.environ.setdefault('PYTHONUTF8', '1')
    if sys.version_info < (3, 10): raise ValueError('Margen requires Python 3.10+. Install it from python.org, then retry.')
    parser = argparse.ArgumentParser(description=__doc__)
    global ORIGIN
    parser.add_argument('--if-changed',action='store_true',help='Comprobar checksum y actualizar sólo cuando cambie el paquete.')
    parser.add_argument('--channel',choices=['stable','preview'],help='Signed release channel; defaults to the saved channel or stable.')
    parser.add_argument('--trusted-key',type=Path,help='Public RSA key pinned out of band for a self-hosted release.')
    parser.add_argument('--check',action='store_true',help='Consultar si hay una actualización sin instalarla.')
    parser.add_argument('--auto',choices=['enable','disable','status'],help='Actualizaciones periódicas por usuario; habilitación explícita.')
    parser.add_argument('--server','--servidor',dest='servidor', help='Portal propio HTTPS; se conserva para futuras actualizaciones.')
    parser.add_argument('--package','--paquete',dest='paquete', type=Path, help='ZIP local; no usa ningún servidor. Requiere archivo .sha256 contiguo.')
    parser.add_argument('--destination','--destino',dest='destino', type=Path, default=Path.home()/'.local/share/bottifact/library')
    parser.add_argument('--no-links','--sin-enlaces',dest='sin_enlaces', action='store_true', help='Actualiza solo la biblioteca; no modifica carpetas de agentes ni instala el comando.')
    parser.add_argument('--agents', help='Install for codex,claude,hermes or all. Omit to keep the saved selection; first installation defaults to all.')
    args = parser.parse_args()
    destination = args.destino.expanduser().absolute()
    if (destination/'.git').exists(): raise ValueError('El destino es un checkout Git. Conserva ese desarrollo y elige otra carpeta con --destino.')
    setting=destination.parent/('.'+destination.name+'-update.json')
    saved=json.loads(setting.read_text(encoding='utf-8')) if setting.exists() else {}
    if args.agents is not None and args.sin_enlaces: raise ValueError('--agents cannot be combined with --no-links.')
    agents = parse_agents(args.agents if args.agents is not None else ','.join(saved.get('agents', list(AGENT_TARGETS))))
    if args.servidor:
        parsed=urlsplit(args.servidor)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:raise ValueError('Usa un servidor HTTPS sin ruta ni credenciales.')
        ORIGIN=args.servidor.rstrip('/')
    elif saved.get('servidor'):ORIGIN=saved['servidor']
    elif saved.get('local') and not args.paquete and not args.auto:raise ValueError('Instalación local: usa --paquete ZIP para actualizar, o --servidor HTTPS para conectar un servidor.')
    channel=args.channel or saved.get('channel','stable')
    trusted_key=args.trusted_key.read_text(encoding='utf-8') if args.trusted_key else saved.get('trusted_key')
    if args.auto:
        if args.servidor or args.paquete:raise ValueError('Primero actualiza desde el servidor o paquete elegido; después configura --auto en un comando separado.')
        if args.auto=='enable' and saved.get('local'):raise ValueError('Una instalación local necesita actualizar desde --server HTTPS antes de programar descargas.')
        if args.auto=='enable' and not (destination/'scripts/update.py').exists():raise ValueError('Instala primero la biblioteca en el destino elegido.')
        from automatic_updates import configure
        print(json.dumps(configure(args.auto,destination),ensure_ascii=False));return
    # One update process per destination; the lock is outside the directory being replaced.
    destination.parent.mkdir(parents=True,exist_ok=True)
    with update_lock(destination.parent/('.'+destination.name+'-update.lock')):
        with tempfile.TemporaryDirectory(prefix='bottifact-download-') as temporary:
            root = Path(temporary)
            package_name='bottifact-preview' if channel=='preview' else 'bottifact-portable'
            expected = (args.paquete.with_suffix('.sha256').read_text(encoding='utf-8') if args.paquete else fetch('/downloads/'+package_name+'.sha256', 1024).decode()).split()[0]
            if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected): raise ValueError('SHA-256 inválido.')
            manifest=None
            if not args.paquete and (urlsplit(ORIGIN).hostname=='artifacts.botto.is' or trusted_key):
                raw=fetch('/downloads/'+channel+'.json',32768);signature=fetch('/downloads/'+channel+'.json.sig',4096)
                manifest=verify_release(raw,signature,trusted_key or TRUSTED_RELEASE_KEY,expected,channel)
                installed=json.loads((destination/'VERSION.json').read_text(encoding='utf-8')) if (destination/'VERSION.json').exists() else {}
                if installed.get('release_sequence',0)>manifest.get('sequence',0):raise ValueError('Release sequence is older than the installed release. Use a reviewed local package for intentional rollback.')
                if manifest and installed.get('version','')[:10]>manifest['version'][:10]:raise ValueError('Release is older than the installed version. Use a reviewed local package for an intentional rollback.')
            elif not args.paquete:
                print('Self-hosted checksum verification. Pin --trusted-key to require signed releases.')
            if args.check:
                print(json.dumps({'installed':(destination/'VERSION.json').exists(),'update_available':saved.get('sha256')!=expected,'server':ORIGIN if not args.paquete else None},ensure_ascii=False));return
            if args.if_changed and saved.get('sha256')==expected and agents==saved.get('agents', list(AGENT_TARGETS)) and (destination/'VERSION.json').exists():
                print('Margen ya está actualizado.');return
            extract(args.paquete.read_bytes() if args.paquete else fetch('/downloads/'+package_name+'.zip', 50*1024*1024), expected, root)
            source = root/'bottifact'
            if manifest and json.loads((source/'VERSION.json').read_text(encoding='utf-8')).get('release_sequence',0)!=manifest.get('sequence',0):raise ValueError('Package sequence differs from signed manifest.')
            if manifest and json.loads((source/'VERSION.json').read_text(encoding='utf-8'))['version']!=manifest['version']:raise ValueError('Package version differs from signed manifest.')
            subprocess.run([sys.executable, str(source/'scripts/install.py'), '--destino', str(destination), '--actualizar'], check=True)
        if not args.sin_enlaces and os.name == 'nt':
            sys.path.insert(0,str(destination/'scripts'))
            from windows_install import integrate
            integrate(destination, agents=agents)
        elif not args.sin_enlaces:
            for agent,label in [AGENT_TARGETS[name] for name in agents]:
                link = Path.home()/agent/'skills/margen'
                link.parent.mkdir(parents=True, exist_ok=True)
                if link.exists() and not link.is_symlink():
                    print('Conservado sin cambios (carpeta propia): ' + str(link));continue
                if link.is_symlink() and link.resolve() == destination.resolve():
                    print(label + ': listo · ' + str(link));continue
                if link.is_symlink():
                    print('Conservado sin cambios (apunta a otra biblioteca): ' + str(link));continue
                link.symlink_to(destination, target_is_directory=True)
                print(label + ': instalado · ' + str(link))
            # Keep the old skill name as an explicit compatibility entry, not a second canonical skill.
            for agent in [AGENT_TARGETS[name][0] for name in agents]:
                legacy=Path.home()/agent/'skills/bottifact'
                alias=destination/'compat/bottifact'
                if legacy.is_symlink() and legacy.resolve()==destination.resolve():
                    legacy.unlink();legacy.symlink_to(alias,target_is_directory=True)
                elif not legacy.exists() and not legacy.is_symlink():
                    legacy.symlink_to(alias,target_is_directory=True)
            binary = Path.home()/'.local/bin/bottifact'
            binary.parent.mkdir(parents=True, exist_ok=True)
            if binary.exists() and not any(marker in binary.read_text(encoding='utf-8') for marker in ['# Bottifact managed launcher','# Margen managed launcher']):
                print('Conservado comando existente: ' + str(binary))
            else:
                text = '#!' + sys.executable + '\n# Margen managed launcher\nimport os,sys\nfrom pathlib import Path\nroot=Path(' + repr(str(destination)) + ')\nargs=sys.argv[1:]\nscript="update.py" if args and args[0] in ("update","install","actualizar","instalar") else "publish.py"\nif script=="update.py":args=args[1:]+["--destino",str(root)]\nos.execv(sys.executable,[sys.executable,str(root/"scripts"/script),*args])\n'
                stage = binary.with_name('.bottifact-new')
                stage.write_text(text);stage.chmod(0o755);stage.replace(binary)
                print('Comando: ' + str(binary) + ' (añade ~/.local/bin a PATH si hace falta).')
                agent_binary=Path.home()/'.local/bin/margen-agent'
                if not agent_binary.exists() or '# Margen managed launcher' in agent_binary.read_text(encoding='utf-8'):
                    agent_binary.write_text('#!'+sys.executable+'\n# Margen managed launcher\nimport runpy\nrunpy.run_path('+repr(str(destination/'scripts/agent_connector.py'))+',run_name="__main__")\n');agent_binary.chmod(0o755)
                margen_binary=Path.home()/'.local/bin/margen'
                if not margen_binary.exists() and not margen_binary.is_symlink():
                    margen_binary.symlink_to(binary)
                elif margen_binary.is_symlink() and margen_binary.resolve()==binary.resolve():
                    pass
                else:
                    print('Preserved existing command: '+str(margen_binary))
        setting.write_text(json.dumps({'local':bool(args.paquete) and not args.servidor,'servidor':ORIGIN if not args.paquete or args.servidor else None,'sha256':expected,'channel':channel,'trusted_key':trusted_key,'agents':agents})+'\n',encoding='utf-8')
        version = json.loads((destination/'VERSION.json').read_text(encoding='utf-8'))['version']
        print('Margen ' + version + '. Generar HTML no requiere cuenta ni token.')
        print('Instalación personal en: ' + str(Path.home()))
        print('Agentes seleccionados: ' + ', '.join(AGENT_TARGETS[name][1] for name in agents))
        print('La biblioteca se comparte entre tus agentes, no entre cuentas de personas distintas.')
        print('Comprueba tu cuenta con margen status. Una conexión anterior requiere margen confirm-account --email TU_CORREO antes de publicar.')
        if not args.paquete or args.servidor:print('Para publicar: entra en ' + ORIGIN + ' → Conectar un agente. Nunca pegues el token en un artefacto.')
        else:print('Instalación local independiente. Conecta tu propio portal solo cuando quieras publicar.')
        print('Actualizar después: python3 ' + str(destination/'scripts/update.py'))


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        sys.exit('No se completó la instalación: ' + str(error))
