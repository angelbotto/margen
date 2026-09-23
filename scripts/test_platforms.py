"""Native smoke checks run unchanged on Windows, macOS and Linux CI runners."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import update
from package import package
from private_storage import write_json, read_json
from windows_install import managed_copy
from automatic_updates import configure

ROOT = Path(__file__).resolve().parents[1]


class PlatformTests(unittest.TestCase):
    def test_signature_authentication_without_openssl_on_windows(self):
        fixture = json.loads((ROOT/'tests/fixtures/release-signature.json').read_text(encoding='utf-8'))
        raw=fixture['manifest'].encode(); signature=base64.b64decode(fixture['signature'])
        self.assertEqual(update.verify_release(raw,signature,fixture['public_key'],fixture['sha256'],'stable')['schema'],1)
        for data,sig in [(raw+b' ',signature),(raw,b'X'+signature[1:])]:
            with self.assertRaises(ValueError): update.verify_release(data,sig,fixture['public_key'],fixture['sha256'],'stable')
        for digest,channel in [('0'*64,'stable'),(fixture['sha256'],'preview')]:
            with self.assertRaises(ValueError): update.verify_release(raw,signature,fixture['public_key'],digest,channel)

    def test_private_credentials_and_unicode(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'private/portal.json';value={'token':'synthetic-not-a-real-token','email':'test@example.org','name':'Ángel'}
            write_json(path,value);self.assertEqual(read_json(path),value)
            if os.name=='nt':
                self.assertNotIn(value['token'],path.read_text(encoding='utf-8'))
                path.write_text(json.dumps(value),encoding='utf-8')
                with self.assertRaises(ValueError):read_json(path)
            else:self.assertEqual(path.stat().st_mode & 0o077,0)

    def test_process_lock_released_after_exit(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'lock'
            code='import sys;sys.path.insert(0,sys.argv[1]);from pathlib import Path;from update import update_lock;\nwith update_lock(Path(sys.argv[2])): pass'
            with update.update_lock(path):
                blocked=subprocess.run([sys.executable,'-c',code,str(ROOT/'scripts'),str(path)],capture_output=True)
                self.assertNotEqual(blocked.returncode,0)
            self.assertEqual(subprocess.run([sys.executable,'-c',code,str(ROOT/'scripts'),str(path)],capture_output=True).returncode,0)

    def test_managed_copies_preserve_independent_folders_and_back_up_edits(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'library';source.mkdir();(source/'SKILL.md').write_text('one')
            target=root/'agent/skills/margen';managed_copy(source,target)
            (target/'personal.txt').write_text('keep in backup')
            (source/'SKILL.md').write_text('two');managed_copy(source,target)
            self.assertEqual((target/'SKILL.md').read_text(),'two')
            self.assertTrue(list((root/'agent/bottifact-respaldos').glob('*/personal.txt')))
            independent=root/'custom';independent.mkdir();(independent/'SKILL.md').write_text('mine')
            managed_copy(source,independent);self.assertEqual((independent/'SKILL.md').read_text(),'mine')

    def test_install_update_and_native_launcher(self):
        archive=package()
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)/'Ángel with spaces';home.mkdir()
            dest=home/'.local/share/bottifact/library'
            with patch.object(Path,'home',return_value=home),patch.object(sys,'argv',['update.py','--package',str(archive),'--destination',str(dest)]):
                update.main()
                update.main()
            for agent in ('.agents','.claude','.hermes'):
                self.assertTrue((home/agent/'skills/margen/SKILL.md').exists())
            command=home/'.local/bin'/('margen.cmd' if os.name=='nt' else 'margen')
            result=subprocess.run([str(command),'--help'],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(command),'update','--package',str(archive),'--no-links'],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stderr)
            content=home/'source.html';content.write_text('<h1>Guía de equipo · información</h1>',encoding='utf-8')
            output=home/'report.html'
            for args in [['create_artifact.py','--content',str(content),'--title','Guía','--output',str(output)],['validate_artifact.py',str(output)]]:
                result=subprocess.run([sys.executable,'-X','utf8',str(dest/'scripts'/args[0]),*args[1:]],capture_output=True,text=True,encoding='utf-8')
                self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('información',output.read_text(encoding='utf-8'))

    def test_windows_scheduler_uses_current_user_and_argument_quoting(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def run(args,**kwargs):
                calls.append(args)
                return subprocess.CompletedProcess(args,0,'S-1-5-21-1000' if args[0]=='powershell.exe' else '','')
            result=configure('enable',Path(d)/'folder with spaces',Path(d),'win32',run)
            import xml.etree.ElementTree as ET
            tree=ET.parse(result['definition']);ns={'t':'http://schemas.microsoft.com/windows/2004/02/mit/task'}
            self.assertEqual(tree.find('.//t:LogonType',ns).text,'InteractiveToken')
            self.assertEqual(tree.find('.//t:RunLevel',ns).text,'LeastPrivilege')
            self.assertIn('--if-changed',tree.find('.//t:Arguments',ns).text)
            self.assertTrue(any('/Create' in c for c in calls))

    @unittest.skipUnless(os.name=='nt','Native Windows PowerShell syntax check')
    def test_powershell_entrypoint_parses(self):
        program='$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile($env:MARGEN_PS_TEST,[ref]$tokens,[ref]$errors) | Out-Null; if($errors.Count){ $errors | Out-String | Write-Error; exit 1 }'
        result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',program],env={**os.environ,'MARGEN_PS_TEST':str(ROOT/'scripts/install.ps1')},capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__': unittest.main()
