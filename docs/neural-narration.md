# Neural narration: implementation and audition gate

Status: **provider not selected; disabled by default; neural quality not validated**. No provider account was purchased or called for this change. The old device-voice approach does not meet the requested experience and is no longer a fallback. This work adds reviewable transport and candidate adapters, not a claim that a voice sounds natural in Spanish.

## Candidate research

Official documentation checked on 2026-10-21. Capabilities establish feasibility, not comparative listening quality.

| Candidate | Relevant capabilities and integration | Decision still needed |
| --- | --- | --- |
| Azure Speech, stock multilingual neural voices | [SSML](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice) controls language, rate, pitch and voice-dependent styles. The candidate uses the [REST synthesis endpoint](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech), escaped literal text and MP3 output. | Audition supported voices in the configured region. Verify style support per voice, ES accent and transitions. No voice is selected by this PR. |
| ElevenLabs `eleven_multilingual_v2`, stock voices | The [streaming endpoint](https://elevenlabs.io/docs/api-reference/text-to-speech/stream) accepts literal text and per-request voice settings. This candidate varies stability/style/speed by reading profile. This model does not accept enforced `language_code`; mixed-language pronunciation must be heard. | Audition ES/EN/mixed, fragment continuity and exact reading. Confirm account price, stock voice rights and retention. The API documents zero retention as enterprise-only; this adapter does not claim zero retention. |
| OpenAI Realtime | The [TTS guide](https://developers.openai.com/api/docs/guides/text-to-speech) deprecates `tts-1`, `tts-1-hd` and `gpt-4o-mini-tts`, retiring them on **2027-01-06**, and directs migration to `gpt-realtime-2.1-mini` through Realtime, not `/audio/speech`. The guide warns that its voices are optimized for English. [Realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations) offer audio output and instructions. | Research candidate only, no adapter here. Conversational generation requires a separate literal-fidelity evaluation and transport/cost design. No new integration uses a retiring speech model. |

No cloning, voice upload or impersonation endpoint is implemented. Operators must configure stock voices. No quality ranking is inferred from vendors' product descriptions.

## Text and prosody

The reader extracts visible editorial text in DOM order and sends a proposed list to the trusted parent. The parent fetches a source manifest from the authorized immutable version and matches exact full-block text plus an ancestor ID. Ambiguous matches, runtime-only changes or altered text fail visibly. Unicode offsets are converted to code points; the backend accepts only canonical block IDs and bounded offsets, never arbitrary speech text or instructions.

Before generation the portal shows **all proposed text**, provider, voice and style in a modal. Only its confirmation creates a session. The session fixes user, artifact, version/SHA, exact ranges, voice and profile. The iframe cannot authorize spending by just emitting a message. Verified browser identity and read permission are required; a public link alone does not grant provider usage.

Profiles are explicit: **Informe**, **Narración**, **Lectura neutra**. Heading/table/prose semantics adjust pauses and, for Azure, pitch/rate; configured voice-supported styles are optional. ElevenLabs adjusts its supported voice settings. `lang="es…"` and `lang="en…"` annotations become escaped SSML language runs for Azure; ElevenLabs detects language from text. Unannotated English and switches inside one sentence need particular audition attention. There is no model that rewrites, summarizes, translates or adds introductions. Whitespace is normalized. Spoken fidelity still requires listening: an API may mispronounce numbers or omit words despite receiving exact text.

Fragments are at most 1,200 characters, one generated at a time, at most 500 fragments / 80,000 characters per confirmed reading. Table captions/headers/cells follow source order; there is no inferred merged-cell interpretation. Full/section reading skips code with an explicit control explanation; selecting code reads the selected literal text. Charts require editorial captions. The browser excludes CSS-hidden content; the backend parser excludes semantic/inline hidden content but does not evaluate stylesheets. Therefore the full parent preview is the authorization boundary; the backend manifest is not a rendered visibility claim.

## Transport and isolation

Audio plays in the parent via same-origin `HTMLAudioElement`. The iframe keeps its opaque origin, `connect-src 'none'`, and existing sandbox/CSP. It receives state/index events, never provider secrets, audio/session URLs or provider errors. The bridge checks parent/frame source; the host also requires the opaque origin and marked operation. The parent invalidates pending confirmation and late responses on document/version navigation and iframe loads.

A POST claims a fragment exactly once and reserves quota **before** opening the provider. GET/HEAD/Range/retry cannot initiate synthesis. A GET streams bounded MP3 bytes; only a complete stream enters cache. HTTP truncation/error marks failure. After media `ended`, the parent verifies server completion before advancing. No automatic retries or device-voice substitution. A rejected browser `play()` stops visibly; autoplay, background audio and screen-lock support are not promised.

Pause retains the current stream/audio buffer; resume uses the same element. Speed changes playback rate without resynthesizing. Stop/navigation closes playback and cancels the session/provider connection; an in-flight request may already have incurred vendor cost. Closing a connection cannot retract text already delivered to a vendor. Disconnected streams discard partial output. Unclaimed prepared streams expire after 20 seconds, sessions after one hour. Explicit cancellation is the recovery path after long suspension.

## Configuration and usage limits

See [.env.example](../.env.example). Activation requires **both** `MARGEN_NARRATION_ENABLED=1` and `MARGEN_NARRATION_BILLING_APPROVED=1`, a dedicated `MARGEN_NARRATION_KEY`, valid provider/voices and positive usage/cost limits. Other existing API keys are not discovered or reused. Invalid configuration fails closed, including optimized Python. Keep secrets in the existing server secret mechanism; never commit actual `.env` values.

- Azure: `PROVIDER=azure`, `AZURE_REGION` from the authorized resource; voice entries have `{ "id": "audition-a", "label": "Voice under test", "voice": "<stock MultilingualNeural voice>" }`. Optional `styles` maps `report`, `narrative`, `neutral` to styles that this voice actually supports. Region/model/voice validation is configuration validation, not a network credential test.
- ElevenLabs: `PROVIDER=elevenlabs`, `MODEL=eleven_multilingual_v2`; the same voice shape uses an authorized stock voice ID. Voice enumeration/selection is an operator action, not an automatic paid discovery call.
- `DAILY_CHARS` is a global UTC-day ceiling, `USER_CHARS` an additional per-user ceiling. Maximum global configuration is 10 million characters. `DAILY_MICRO_USD` caps the conservative reservation calculated from request bytes and an explicitly approved `USD_PER_MILLION_CHARS`. No prices are hard-coded. Set an upper-bound rate including the account/model multipliers; this reserve is not a reconciliation of the vendor invoice. Configure a vendor-side account cap too if available.
- Reservations are durable in SQLite, atomic under the store transaction, and retained for 31 days. Failed/cancelled requests keep their reservation; no speculative refund or automatic retry can bypass a limit. There are at most two provider streams globally, two active sessions per user and sixteen globally.

This implementation targets the repository's **single-instance, single-process** SQLite deployment. Sessions and concurrency claims are in memory; multiple web workers/replicas require shared session/claim coordination before enabling narration. A restart invalidates sessions while retaining reservations and private cache.

## Private cache and deletion

Cache keys include artifact, version/SHA, exact block/ranges/text/languages, voice, profile and provider/configuration fingerprint. Cache is never globally shared by text alone. Every delivery rechecks identity and current version access. Responses are `private, no-store`; browser HTTP caching is not used. The server cache has a 24-hour lifetime, a 64 MiB audio budget and LRU trimming on activity/startup; each clip is bounded at 8 MiB. Expired entries are not served.

`DELETE /api/artifacts/{id}/narration/cache` requires manage permission. It cancels all document sessions and deletes its cached audio under the same lock, preventing a stream from repopulating it. Version/artifact foreign keys cascade on actual deletion. Archiving is not deletion. SQLite secure deletion is enabled for this purge; existing backups have their own retention and are not erased by deleting the live cache. Provider retention is separate and must be approved before sending confidential text.

## Prepared audition, no paid execution

Run `python3 scripts/prepare_narration_audition.py`. This writes synthetic standalone HTML and a blank scorecard to ignored `tests/artifacts/`; it makes **no network call**. Import that HTML privately into a local/test portal only after an authorized provider/account, regional policy and maximum spend have been agreed. Do not use customer documents for a public audition.

The corpus has Spanish, English and mixed-language sections, each with report and narrative text, plus numbers, abbreviations, punctuation, inline language changes, table and code. Test both Informe and Narración against the **same text** to distinguish style from content changes. Compare candidates blind with stable voice/profile IDs and record model/region, source SHA, timestamp, actual cost, time to first audio and browser. Keep generated audio private unless its publication is separately authorized.

For each condition record 1–5 scores for ES pronunciation, EN pronunciation, switching, naturalness, pauses/rhythm, fit to document type and continuity across fragments. Record every insertion, omission, paraphrase or number/name error against the source. Proposed release gate: zero meaning-changing errors or additions/omissions, ES and EN pronunciation/naturalness at least 4/5 from fluent listeners, and Angel's acceptance of the report-versus-narrative contrast. Automated transcripts can assist but cannot replace listening.

**Current results:** no neural audio generated or heard; every score remains pending. Deterministic tests validate plumbing, not auditory quality. Provider choice, authorized budget/retention, real listening, Safari/Firefox/physical-mobile checks and human PR review remain release gates. This PR does not merge or deploy the feature.
