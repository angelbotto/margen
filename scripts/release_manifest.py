#!/usr/bin/env python3
"""Sign a portable release manifest with an external RSA private key."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sign(package, key, channel="stable"):
    import zipfile

    with zipfile.ZipFile(package) as z:
        metadata = json.loads(z.read("bottifact/VERSION.json"))
        version = metadata["version"]
    manifest = {
        "schema": 1,
        "channel": channel,
        "version": version,
        "sequence": metadata.get("release_sequence",0),
        "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
        "package": (
            "bottifact-preview.zip"
            if channel == "preview"
            else "bottifact-portable.zip"
        ),
        "compatibility": {
            "python": "3.10",
            "assignment": 1,
            "formats": 1,
            "skill_contract": 4,
        },
    }
    if channel == "preview":
        import shutil

        destination = package.parent / "bottifact-preview.zip"
        if package != destination:
            shutil.copyfile(package, destination)
        destination.with_suffix(".sha256").write_text(
            manifest["sha256"] + "  " + destination.name + "\n"
        )
    target = package.parent / (channel + ".json")
    target.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    )
    subprocess.run(
        [
            "openssl",
            "dgst",
            "-sha256",
            "-sign",
            str(key),
            "-out",
            str(target) + ".sig",
            str(target),
        ],
        check=True,
    )
    return target


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--key", type=Path, required=True)
    p.add_argument("--channel", choices=["stable", "preview"], default="stable")
    a = p.parse_args()
    print(sign(a.package, a.key, a.channel))
