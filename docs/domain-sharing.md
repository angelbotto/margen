# Share with an email domain

An artifact owner can authorize a whole team without maintaining an email list. In **Share → People and authorized domains → A whole team**, add an exact email domain, choose **View** or **Comment**, then save permissions. In the Spanish interface these controls are **Compartir → Personas y dominios autorizados → Todo un equipo**.

Members sign in with Google or an email code. Their verified account email must match the domain exactly. New members qualify automatically; they can open the link and find the document in **Shared**. Receiving a link alone does not grant access. Domain grants do not create administrators or editors, and the feature sends no invitation emails.

## Scope and precedence

- `example.com` matches `person@example.com`, including normalized case. A leading `@` is accepted in configuration. Domains use ASCII DNS spelling; use the ASCII/punycode form for an internationalized domain.
- It does not match `team.example.com`, `otherexample.com` or `example.com.other.org`. Wildcards, URLs, email addresses and IP addresses are rejected.
- Up to 25 domains can be assigned independently to each artifact. Instances have no maintainer-specific domain defaults.
- An explicit personal grant takes precedence over the domain grant. For example, an individually assigned viewer remains a viewer even when their domain can comment. Personal editor grants still work.
- Owners and instance administrators retain management rights. Domain grants permit only `viewer` or `commenter`.
- Drafts and other people's private notes remain excluded. Domain access does not share agent transcripts, tokens or session credentials.
- Removing a domain removes that path to access immediately on subsequent requests. An independent personal grant, ownership, administrator status or public/unlisted visibility can still allow access. Previously downloaded content cannot be withdrawn.
- Choosing Private removes both personal and domain grants. Public and unlisted visibility allow readers outside the domain; choose Invited for a team-only document.
- Domain eligibility uses the verified email recorded on the Margen account. It is not live Google Workspace directory membership or employee offboarding. Existing sign-in sessions remain valid under the portal session policy; revoking all sessions for a departed employee requires account/session administration.

## From an agent or terminal

Publish the document privately first, then share only when the user has explicitly authorized the audience:

```bash
margen share --artifact-id ARTIFACT_ID --domain example.com --role commenter --visibility invited
margen share --artifact-id ARTIFACT_ID --domain another.example --role viewer
margen share --artifact-id ARTIFACT_ID --remove-domain another.example
margen share --artifact-id ARTIFACT_ID --visibility private
```

`--domain` and `--remove-domain` are repeatable. Additions are merged with existing domain grants; personal grants, comment settings, document ID, versions and URL are preserved unless Private is explicitly selected. Without `--visibility`, a private artifact becomes invited when a domain is added; public/unlisted artifacts retain their broader visibility. Use `--visibility invited` to restrict a document to authorized people and domains. The command reports the saved audience after writing it and refuses an older portal that lacks domain support.

The updated UI and CLI include `expected_access`, the manager-only access revision returned by the artifact endpoint. A stale save returns 409 without restoring an audience another manager revoked. Reopen Share or rerun the command to read the latest settings. Legacy clients without this token retain last-write behavior.

## API and compatibility

`GET /api/artifacts/{id}` returns `domain_grants` only to managers (an empty array for readers). `PUT /api/artifacts/{id}/access` accepts:

```json
{
  "visibility": "invited",
  "comments": "reviewers",
  "guests": false,
  "grants": [],
  "domain_grants": [{"domain": "example.com", "role": "commenter"}]
}
```

An explicit `domain_grants: []` revokes domain grants. Omission preserves the domain audience for older clients, except when changing to Private, which clears all grants. Invalid input is rejected atomically. Duplicate normalized domains are rejected. The SQLite migration adds an indexed `domain_grants` table without changing existing audiences; normal database backups include it.

Authorization is enforced on direct reads, rendered versions, review, library/search and context links. Matching is computed from the verified identity, never from a query parameter, guest display name, project label or theme. The shared library reports the effective role using the same precedence as direct reads.
