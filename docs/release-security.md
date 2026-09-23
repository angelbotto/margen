# Release channels, verification and compatibility

Managed downloads from artifacts.botto.is use a signed manifest in addition to the ZIP's SHA-256. The updater pins the release public key and verifies RSA/SHA-256 through OpenSSL on Unix or native .NET on Windows before extracting or executing package code. Manifests declare the channel, package digest, version and contract compatibility. `stable` is the default; `--channel preview` is explicit and persists. A channel with no published manifest fails closed.

```bash
margen update --check
python3 scripts/update.py --channel stable --if-changed
# A self-hosted operator can pin their own public key out of band:
python3 scripts/update.py --server https://artifacts.example.com --trusted-key release-public.pem
```

Self-hosted instances remain independent: unsigned custom servers and explicitly selected local packages retain checksum verification. Pin a key to require authenticated releases. A checksum alone detects corruption but does not authenticate the publisher. Never replace a pinned key from the same untrusted download being verified.

Maintainers keep the private key outside Git and build images:

```bash
python3 scripts/package.py
python3 scripts/release_manifest.py --package dist/bottifact-portable.zip --key /secure/release-private.pem --channel stable
```

Publish the ZIP, checksum, `stable.json` and `stable.json.sig` together. A preview build produces `bottifact-preview.zip`, its checksum and the matching preview manifest/signature. Sign only the reviewed commit's package. Back up the signing key separately; key rotation requires a reviewed updater release or explicit out-of-band repinning.

The initial `install.sh`/`install.py` bootstrap still relies on HTTPS or a reviewed Git checkout. Installed pinned verification protects subsequent packages; it is not a claim of reproducible trust from an untrusted bootstrap. The updater rejects an older release date. Intentional rollback uses an explicitly reviewed local package. New signed releases include a monotonic sequence also stored in VERSION.json. Updated installers reject a lower sequence, including a rollback within the same day, and verify that package and manifest agree. Legacy installations gain this protection after updating their installer; retain metadata and backups.

Current compatibility: Python 3.10+, skill contract 4, assignment contract 1, format capability contract 1. Changes requiring a higher skill contract fail before installation with the older updater. Agent CLI versions are independent and must be checked on the executing device.
