# Review of T-3-3 (round 1)

- Reviewer: reviewer on Opus
- Author: backend-engineer (inventory) on Opus 5.5
- Verdict: approve

Scope: `invai-backend` commit `b8ac9d0` only ("Listings recorded and stock pushed to opted-in
channels"). Reviewed with fresh context (card, diff, author's report only).

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-r33 b8ac9d0` (node_modules symlinked) | clean checkout of the commit under review |
| `node_modules/.bin/tsc --noEmit -p .` | no errors |
| `node_modules/.bin/biome check .` | `Checked 239 files ... No fixes applied.` |
| `TEST_DATABASE_URL=…invai_test_r33 node_modules/.bin/tsx src/db/migrate.ts` | `[migrate] up to date` (confirms the card's claim of **no migration**) |
| `REDIS_URL=redis://localhost:6379/12 node_modules/.bin/vitest run` | **61 files, 431 tests passed** |
| `node_modules/.bin/tsup` (`pnpm build`) | `⚡️ Build success` |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-r33 97651a0` (parent commit, since `origin/main` is far behind the unpushed wave) | 0 assertions removed, 64 added; no `.skip`/`.only`; the only `vi.mock`/`mockImplementation` hits are on `integrations/channels` (the adapter boundary) and `lib/realtime` (the publish boundary) — never on the units under test (`availability.ts`, `sku.ts`, `ledger.ts`, `jobs.ts`); no test-only prod branches, no config loosening, no snapshot changes |
| API `PORT=3193` + worker, `DATABASE_URL=…invai_r33_copy` (`createdb -T invai`), `REDIS_URL=…/12`, mocks on | booted clean: `mocks: {ai,carrier,shopify,supplier,billing,mail: true}` |

### Exercised for real (evidence)
- Signed in as `owner@desertbloom.test`. `PATCH /api/v1/channels/{shopify-conn}` → `pushAvailability:true`.
- Found a mapped listing variant `DB025-G64000-SGR-S` (blank `92e18745-…`, `last_pushed_qty` null).
- `POST /api/v1/inventory/adjust` `qty:+3` on that blank (44 → 47 available, confirmed in
  `stock_levels`).
- Worker log, next 30 s window: `availability planned {"variants":1}` →
  `mock shopify availability {"items":[{"sku":"DB025-G64000-SGR-S","available":47}]}` →
  `availability pushed {"pushed":1,"skipped":0,"notFound":0,"failed":0}`. **One push, right
  quantity** (44+3=47). (An earlier window also fired, pushing 3 variants at their pre-existing
  quantities — that was residual state from before I flipped the opt-in on and adjusted stock,
  not double-counting my change; the window that covers my adjustment sent exactly one variant.)
- `qty:+2` then `qty:-2` on the same blank inside one window (47→49→47). Next window:
  `availability planned {"connections":0,"variants":0,"skippedConnections":0}` — **no
  `setAvailability` call**, confirmed by the log having no further `mock shopify availability`
  line.
- Refused case: signed in as `presser@desertbloom.test`, `PATCH /api/v1/channels/{id}` → `403
  FORBIDDEN "Missing permission channels.manage for channels.update"`.
- Cleaned up: stopped API (67569/67577) and worker (67641 + child), confirmed
  `lsof -iTCP:3193` empty; dropped `invai_r33_copy` and `invai_test_r33`; flushed Redis db 12;
  removed the worktree; `invai-backend/seed-output.json` untouched (backed up before the run,
  diffed identical after — no seed was run against the shared dev DB or this copy).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Listings recorded on import/map, seeded, tenant-scoped | Yes | `listings.test.ts`: import via `order.imported`, idempotent replay, manual map via `item.mapped`, rule save re-maps, backfill, and an explicit cross-tenant test (`recordListingsForItems` from another company's context sees and writes nothing). Seed hunk calls `recordListingsForCompany` under `withSystem`; migrate/tsc/tests confirm no migration needed (existing RLS'd columns) |
| 2. Availability math + concrete debounce | Yes | `pushQuantity` clamps negative available to 0 and negative/positive caps correctly (`availability.test.ts` unit cases); `planAvailability` sums `stock_levels.available` (already on-hand minus reserved) across every location before capping (test: 10+5 locations −3 reserved → 12, capped to 4); 30 s fixed-bucket debounce (`availabilityBucket`) verified live above and in tests (same bucket for changes 1s/20s apart, next bucket 30s later) |
| 3. Opt-in only, idempotent, last value stored | Yes | `canPushAvailability` re-checked once at plan time and again inside `pushAvailability`'s own transaction (a toggle-off between plan and push is caught, tested); idempotency key lives in the frozen job data and is reused on a thrown-error retry (test: same key sent twice, `lastPushedQty` unset until success); `not_found`/`failed` variants are never marked pushed, so they retry; live run above shows the exact opt-in → push → no-op cycle |
| 4. Realtime `stock.changed` | Yes | `ledger.ts`'s `stockChanged`/`afterCommit` batches one event per `(blankVariantId, locationId)` per transaction, sent only after commit (tested with 3 movements over 2 locations → 2 events, 0 on rollback). Payload `{blankVariantId, locationId, available}` matches `invai-contracts/src/realtime.ts:65` exactly (`Id, Id, z.number().int()`) |
| 5. Tests | Yes | 17 new tests across `availability.test.ts` and `listings.test.ts`, all passing, none weakened (scan above) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat b8ac9d0`): `db/seed/index.ts` (flagged out-of-scope
  by the author, correctly — see backend-foundation's co-review),
  `modules/channels/{sku.ts,listings.test.ts}`, `modules/inventory/{availability.ts,jobs.ts,ledger.ts,availability.test.ts}`.
  All match the card's owned globs or the card's explicit "seed if needed" allowance under AC1.
- [x] Nothing outside scope — no UI, no unrelated refactors.
- [x] Tests exercise the behavior; none weakened (scan above).
- [x] Tenancy: every new/changed function takes `companyId` and filters or uses `withTenant`;
  `listPushTargets`, `lastPushedQuantities`, `markAvailabilityPushed`, `upsertListings` all scope
  by `companyId`; `pushAvailability`'s pre-check re-selects the connection by `companyId` **and**
  `id` together (not just `id`), so a stale/cross-tenant connection id can't be pushed against.
  No new `withSystem` in a request path (the seed's `withSystem` call is the documented seed
  exception). Idempotency: keys frozen in job data, reused on retry, dedup checked before the
  channel call. Money: n/a (no cents here). No PII touched.
- [x] Decisions recorded where needed: decision 0003 (opt-in) is the gate this card implements;
  no new decision needed.

## Optional notes (not blocking)
- The known gaps the author already flagged are real and worth wave-4 follow-ups, not blockers
  here: opt-in flipping on doesn't push until the next stock change; `not_found` variants retry
  every window with no backoff/alert; two overlapping retried pushes to one connection could land
  out of order (self-correcting on the next window, per the author).
- `db/seed/index.ts`'s 5-line hunk is outside this card's owned paths; see
  `T-3-3-backend-foundation-r1.md` for that co-review.
