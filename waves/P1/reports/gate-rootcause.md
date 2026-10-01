# Gate root-cause: market.spec.ts:197 and press.spec.ts:9

Author: qa-engineer. Source: `.gate/run-20261001T021953Z.log` (fail) vs
`.gate/run-20261001T002657Z.log` (A2, pass), code reading only; no stack was up to re-run live
(ports 3000/5173/5174/8000 all free) and gate instructions forbade starting dev:all.

## 1. invai-web `market.spec.ts:197` (AC32) — CONFIRMED, layer: web component

Cause: `src/routes/_app/catalog/designs.index.tsx:176` renders one `<SignedImage>` per design
card for the whole first page of the list (`designs.list` default `limit: 60`; the seed has ~40
designs, per T-P1-4's own report "0 to 40/40 previews"). Before T-P1-4 (backend 7247b32),
`placements[0]?.previewKey` was always `null`, so `useSignedUrl` (`signed-image.tsx:7-16`,
`enabled: !!fileKey`) never fired — zero `files.downloadUrl` calls, ever, from this page. Now
every card fires its own POST, and Chrome queues most of them behind its 6-connections-per-origin
cap. The test's `settled()` helper (`e2e/helpers/ui.ts:74-83`) polls for zero `[data-slot=skeleton]`
but **silently swallows a timeout** (`.catch(() => {})`), so `link.click()` can fire while a chunk
of the ~40 thumbnail fetches are still in flight; navigating away aborts them, and `watchPage()`
(`ui.ts:9-55`) correctly flags every `net::ERR_ABORTED` except the one allow-listed ask-abort shape.
The single `analytics/designLifecycle` abort (fired with no loading UI at all, `designs.index.tsx:90`)
is the same mechanism. A2's log confirms: same test, same spec, 2.9s, zero aborts, before T-P1-4
existed.

Not a backend bug: no 4xx/5xx from `files.downloadUrl`, only client-driven cancels. Not purely a
test bug either: `watchPage`'s strict policy is deliberate (B-132 comment: "nothing else is
allow-listed") and correctly caught a real regression — rendering ~40 signed-URL fetches with no
lazy-loading/virtualization on a list page is new, wasteful load introduced by T-P1-4 surfacing a
pattern that was previously dead code.

Owner: web-engineer (lazy-fetch or batch the catalog grid's thumbnails, e.g. only request a
signed URL once a card is near-viewport, or add a bulk `downloadUrl`-for-many endpoint).
Secondary: qa-engineer backlog — `settled()`'s swallowed timeout should surface as a failure, not
silence, for the next time this masks a real cause.

Retry on fresh seed: not justified. The count of in-flight requests will vary run to run, but the
test will keep failing while the grid has ~40 cards and no lazy-loading; it is not an environmental
flake.

## 2. invai-floor `press.spec.ts:9` — CONFIRMED timeout, cause only partially confirmed

Confirmed: the floor's RPC client timeout is `TIMEOUT_MS = 10_000` (`src/api/rpc.ts:13,43,47`); on
timeout it throws `ApiFailure("offline", "TIMEOUT", ...)`, which `SyncEngine.submit`
(`src/outbox/sync.ts:100-120`) reports as `status: "queued"`, and `PressStation.runCheck`
(`src/stations/PressStation.tsx:84`) falls back to `localPressCheck`. The test's 16.5s total
(vs A2's 2.7s) is consistent with exactly one scan call eating the full 10s before falling back,
plus setup/login/first-scan time — not a logic bug in the mismatch-reason code.

Refuted: the `[api]`/`[worker]` restart at log line ~788 is the gate's own deliberate
restart-once-after-seed step (`run-golden-path` step 5); it completes ~300 lines (several minutes)
before the floor suite starts at line 1101, and `[api]` never logs again until the suite's own
shutdown. No crash or restart happens during the floor test.

Not confirmed, leading hypothesis: worker contention from T-P1-4's new `catalog.renderDesignPreviews`
job (queue `render`, concurrency 2, `lockDuration: 120_000`, `src/lib/queues.ts:25,55`). It runs
inside `withTenant` and calls `imaging.preview()` synchronously **while the DB transaction is open**
(`src/modules/catalog/service.ts:341-359`) — already flagged as a backlog risk by T-P1-4's own
reviewer (wave.md line 69: "the job holds a DB transaction during the imaging call"). It fires on
every `design.updated` event, so the 2.1-minute web browser suite immediately before the floor
suite (same dev DB, worker and imaging process) could leave this backlog still draining when
`press.spec.ts` starts. I could not measure server-side timing without a live stack: production.scan
itself has zero references to `previewKey`/`designFiles`/`imaging.` (grep of
`src/modules/production/service.ts`), so T-P1-4 did not touch the scan path directly — any effect
would be indirect (shared imaging process / DB connections), not a defect in the scan code itself.

Owner: backend-engineer (catalog, T-P1-4) — move `imaging.preview()` out of the transaction (already
backlogged); backend-foundation — add duration logging around `production.scan` and the render job
so the next gate run can confirm or rule out contention directly.

Retry on fresh seed: diagnostic only, not a fix. If it passes, that confirms timing-dependent
contention (not an inherent logic defect), but the transaction-held-during-imaging-call pattern is
a real anti-pattern regardless of whether this one run collides with it — ship the instrumentation
fix before trusting a bare retry.

## Processes and data
No stack was started by me; nothing to stop. Dev DB untouched.
