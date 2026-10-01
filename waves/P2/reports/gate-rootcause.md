# Gate root-cause: invai-floor `press.spec.ts:9` (P1 run 2, P2 run 2)

Author: qa-engineer. Reproduced live (own stack, dev DB untouched, not reset).

## Confirmed cause — layer: backend (rate limiter), owner: backend-foundation

Not a timeout, not offline-test leakage, not the imaging-contention hypothesis in
`invai-docs/waves/P1/reports/gate-rootcause.md` §2 (already ruled out by the new duration logs —
confirmed again here: every real `production.scan` logged 6–47 ms). **press.spec.ts fails even run
alone**, immediately after any other floor-suite run against the same seeded company — proving it
is independent of `offline.spec.ts`'s offline emulation, IndexedDB, service worker or storage state.

Trace evidence (`e2e/.e2e-out/invai-floor/results/press-*/trace.zip`, network trace): only **two**
`production/scan` requests exist for the whole test. The first (the wrong-style blank scan) got
**HTTP 429**, not a hang; the client's 10 s `AbortSignal.timeout` in `invai-floor/src/api/rpc.ts:43`
never fires here — the 429 is treated as `unavailable`/retryable by `toFailure` and
`countsAsAttempt` (`invai-floor/src/outbox/outbox.ts:95`), so `SyncEngine.flushOnce`
(`sync.ts:149-168`) reports `queued`, and `PressStation.runCheck` (`PressStation.tsx:77-84`) shows
the offline fallback — a real rate limit is mislabeled "offline" to the presser. A background
retry 3 s later (`sync.ts:200`, `backoffMs` starts at 3 000 ms) got 200, but nothing re-renders the
already-shown panel, and the test had already failed its assertion.

Root mechanism, confirmed by reading Redis directly after a fresh floor-suite run:
```
tb:writes:1f5d22c6-3527-4217-8417-caf5971cdd8e  tokens=5.79  (capacity 120, refill 2/s)
tb:reads:1f5d22c6-3527-4217-8417-caf5971cdd8e   tokens=299   (capacity 300, refill 5/s)
```
`bucketFor` (`invai-backend/src/api/orpc.ts:159-165`) buckets every non-GET procedure as `writes`:
`return method === "GET" ? "reads" : "writes";`. `files.downloadUrl` is **correctly** declared
`.route({ method: "POST", path: "/download-url" })` (`invai-contracts/src/contract/files.ts:24`,
a body param forces POST) but it is a pure read (thumbnail signed URLs,
`invai-floor/src/components/Thumbnail.tsx:30` → `fileUrl` → `files.downloadUrl` per queue item).
The trace shows **92** `files/downloadUrl` calls in this one test, all spent from the 120/min
`writes` bucket alongside the real mutations (station create, login, hold/release, scan, QC,
pack) from `floor.spec.ts` + `offline.spec.ts` + `press.spec.ts` sharing the same company. By the
time `press.spec.ts` makes its first real scan, the shared bucket is nearly empty and the request
is 429'd. `reads` (300/min) sits almost untouched, confirming nothing is wrongly read-classified
except this.

## Fix (for backend-foundation, not built here)

`bucketFor` must not infer rate-limit classification from REST `method`. Use the procedure's own
read/write intent instead — e.g. the existing permission suffix (`files.read` is already passed to
`proc()` at `invai-contracts/src/contract/files.ts:23`) or an explicit `meta.rateBucket` override,
so a safe, high-volume, POST-shaped read like `downloadUrl` lands in `reads`, not `writes`. Until
fixed, any floor or web screen that fetches several thumbnails per load will intermittently 429 a
real mutation right after it, anywhere in the golden path, not just this test.

## Why P1's instrumentation (T-P2-2) didn't surface this

The duration log added in `invai-backend/src/modules/production/router.ts:116-123` only logs scans
that *complete* on the server; a 429 is rejected one layer up by the `rateLimit` oRPC middleware
(`orpc.ts:169-178`), before `router.ts`'s handler runs, so it never appears as a `production.router
scan` line at all — which is exactly why the P1 log showed only fast, successful scans and no slow
one: the failing request was never logged server-side by design, not because it never arrived.

## Not the cause (ruled out)
- `offline.spec.ts` state (context/IndexedDB/service worker/`navigator.onLine`): reproduces with
  `press.spec.ts` run alone; Playwright gives each test a fresh incognito-like context by default
  (`invai-floor/playwright.config.ts` sets no shared `storageState`).
- Client RPC timeout / health probe / CORS / contract-version handshake: the failing request got a
  fast 429 response (4.7 ms), not a hang or a transport error.
- `press.spec.ts` itself: the test's assertions and scan sequence are correct; it is sensitive to
  how much write-bucket budget prior calls already spent against the same seeded company.

## Processes and data
Started (all stopped, confirmed via `lsof` after kill): invai-backend `pnpm dev:api` PID 29283,
`pnpm dev:worker` PID 29284; invai-floor `pnpm dev` PID 29319. Dev DB: not reset/reseeded, used
as-is per instructions. Valkey rate-limit keys were left to expire naturally (TTL ≈120 s); not
flushed manually.
