import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bottifact_updater',ROOT/'scripts/update.py')
updater=importlib.util.module_from_spec(spec);spec.loader.exec_module(updater)

class InstallerTests(unittest.TestCase):
    def setUp(self):
        # Installation fixtures model an independent unsigned server. Signed
        # official releases use real OpenSSL keys in scripts/test_release.py.
        check=patch.object(updater,'ORIGIN','https://fixtures.example.org')
        check.start();self.addCleanup(check.stop)

    def archive(self,version):
        files={'packages/core/registry/registry.json':b'{}','VERSION.json':json.dumps({'version':version}).encode(),'SKILL.md':b'---\nname: bottifact\ndescription: Test\n---\n'}
        for name in ['install.py','verify_package.py']:files['scripts/'+name]=(ROOT/'scripts'/name).read_bytes()
        files['MANIFIESTO.json']=json.dumps({'formato':'bottifact-portable','version':version,'archivos':{k:hashlib.sha256(v).hexdigest() for k,v in files.items()}}).encode()
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            for name,blob in files.items():z.writestr('bottifact/'+name,blob)
        return out.getvalue()

    def test_download_install_update_backup_and_git_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            dest=Path(temporary)/'stable/library'
            for version in ['first','second']:
                data=self.archive(version)
                def fetch(path,limit):return data if path.endswith('.zip') else (hashlib.sha256(data).hexdigest()+'  package.zip').encode()
                with patch.object(updater,'fetch',fetch),patch.object(sys,'argv',['install','--destino',str(dest),'--sin-enlaces']):updater.main()
                self.assertEqual(json.loads((dest/'VERSION.json').read_text())['version'],version)
            backups=list((Path(temporary)/'bottifact-respaldos').glob('library-*'))
            self.assertEqual(len(backups),1);self.assertEqual(json.loads((backups[0]/'VERSION.json').read_text())['version'],'first')
            (dest/'.git').mkdir()
            with patch.object(sys,'argv',['install','--destino',str(dest),'--sin-enlaces']):
                with self.assertRaises(ValueError):updater.main()

    def test_margen_aliases_preserve_legacy_entry_and_custom_installations(self):
        with tempfile.TemporaryDirectory() as temporary:
            home=Path(temporary);dest=home/'library'
            legacy=home/'.agents/skills/bottifact';legacy.parent.mkdir(parents=True);legacy.symlink_to(dest)
            custom=home/'.claude/skills/margen';custom.mkdir(parents=True);(custom/'personal.txt').write_text('keep')
            data=self.archive('margen')
            def fetch(path,limit):return data if path.endswith('.zip') else (hashlib.sha256(data).hexdigest()+'  package.zip').encode()
            with patch.object(updater.Path,'home',return_value=home),patch.object(updater,'fetch',fetch),patch.object(sys,'argv',['install','--destination',str(dest)]):updater.main()
            self.assertEqual((home/'.agents/skills/margen').resolve(),dest.resolve())
            self.assertEqual((home/'.hermes/skills/margen').resolve(),dest.resolve())
            self.assertEqual(legacy.resolve(),(dest/'compat/bottifact').resolve())
            self.assertEqual((custom/'personal.txt').read_text(),'keep')
            self.assertEqual((home/'.local/bin/margen').resolve(),(home/'.local/bin/bottifact').resolve())

    def test_unmanaged_command_does_not_gain_a_margen_alias(self):
        with tempfile.TemporaryDirectory() as temporary:
            home=Path(temporary);binary=home/'.local/bin/bottifact';binary.parent.mkdir(parents=True);binary.write_text('personal command')
            data=self.archive('margen')
            def fetch(path,limit):return data if path.endswith('.zip') else (hashlib.sha256(data).hexdigest()+'  package.zip').encode()
            with patch.object(updater.Path,'home',return_value=home),patch.object(updater,'fetch',fetch),patch.object(sys,'argv',['install','--destination',str(home/'library')]):updater.main()
            self.assertEqual(binary.read_text(),'personal command')
            self.assertFalse((home/'.local/bin/margen').is_symlink())

    def test_corrupt_and_traversal_packages_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            data=self.archive('test')
            with self.assertRaises(ValueError):updater.extract(data,'0'*64,Path(temporary))
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as z:z.writestr('bottifact/../../escape','no')
            data=out.getvalue()
            with self.assertRaises(ValueError):updater.extract(data,hashlib.sha256(data).hexdigest(),Path(temporary))


class ShellEntryTests(unittest.TestCase):
    def test_shell_entry_explains_agents_and_propagates_failure(self):
        import os, subprocess
        script=ROOT/'scripts/install.sh'
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fake=root/'curl'
            fake.write_text('#!/bin/bash\nexit 22\n');fake.chmod(0o755)
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'TMPDIR':str(root)}
            result=subprocess.run(['bash',str(script)],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,22)
            for agent in ['Codex','Claude Code','Hermes','ChatGPT']:self.assertIn(agent,result.stdout)
            self.assertEqual(list(root.glob('bottifact-install.*')),[])

if __name__=='__main__':unittest.main()
