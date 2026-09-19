#!/usr/bin/env python3
"""Release authentication rejects tampering and wrong-channel packages."""
import hashlib, json, subprocess, tempfile, unittest
from pathlib import Path
from update import verify_release


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


if __name__ == "__main__":
    unittest.main()
