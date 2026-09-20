# Host Margen on your own server

To use the existing service without operating a server, follow [artifacts.botto.is onboarding](hosted-service.md). This guide is only for deploying your own instance.

The portal is optional. A skill-only installation creates HTML without a server. Hosting adds accounts, access controls, comments, notes, versions and a searchable artifact library. Your instance has its own users, files and tokens; it does not synchronize them with botto.is.

## 1. Prepare the host

Use Docker with Compose v2 on a Linux host, VM or NAS. For a first small installation, budget around 2 GB of host RAM plus space for artifacts and backups; this is a starting budget, not a measured capacity guarantee. SQLite runs on a local persistent volume. Use one app and one worker; do not scale app replicas or put SQLite on a network filesystem.

For public HTTPS, point your domain's A/AAAA records at the host and allow ports 80 and 443. Remove an incorrect AAAA record if the host has no IPv6 connectivity. If a reverse proxy already owns those ports, use the existing-proxy option below. Nothing here requires Cloudflare.

```bash
git clone https://github.com/angelbotto/margen.git
cd margen
python3 scripts/configure_portal.py \
  --origin https://artifacts.example.com --admin you@example.com
```

Replace the domain and email. The command creates `.env` with permissions `0600` and a random authentication secret. It refuses to overwrite a file. Keep `.env` outside version control and back it up separately in encrypted storage.

For development on the Docker host, `--origin http://localhost:8788` works without the HTTPS overlay. Remote users need HTTPS. Do not change the default loopback port binding to expose plain HTTP publicly.

## 2. Start

With automatic HTTPS through Caddy:

```bash
docker compose -f compose.yaml -f deploy/https.yaml config --quiet
docker compose -f compose.yaml -f deploy/https.yaml up -d --build
```

Caddy forwards to `app:8080`, handles certificates and persists them in `caddy_data`. Keep ports available for certificate renewal. Do not delete that volume during upgrades.

With an existing HTTPS reverse proxy:

```bash
docker compose config --quiet
docker compose up -d --build
```

Forward your configured origin to `http://127.0.0.1:8788`. A proxy in a different container needs a shared Docker network and `app:8080` instead of the host loopback. Preserve request bodies, query strings, cookies and the `Origin` header. Do not place a separate Google/Cloudflare Access login in front of Margen's normal login flow.

Check startup:

```bash
docker compose ps
curl --fail http://127.0.0.1:8788/health
```

The image builds the portable skill ZIP and serves it from `/downloads`. Both the application and background worker run without root, with read-only root filesystems; named volumes hold their writable data. `BOTTIFACT_UID` / `BOTTIFACT_GID` default to 1000. Changing them on an existing installation also requires deliberate ownership migration of its volumes.

## 3. Sign in as the first administrator

```bash
docker compose exec app python -m portal.manage bootstrap --email you@example.com
```

The email must be in `BOTTIFACT_ADMIN_EMAILS`. The command prints a temporary, single-use sign-in URL. Open it privately; do not paste it into an issue, chat log or README. Administrator bootstrap requires server access and is intended for initial setup or recovery.

Configure at least one of the normal sign-in methods below before inviting other users. Provider credentials are never bundled in the skill. Authentication establishes identity; document permissions decide what that identity can read or change. An admin can see all artifacts on their instance, so assign admin accounts deliberately.

### Google

In your own Google Cloud project, configure an OAuth consent screen and a Web application OAuth client. Register this exact authorized redirect URI:

```text
https://artifacts.example.com/auth/google/callback
```

Set these values in `.env`:

```dotenv
BOTTIFACT_GOOGLE_ENABLED=1
BOTTIFACT_GOOGLE_ID=your-client-id
BOTTIFACT_GOOGLE_SECRET=your-client-secret
```

Use the domain from `BOTTIFACT_ORIGIN`. Configure consent-screen audience/test users appropriately in Google; a successful administrator bootstrap does not prove Google consent works for everyone.

### Email codes

The current adapters support **UseSend** and **Resend**, through their HTTP APIs. SMTP is not implemented. UseSend can be deployed separately if you want to operate that service too.

```dotenv
BOTTIFACT_EMAIL_PROVIDER=usesend
BOTTIFACT_EMAIL_URL=https://mail.example.com
BOTTIFACT_EMAIL_FROM=Margen <no-reply@example.com>
BOTTIFACT_EMAIL_KEY=your-provider-key
```

For Resend, use `BOTTIFACT_EMAIL_PROVIDER=resend` and `BOTTIFACT_EMAIL_URL=https://api.resend.com`. Configure and verify your sender domain with the provider, including its DNS requirements. Provider acceptance is not proof of delivery: send a test code to a real inbox and check spam/delivery status.

Apply environment changes by recreating containers (a plain restart does not reload `.env`):

```bash
docker compose up -d --force-recreate app worker
```

### Administrator aliases

`BOTTIFACT_ADMIN_EMAILS` is a comma-separated set of administrators. `BOTTIFACT_OWNER_ALIASES` is different: it combines addresses of **the same owner**, with the canonical email first. Never put several teammates in the alias list; that would merge identities. Leave it empty unless you need it.

## 4. Install and connect agents

Your server serves its own installation instructions at `/install`. For an HTTPS instance:

```bash
curl -fsSL https://artifacts.example.com/install.sh -o /tmp/bottifact-install.sh
# Review the script, then run it:
bash /tmp/bottifact-install.sh
```

The installer downloads from that origin and remembers it for future updates. It creates a shared skill for Claude Code, Codex and Hermes. `margen update` continues using the selected server. A local ZIP installation is also supported; see the README.

Sign in to your portal, open **Conectar un agente**, and create an access token. Connect through the CLI, which prompts for the token without putting it in a shell command:

```bash
margen connect --server https://artifacts.example.com
margen status
```

Creating files remains local. Publishing requires explicit instruction or the user's stored `publish_on_create` preference. New documents are private unless explicitly published otherwise. Tokens, personal settings and publication receipts live outside the skill folder and must never be added to a shared ZIP.

## Configuration reference

| Variable | Purpose |
| --- | --- |
| `BOTTIFACT_ORIGIN` | Exact external origin, including HTTPS; used for auth, links and installers |
| `BOTTIFACT_DOMAIN` | Hostname for the optional Caddy overlay |
| `BOTTIFACT_ADMIN_EMAILS` | Comma-separated administrator emails |
| `BOTTIFACT_OWNER_ALIASES` | Optional addresses of a single owner, canonical first |
| `BOTTIFACT_AUTH_SECRET` | Random secret protecting email authentication challenges |
| `BOTTIFACT_GOOGLE_ENABLED`, `_ID`, `_SECRET` | Enable native Google OIDC and configure its client |
| `BOTTIFACT_EMAIL_PROVIDER`, `_URL`, `_FROM`, `_KEY` | Email code/digest provider settings |
| `BOTTIFACT_DATA` | Container data path; keep `/data` with the supplied Compose file |
| `BOTTIFACT_BACKUPS` | Container backup path; keep `/backups` |
| `BOTTIFACT_RELEASES` | Bundled portable downloads; keep `/releases` |
| `BOTTIFACT_BIND`, `BOTTIFACT_PORT` | Host HTTP binding, default `127.0.0.1:8788` |
| `BOTTIFACT_UID`, `BOTTIFACT_GID` | Runtime user/group build arguments |
| `BOTTIFACT_IMAGE_TAG` | Optional local image tag, default `latest` |

There is no default password and no preloaded administrator data. The legacy `portal/compose.yaml` illustrates the original Synology deployment; **new instances should use the root `compose.yaml`**.

## Backups and recovery

The worker creates a daily consistent SQLite snapshot, copies referenced files, verifies hashes and performs a restore into an isolated temporary directory. Backups are stored in the `backups` volume. Copy them to a separate host or storage location: a second volume on the same disk does not protect against losing the disk. Monitor available storage and set your own retention; this release does not delete old backups automatically.

Create a backup now:

```bash
docker compose exec app python -m portal.backup create --data /data --output /backups
```

The command returns the backup directory. Verify a selected backup and restore it into a **new** directory first:

```bash
docker compose exec app python -m portal.backup verify /backups/BACKUP_DIRECTORY
docker compose exec app python -m portal.backup restore /backups/BACKUP_DIRECTORY /backups/restore-check
```

Replace `BACKUP_DIRECTORY` with the returned name. Existing destinations are refused. For disaster recovery, stop app and worker, restore into a new data volume/directory with the correct runtime ownership, point the app at it and verify login, file reads, permissions and comments before switching traffic. Preserve the old volume until that verification succeeds. Never overwrite a live SQLite database.

Keep `.env`, any external reverse-proxy configuration and DNS/provider recovery credentials separately. The default Compose backup does not include `.env`. Backups contain private documents and identities; protect them like production data.

## Upgrade

Before upgrading, create and verify a backup and record the current commit/release. Read [CHANGELOG.md](../CHANGELOG.md). From a clean source checkout:

```bash
git pull --ff-only
docker compose -f compose.yaml -f deploy/https.yaml up -d --build
```

Use the command without the HTTPS overlay if you use your own proxy. Volumes and `.env` survive image rebuilds. **Do not use `down -v` for upgrades.** Rollback can require restoring a pre-upgrade database if a future migration is incompatible; changing only the image is not a universal rollback procedure.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `/health` fails | `docker compose ps` and `docker compose logs --tail=80 app`; volume ownership and available disk space |
| HTTPS certificate not issued | DNS, IPv4/IPv6 routing, ports 80/443, Caddy logs and another proxy occupying those ports |
| Login returns to the wrong host | `BOTTIFACT_ORIGIN`, exact Google redirect URI and recreated containers |
| Email code never arrives | Provider key, verified sender, spam folder and provider delivery status |
| Library looks empty | Signed-in account, permissions and owner aliases; a fresh install starts empty |
| Updates download from another host | Re-run that instance's installer, or `margen update --server https://artifacts.example.com` |
| Backup status is stale | Worker health, disk capacity and permissions on `/backups` |

When sharing logs, redact credentials, email addresses, private titles, access links and document bodies. Report security issues through [SECURITY.md](../SECURITY.md).

## Optional analytics

See [analytics](analytics.md) for owner-controlled page-open measurement and your own Umami instance. Collection is disabled by default and requires no Umami authentication secret in the artifact.
