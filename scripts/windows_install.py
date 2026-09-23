"""Native Windows integration without administrator rights or symlink privileges."""
import json
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

MARKER = '.margen-managed.json'


def managed_copy(source, target):
    source, target = Path(source).resolve(), Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        print(('Ready: ' if target.resolve() == source else 'Preserved independent link: ') + str(target))
        return
    marker = target/MARKER
    if target.exists():
        try: owned = json.loads(marker.read_text(encoding='utf-8')).get('source') == str(source)
        except (OSError, ValueError): owned = False
        if not owned:
            print('Preserved independent skill: ' + str(target)); return
    stage = Path(tempfile.mkdtemp(prefix='.margen-', dir=target.parent))
    backup = None
    try:
        shutil.copytree(source, stage, dirs_exist_ok=True)
        (stage/MARKER).write_text(json.dumps({'source':str(source)}), encoding='utf-8')
        if target.exists():
            backups = target.parent.parent/'bottifact-respaldos'; backups.mkdir(exist_ok=True)
            backup = backups/(target.name+'-'+uuid.uuid4().hex)
            target.rename(backup)
        try: stage.rename(target)
        except BaseException:
            if backup: backup.rename(target)
            raise
    finally:
        if stage.exists(): shutil.rmtree(stage)
    print('Managed skill: ' + str(target))


def integrate(destination, home=None, agents=('codex','claude','hermes')):
    home = Path(home or Path.home()); destination = Path(destination).resolve()
    targets = {'codex':'.agents', 'claude':'.claude', 'hermes':'.hermes'}
    for agent in (targets[name] for name in agents):
        managed_copy(destination, home/agent/'skills/margen')
        managed_copy(destination/'compat/bottifact', home/agent/'skills/bottifact')
    binary = home/'.local/bin'; binary.mkdir(parents=True, exist_ok=True)
    for name, connector in [('margen',False),('bottifact',False),('margen-agent',True)]:
        launcher = binary/(name+'-launcher.py')
        cmd = binary/(name+'.cmd')
        marker = '# Margen managed launcher'
        if any(p.exists() and 'Margen managed launcher' not in p.read_text(encoding='utf-8') for p in (cmd,launcher)):
            print('Preserved existing command: '+str(cmd)); continue
        code = marker+'\nimport subprocess,sys\nfrom pathlib import Path\nroot=Path('+repr(str(destination))+')\nargs=sys.argv[1:]\n'
        code += 'script="agent_connector.py"\n' if connector else 'script="update.py" if args and args[0] in ("update","install","actualizar","instalar") else "publish.py"\nif script=="update.py": args=args[1:]+["--destination",str(root)]\n'
        code += 'raise SystemExit(subprocess.call([sys.executable,"-X","utf8",str(root/"scripts"/script),*args]))\n'
        launcher.write_text(code,encoding='utf-8')
        # Paths are quoted and percent expansion is escaped for cmd.exe.
        command = ('@echo off\nrem Margen managed launcher\nsetlocal DisableDelayedExpansion\n'
                   'for /f "tokens=2 delims=: " %%a in (\'chcp\') do set "_margen_cp=%%a"\n'
                   'chcp 65001 >nul\n"'+sys.executable.replace('%','%%')+'" -X utf8 "'+str(launcher).replace('%','%%')+'" %*\n'
                   'set "_margen_exit=%errorlevel%"\nchcp %_margen_cp% >nul\nexit /b %_margen_exit%\n')
        cmd.write_text(command,encoding='utf-8')
    print('Commands: '+str(binary)+' (PowerShell/CMD; add this directory to your user PATH).')
