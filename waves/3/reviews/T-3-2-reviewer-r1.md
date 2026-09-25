# Review of T-3-2 (round 1)

- Reviewer: reviewer on Opus
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran

Setup: `git -C invai-backend worktree add ../invai-backend-r32 b648cfd`, `node_modules` symlinked from `invai-backend`. Test DB `invai_test_r32`, `REDIS_URL=redis://localhost:6379/9`. DB copy `invai_r32_copy` via `docker exec local-postgres-1 createdb -U invai -T invai invai_r32_copy` (per instructions), API on `PORT=3192` plus a worker, `MOCK_CARRIER_TRANSIT_HOURS=0.001`.

| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit -p .` | exit 0, no output |
| `node_modules/.bin/biome check .` | "Checked 227 files in 144ms. No fixes applied." |
| `node_modules/.bin/vitest run` (`invai_test_r32`, redis db 9) | **53 files, 380 tests passed** |
| `node_modules/.bin/vitest run src/db/rls-coverage.test.ts src/api/authz.test.ts` | 2 files, 14 tests passed |
| `node_modules/.bin/tsup` (`pnpm build`) | "Build success", server.js + index.js built |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-r32 55725bf~1` | hits found, all read and non-blocking (below) |

Note: the DB copy, taken from the live shared dev DB, was **missing migration 0013** (`__drizzle_migrations` on `invai` stopped at the row for `0012_shipping_crash_safe`, despite the report's claim the shared DB was "already at 0013" — that must have been rolled back or reset by another wave-3 card's in-progress work since the report was written). I ran `tsx src/db/migrate.ts` against the copy, which applied `0013_carriers_webhook_events` cleanly (hash matched the file in this worktree) — an environment quirk, not a defect in this change. Flagging so the tech lead knows the shared dev DB's migration state is currently behind `main`.

### Exercised for real (own port, own DB copy)
Set shipment `e524c0ea-ce0a-4db4-b85e-785d9705909d` (`shp_mock_264`) to `labeled`/`packed`, posted signed EasyPost events with a small Node/curl script computing the real NFKD-normalized HMAC:

```
bad signature, in_transit               -> 401 {"error":"invalid signature"}
evt_r32_a in_transit 2026-09-24T10:00Z  -> 200 {"ok":true}; shipment labeled->in_transit, unit shipped
evt_r32_a replay                        -> 200 {"ok":true,"duplicate":true}
evt_r32_b delivered 2026-09-25T15:30Z   -> 200 {"ok":true}; shipment ->delivered, delivered_at set
evt_r32_c in_transit 2026-09-24T12:00Z (older than both) -> 200; status unchanged at delivered, event recorded "ignored"
```
`carrier_webhook_events` after: `evt_r32_a processed`, `evt_r32_b processed`, `evt_r32_c ignored / "older than the last applied tracker event"`. Redis job payload for `evt_r32_a` inspected directly: no `signed_by` or location field present, only normalized fields.

**Production guard:** started the API with `NODE_ENV=production ALLOW_MOCKS=true`, no `EASYPOST_WEBHOOK_SECRET` set, posted a mock-signed event to `/webhooks/easypost` → `404 {"error":"not found"}`, same for `/webhooks/easypost/anything`.

**Stuck-intent sweep, buy, read-back only:** staged two shipments in `buying` with `updated_at` 20 minutes old:
- carrier shipment id with no prior mock record → `retryStuckIntent(..., "buy")` returned `"resolved"`, final status `rated`, `tracking_code` still null. No S3/MinIO label object exists for that id.
- a second shipment stuck in `buying` (no matching mock record found for its carrier id either, since seed data doesn't go through the real adapter) → same outcome, `rated`, no buy.

I did not manage to reproduce the "carrier already sold it, read back completes it" path for real (seed data bypasses the real mock-carrier S3 records, so no genuine prior record existed to read back), but this exact path is covered by `jobs.test.ts` ("a buy the carrier sold but we never recorded is read back, never bought again"), which asserts `carrier.calls.buy` stays at **1** across the whole test even through the sweep retry — I read this test and the `buyLabel`/`readBackOnly` code path in `service.ts` (read-only for this card) and confirm the logic can never reach `adapter.buy()` when `readBackOnly` is set: it either finds the carrier's record (`found`) or settles back to `not_done`/`rated`; `adapter.buy(plan.req)` is only reached when `!found && !(plan.expired || opts.readBackOnly)`, which is impossible with `readBackOnly: true`.

## Acceptance criteria

| # | Met? | Evidence |
|---|---|---|
| 1 Webhook: HMAC first, dedupe, state mapping, forward-only | Yes | Real signed-event run above; `src/api/webhooks-carriers.test.ts`, `src/modules/shipping/jobs.test.ts` ("an older event never moves a shipment back") |
| 2 Tracker creation, daily poll | Yes | `easypost/index.ts` `ensureTracker`/`createEasypostTracking`; `jobs.test.ts` poll-sweep tests; code read |
| 3 Mock carrier unchanged, same state function | Yes | `applyTrackerUpdate` is the single entry point for webhook, poll and `mockTrackingJob`; full suite (incl. pre-existing T-2-5 tests) passes |
| 4 Stuck-intent sweep, buy never re-bought | Yes | Real exercise above + `service.ts` code path read + `jobs.test.ts` assertions on `carrier.calls.buy === 1` |
| 5 Error mapping (`rate_expired` narrowed, 429 no retry on buy/refund) | Yes | Read `easypostError`/`call()` in `easypost/index.ts`: `retry429` defaults to `method === "GET"`, so `buy()` and `void()` (both POST) never retry a 429; `RATE_EXPIRED_CODES` narrowed to the three documented codes |
| 6 Fetch-mocked tests | Yes | 36 new tests across 4 files, all passing; scan-test-weakening shows only additions (0 removed assertions) |

## Blocking findings

None.

## Checks
- [x] Only owned paths changed (`git show --stat` on both commits): `integrations/carriers/**`, new `api/webhooks-carriers.ts` + its one mount/guard hunk in `app.ts`, `modules/shipping/jobs.ts` (`service.ts` untouched, confirmed), a new `db/schema/carriers.ts` + migration `0013`, two lines in `env.ts`, tests. One extra line in `db/schema/index.ts` (backend-foundation's file, not on the card's owned-path list) — see the backend-foundation review file for the ownership call; I treat it as non-blocking given it's mechanical, necessary for `drizzle.config.ts` to see the new schema, transparently reported, and the identical pattern was used by T-3-1's own commit in this same wave for the same reason.
- [x] Nothing outside scope — every changed file serves an acceptance criterion.
- [x] Tests exercise the behavior, and none were weakened: `scan-test-weakening.sh` shows 0 removed assertions, 217 added, no `.skip`/`.only`, no deleted test files, no loosened config. The `vi.mock` hits are mocks of the carrier/channel adapters (dependencies), not of `jobs.ts` itself (the unit under test). The one "test-only branch" hit (`if (!env.isTest)` guarding scheduler registration in `jobs.ts`) is the same pattern used in 6 other `modules/*/jobs.ts` files already in the codebase — an established convention, not new weakening.
- [x] Tenancy (`withTenant`, RLS on new table): `carrier_webhook_events` has `tenantPolicy`, `.enableRLS()`, and `REVOKE INSERT, UPDATE, DELETE ... FROM invai_app` in the migration, verified live (`\dp carrier_webhook_events` on the DB copy shows `invai_app=r` only). `processCarrierEvent`/`applyTrackerUpdate` run inside `withTenant(target.companyId, ...)` with the shipment row locked; cross-tenant lookups (`findStuckIntents`, `trackerPollSweepJob`) correctly use `withSystem` for the ids-only fan-out, then `withTenant`/`systemContext(companyId)` for the actual per-company work — matches the pattern used elsewhere in this file (`pushReleasedJob`, etc.).
- [x] Idempotency: webhook dedupe on `(provider, event_id)` unique index with `onConflictDoNothing()` (DB-enforced, no TOCTOU); stuck buy is read-back only, never a second `adapter.buy()`; void reads the refund back first; push reuses T-2-5's safe-to-repeat path. Money: postage cents as integers, unaffected by this diff.
- [x] Decisions recorded where needed: schema follows decision 0009 exactly, plus two additive columns the author flagged explicitly for architect/backend-foundation to confirm (see their review files).

## Optional notes (not blocking)
- The `db/schema/index.ts` one-liner is backend-foundation's path per the operating system doc; it's a small, repeated, transparently-reported pattern (T-3-1 did the same this wave) — worth codifying as "new schema modules may add their own export line" rather than leaving it as an implicit exception every wave.
- `finishCarrierEvent` writes via `withSystem` (a separate connection/transaction) nested inside the outer `withTenant` transaction that applies the shipment state change. I traced the crash-window edge case (process death between the inner commit and the outer commit) and concluded it self-heals via BullMQ retry and never causes a backward state move or a double-apply — but it is a real atomicity gap between the dedupe/audit record and the state change, forced by `invai_app`'s revoked write access to the table. Worth a line in `modules/README.md` about the pattern for other system-only tables, not a fix.
- The shared dev DB being behind `main` on migrations (see Evidence) should be flagged to the tech lead outside this review.
