"""Self-hosting contracts: no implicit dependency on the maintainer's instance."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from portal.app import create_app
from portal.auth import send_code
from portal.settings import validate_origin
import portal.test_installer as installer_fixtures
updater=installer_fixtures.updater
from scripts.configure_portal import configure


class SelfHostTests(unittest.TestCase):
    def test_configuration_is_private_unique_and_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            first=Path(temporary)/'first.env';second=Path(temporary)/'second.env'
            configure(first,'https://docs.example.org','owner@example.org')
            configure(second,'https://docs.example.org','owner@example.org')
            self.assertEqual(stat.S_IMODE(first.stat().st_mode),0o600)
            self.assertIn('BOTTIFACT_ORIGIN=https://docs.example.org',first.read_text())
            self.assertNotIn('REPLACE_WITH',first.read_text())
            self.assertNotEqual(first.read_text(),second.read_text())
            before=first.read_bytes()
            with self.assertRaises(FileExistsError):configure(first,'https://other.example.org','owner@example.org')
            self.assertEqual(before,first.read_bytes())

    def test_origin_rejects_redirect_shell_and_insecure_remote_inputs(self):
        for origin in ['https://user:pass@example.com','https://example.com/path','https://example.com?x=1',
                       'https://example.com;whoami','https://example.com$(whoami)','http://example.com',
                       'https://example.com:invalid','https://example.com:99999','https://example.com:0']:
            with self.subTest(origin=origin),self.assertRaises(ValueError):validate_origin(origin)
        self.assertEqual(validate_origin('https://docs.example.org/'),'https://docs.example.org')
        self.assertEqual(validate_origin('http://localhost:8788'),'http://localhost:8788')

    def test_instance_installation_links_and_auth_do_not_need_cloudflare(self):
        with tempfile.TemporaryDirectory() as temporary,patch.dict(os.environ,{'BOTTIFACT_ISSUER':'','BOTTIFACT_AUDIENCE':''}):
            client=TestClient(create_app(temporary,origin='https://docs.example.org'),base_url='https://docs.example.org')
            self.assertEqual(client.get('/health').status_code,200)
            for route in ['/install','/install.sh','/install.ps1','/install.py']:
                response=client.get(route)
                self.assertEqual(response.status_code,200)
                self.assertIn('https://docs.example.org',response.text)
                self.assertNotIn('https://artifacts.botto.is',response.text)
            self.assertEqual(client.get('/auth/login').status_code,503)

    def test_email_uses_own_origin(self):
        with patch.dict(os.environ,{'BOTTIFACT_ORIGIN':'https://docs.example.org','BOTTIFACT_EMAIL_URL':'https://mail.example.org','BOTTIFACT_EMAIL_FROM':'owner@example.org','BOTTIFACT_EMAIL_KEY':'fixture','BOTTIFACT_EMAIL_PROVIDER':'usesend'}),patch('portal.auth.remote_json') as remote:
            send_code('reader@example.org','123456')
            data=remote.call_args.args[1]
            for field in ['text','html']:
                self.assertIn('https://docs.example.org',data[field])
                self.assertNotIn('botto.is',data[field])

    def test_local_install_never_downloads_and_requires_explicit_future_source(self):
        with tempfile.TemporaryDirectory() as temporary,patch.object(updater,'ORIGIN','https://artifacts.botto.is'):
            root=Path(temporary);archive=root/'package.zip';data=installer_fixtures.InstallerTests().archive('local')
            archive.write_bytes(data);archive.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest())
            args=['install','--destino',str(root/'installed/library'),'--sin-enlaces']
            with patch.object(updater,'fetch',side_effect=AssertionError('Local installation contacted a server')),patch.object(sys,'argv',args+['--paquete',str(archive)]):updater.main()
            with patch.object(sys,'argv',args),self.assertRaisesRegex(ValueError,'Instalación local'):updater.main()

    def test_server_survives_an_upgrade_with_an_unmodified_packaged_updater(self):
        with tempfile.TemporaryDirectory() as temporary,patch.object(updater,'ORIGIN','https://artifacts.botto.is'):
            dest=Path(temporary)/'library';data=installer_fixtures.InstallerTests().archive('own-server');origins=[]
            def fetch(path,limit):
                origins.append(updater.ORIGIN)
                return data if path.endswith('.zip') else hashlib.sha256(data).hexdigest().encode()
            args=['install','--destino',str(dest),'--sin-enlaces']
            with patch.object(updater,'fetch',fetch):
                with patch.object(sys,'argv',args+['--servidor','https://docs.example.org']):updater.main()
                updater.ORIGIN='https://artifacts.botto.is'
                with patch.object(sys,'argv',args):updater.main()
            self.assertEqual(set(origins),{'https://docs.example.org'})

if __name__=='__main__':unittest.main()
