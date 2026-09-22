# Reader activity

The reader's **Share → Artifact activity** panel shows page opens, estimated unique visitors, and participants in the conversation the current reader may access. The three-action dock remains Comments, Share, Preferences.

## Visibility and scope

Creators can enable reader activity for one artifact in the panel. It defaults to creator-only. Account preferences can set `share_with_readers` for the creator's artifacts; an explicit artifact setting overrides that default. Access to activity always requires access to the artifact. Changing visibility or revoking a grant immediately applies to the endpoint, including when upstream counts are cached.

- Visits and uniques use the selected 7/30/90/365-day UTC window, starting at midnight on the first day.
- Participants include authors of visible, non-deleted comment threads and replies across published versions. They cover the full conversation, independently of the visits window.
- Private notes and draft threads are excluded, including from the creator's aggregate. Hidden review conversations do not contribute names or counts for a reader who cannot access them.
- Names are plain text, with verified/guest status. Emails, actor IDs, visitor identities and IPs are not returned. Up to 30 names are shown; the total counts the full visible participant set.

## Umami reporting

Existing `MARGEN_UMAMI_URL` and `MARGEN_UMAMI_WEBSITE_ID` configure the browser collector. Reporting adds a **server-only** credential:

| Variable | Meaning |
| --- | --- |
| `MARGEN_UMAMI_API_VERSION` | `3` (default) or `2`. v3 filters with `path`; v2 uses `url`. Set the actual deployed version. |
| `MARGEN_UMAMI_API_ORIGIN` | Optional internal server endpoint, e.g. `http://umami:3000` on a private Docker network. Empty uses the public HTTPS origin. Never exposed to the browser. |
| `MARGEN_UMAMI_SHARE_ID` | Website-scoped read-only reporting credential from Umami's share feature. Treat it as a secret: knowing it grants access to that website's analytics in Umami. Keep the share URL private. |
| `MARGEN_UMAMI_TOKEN` | Alternative existing bearer token. Scope the associated account appropriately. |
| `MARGEN_UMAMI_USERNAME`, `MARGEN_UMAMI_PASSWORD` | Alternative self-hosted login. Use a dedicated least-privilege account. |

Configure one credential method. Shared reporting validates the returned website ID before using the token. The server requests only `/a/ARTIFACT_ID`, never a caller-supplied path, website or URL. Reports are cached for up to five minutes in a bounded process cache; failures retry after 30 seconds. Requests have timeouts and bounded response sizes; redirects are refused. No raw analytics response or provider error reaches the reader.

A share ID is a capability for the entire Umami website, so do not distribute it to readers. Margen applies its own per-artifact authorization before returning only allowed aggregates. Self-hosted operators can instead use an authenticated account credential.

## What the numbers mean

Umami's pageviews and visitors are used together so their source and period match. Unique visitors are a technical estimate, not a list of authenticated people. Do not sum daily uniques to compute period uniques.

If reporting is unavailable, Margen can display its existing count of page opens; uniques are **unavailable**, not zero. The panel labels that fallback explicitly. Disabled collection shows unavailable visit metrics. The existing collector excludes identified owner/agent reads, noncurrent versions, and DNT/GPC requests. Counts can be affected by blockers or unavailable collection, and are not security/audit logs or evidence of reading completion.

References: [Umami v3.0.3 stats route](https://github.com/umami-software/umami/blob/v3.0.3/src/app/api/websites/%5BwebsiteId%5D/stats/route.ts), [v3 path filter](https://github.com/umami-software/umami/blob/v3.0.3/src/lib/schema.ts), [v2 statistics API](https://v2.umami.is/docs/api/website-stats-api).
