# Portal operations

Portable HTML works independently. Inside a configured Margen portal, an isolated bridge adds authenticated review, shared versions and permissions. See [self-hosting](self-hosting.md) for the complete environment and deployment reference; use [the hosted service](hosted-service.md) when no server operation is needed.

## Identity and access

The portal owns its login flow: Google OAuth and configured email-code delivery. Provider credentials and the stable authentication secret live in an external environment file. Google returns to `/auth/google/callback` on the configured public origin. Administrator aliases are an instance configuration, not identities to copy into another installation.

Artifacts support private, public and unlisted visibility plus explicit access grants. Public publishing needs authorization. Readers and reviewers have distinct permissions; private notes remain author-owned. Every search, graph, reference and export endpoint must enforce access. Tokens grant selected agent capabilities; never embed them into HTML or publish them in transcripts.

The artifact iframe has an opaque origin and a restricted CSP. Credentials stay in the parent/server boundary. Do not loosen sandbox or CSP settings for styling, previews or convenience. The account UI loads external CSS/scripts. Runtime bridge data is validated as untrusted input.

## Routine publishing

```bash
python3 scripts/publish.py status
python3 scripts/publish.py listar --buscar 'quarterly review'
python3 scripts/publish.py publicar --file /path/review.html --title 'Quarterly review' --space 'Company' --agent Codex
python3 scripts/publish.py versiones --artifact-id ARTIFACT_ID
python3 scripts/publish.py comentarios --abiertos
```

The saved publishing preference is separate from public visibility. New documents are private by default. Existing document IDs resolve to revisions, preserving link, audience and feedback. Record a real session and device; missing provenance stays unknown. Organization and title edits need not create versions.

## Review and release

Upload a draft, inspect its preview, compare against the published revision and release with an expected-current guard:

```bash
python3 scripts/publish.py comparar --artifact-id ARTIFACT_ID --desde OLD_VERSION --hasta NEW_VERSION
python3 scripts/publish.py liberar --artifact-id ARTIFACT_ID --version NEW_VERSION --expected-current OLD_VERSION
```

A copied context bundle includes the artifact URL, version, hash, anchors and selected feedback. Include only authorized comments and explicitly selected own notes. It does not transmit to an AI service or reopen a session. Stale or ambiguous anchors require human/source verification. Local standalone JSON is not automatically imported into shared history.

## Delivery, recovery and upgrades

Email requires a configured provider, sender and credential. Queue acceptance is not proof of inbox delivery; inspect provider results and retry behavior. Keep logs free of tokens and document bodies. Backup uses SQLite's online backup mechanism plus required stored artifacts and a separately protected configuration snapshot. Verify restore into an empty isolated destination before switching production volumes.

```bash
python -m portal.backup --help
python -m portal.backup create --data /data --output /backups --config /path/private.env
```

Use immutable image tags, a pre-upgrade backup and health checks. Preserve UID/GID, mounts, read-only filesystem, capability restrictions and the existing public origin. Update the portable ZIP/checksum pair consistently. The portal and agent skill have separate release lifecycles; installed agents must reread the skill.

References: [SQLite backup API](https://www.sqlite.org/backup.html), [Resend idempotency](https://resend.com/docs/dashboard/emails/idempotency-keys), [W3C Web Annotation](https://www.w3.org/TR/annotation-model/). Margen uses its own selectors and does not claim full Web Annotation conformance.

## Reader activity

See [reader activity](reader-activity.md) for creator-controlled aggregate visibility, Umami reporting credentials, unique-visitor semantics and participant privacy.
