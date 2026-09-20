# Artifact analytics with your own Umami

Analytics is disabled by default for a self-hosted instance. No credential, website ID or owner account ships in the skill. A creator can enable or disable collection for their own artifacts under **Mi trabajo → Visitas**.

To configure a separately operated Umami website:

```dotenv
MARGEN_UMAMI_URL=https://analytics.example.com
MARGEN_UMAMI_WEBSITE_ID=your-website-uuid
# Optional instance-wide initial default; individual owner preferences take precedence:
MARGEN_ANALYTICS_ENABLED=0
```

Create the website in your Umami instance with your artifact hostname, then recreate the app container to reload its environment. Invalid origins/IDs disable the remote tracker. Only an HTTPS origin without credentials or a path is accepted. Umami authentication secrets are not required for collection and must never enter HTML.

The trusted parent reader loads Umami's official `script.js` after document access succeeds, with automatic tracking disabled. It sends one manual pageview for the published artifact's canonical `/a/ID` path. It uses a generic title, an empty referrer, browser language and screen size. It does not send query strings, thread IDs, private titles, comments, notes, email, agent sessions or a custom identity. The artifact iframe's sandbox and CSP remain unchanged. The parent's CSP permits only the configured analytics origin.

Own visits, agent requests, draft/history previews, embedded library thumbnails and Do Not Track / Global Privacy Control readers are excluded by the reader path. Blockers may prevent collection; do not claim complete audience coverage. No replay, heatmap, identity or user-content capture is enabled.

Margen also stores aggregate daily page-open counts, without IP addresses or visitor IDs, for up to 365 days. Counts represent opens, not distinct people. APIs require the same artifact access as the reader; only the owner can read the aggregate dashboard. The dashboard returns at most 2,000 daily rows and states that scope. Direct repeated authorized requests can inflate the aggregate; these are product analytics, not a fraud-resistant billing counter.

Collection begins when enabled; previous visits cannot be recovered. Verification should use a clearly named integration event in Umami or a synthetic test document, never a fabricated claim of real readership. Metrics retention in Umami is configured in that independent service.

Official contracts: [tracker configuration](https://docs.umami.is/docs/tracker-configuration), [custom pageviews](https://docs.umami.is/docs/tracker-functions), [collection API](https://docs.umami.is/docs/api/sending-stats). The integration uses functions available in Umami 3.0.3; newer automatic performance/replay features are deliberately not assumed.
