#!/usr/bin/env python3
"""Release authentication rejects tampering and wrong-channel packages."""
import hashlib, json, subprocess, tempfile, unittest
from pathlib import Path
from update import verify_release
import update
from unittest.mock import patch


class SignatureTests(unittest.TestCase):
    def test_signature_and_channel(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            key = r / "key"
            pub = r / "pub"
            subprocess.run(
                [
                    "openssl",
                    "genpkey",
                    "-algorithm",
                    "RSA",
                    "-pkeyopt",
                    "rsa_keygen_bits:2048",
                    "-out",
                    str(key),
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(pub)],
                check=True,
                capture_output=True,
            )
            digest = hashlib.sha256(b"fixture").hexdigest()
            raw = json.dumps(
                {
                    "schema": 1,
                    "channel": "stable",
                    "version": "2026.09.19-test.1",
                    "sha256": digest,
                    "package": "bottifact-portable.zip",
                    "compatibility": {"skill_contract": 4},
                }
            ).encode()
            (r / "manifest").write_bytes(raw)
            subprocess.run(
                [
                    "openssl",
                    "dgst",
                    "-sha256",
                    "-sign",
                    str(key),
                    "-out",
                    str(r / "sig"),
                    str(r / "manifest"),
                ],
                check=True,
            )
            sig = (r / "sig").read_bytes()
            self.assertEqual(
                verify_release(raw, sig, pub.read_text(), digest, "stable")["version"],
                "2026.09.19-test.1",
            )
            for content, expected, channel in [
                (raw + b" ", digest, "stable"),
                (raw, "0" * 64, "stable"),
                (raw, digest, "preview"),
            ]:
                with self.assertRaises(ValueError):
                    verify_release(content, sig, pub.read_text(), expected, channel)

    def test_signed_same_day_rollback_does_not_change_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'library';root.mkdir()
            version={'version':'2026.09.20-current','release_sequence':12}
            (root/'VERSION.json').write_text(json.dumps(version))
            manifest={'version':'2026.09.20-new-name','sequence':11}
            with patch.object(update.sys,'argv',['update.py','--destination',str(root),'--server','https://artifacts.botto.is','--no-links']),patch.object(update,'fetch',return_value=b'a'*64),patch.object(update,'verify_release',return_value=manifest),patch.object(update,'extract') as extract:
                with self.assertRaisesRegex(ValueError,'sequence is older'):update.main()
            extract.assert_not_called()
            self.assertEqual(json.loads((root/'VERSION.json').read_text()),version)


if __name__ == "__main__":
    unittest.main()
