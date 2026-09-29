# Review of T-20-5 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-foundation on Fable 5.1
- Verdict: **changes-required**
- Commit reviewed: `invai-backend` 8fdc733 (HEAD has since moved to 8814acb, T-20-1's market test only; no overlap with this card's files)

## Evidence I re-ran
All runs used `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` → `invai_t20_rev5`, seeds on `invai_t20_rev5_seed` (both `DATABASE_URL` **and** `MIGRATION_DATABASE_URL` pointed at it, because `reset.ts` resets `MIGRATION_DATABASE_URL`), `SEED_OUTPUT_FILE` in my scratchpad.

**Redis DB deviation:** I used Redis DB 11, not DB 10. DB 10 held 66 keys from another agent, with a live client connected (`bull:reports:market-signals-*` jobs, `rt:company:*`, `tb:*`). Running `db:reset` there would have obliterated their queue jobs, and I may clean only keys I created. DB 11 had 0 keys and no clients when I started.

| Command | Result |
|---|---|
| `tsc --noEmit` | exit 0 |
| `biome check .` | `Checked 394 files ... No fixes applied.` |
| `vitest run src/db/reset.test.ts src/db/seed/outbox-hold.test.ts src/modules/tenancy/demo.test.ts src/modules/tenancy/demo-guards.test.ts src/db/rls-coverage.test.ts` (Redis 11) | `Test Files 5 passed (5)`, `Tests 33 passed (33)` |
| `scan-test-weakening.sh invai-backend 8fdc733^` | The only removed assertion is in `market.acceptance.test.ts` (commit 8814acb, T-20-1, not this card). This card's two test files are new and only add lines. |
| AC2 on Redis 11: 1 waiting and 1 delayed dummy per queue, a job scheduler, `rl:rev5:sentinel`, `ratelimit:rev5:sentinel`, `bullish:rev5` and a 2-entry stream `rt:company:rev5-proof`; then `tsx src/db/reset.ts` under `valkey-cli MONITOR` | `[reset] queues obliterated in /11: {"sync":2,"render":2,"ship":2,"ai":2,"reports":3}`. After: every queue 0, schedulers 0, only the 5 `bull:<q>:meta` keys left, `rl`=1, `ratelimit`=1, `bullish`=1, stream len 2. MONITOR: the reset client sent one `hello` on DB 0 (before `SELECT 11`) and every other command on DB 11. All 22 `DEL`s were on DB 11 and all targeted `bull:(sync\|render\|ship\|ai\|reports):*` (0 other keys). 0 `FLUSHDB`/`FLUSHALL`/`KEYS`/`SCAN`. |
| Run A: reset → migrate → worker on Redis 11 → `db:seed` | exit 0; `outbox released {"events":5188}`; `[seed] done {"orders":360,"items":694,"transitions":3927,"dueSoon":88,"seconds":45}`; 59/59 artwork, 4/4 sheets composed. Worker log 0 error lines; all 5 queues `failed: 0`. After the drain: `360\|694\|3927\|108 stock\|0 negative\|761 movements\|1 usage\|15 alerts`. |
| Run D: same, worker stopped | exit 0; `[seed] done {"orders":360,"items":694,"transitions":3927,...}`; `360\|694\|3927\|108\|0\|761\|1\|15`. Matches run A exactly. |
| Run C: reset → migrate → worker on 11 → `db:seed`, with `today.alertsSweep` enqueued after the orders phase (what the 5-minute scheduler does on its tick) | **seed exit 1**: `duplicate key value violates unique constraint "alerts_company_id_dedupe_key_index"`, `Key (company_id, dedupe_key)=(…, stock_low:…) already exists`, at `builder.ts:1522` (inventory phase). The sweep had written 108 `stock_low`, 35 `order_at_risk` and 13 `order_overdue` alerts at 00:35:05.784, 3 ms after the enqueue. All 5188 events were left held (never released). |
| `seed-out.json` vs shared `seed-output.json` shape | same top-level keys (`channels,counts,logins,pins,seconds,shopId,stationToken,vendorOrgId`) and counts keys. The shared file is untouched (mtime 10:08). |
| Cleanup | dropped `invai_t20_rev5`, `invai_t20_rev5_seed`; deleted every key in Redis 11 (it had held only my keys; 0 clients); my worker and seeds have exited. Shared dev DB `invai` and Redis DB 0 untouched. OrbStack restarted mid-review (not by me); I re-ran run D after it came back. |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | **No** | The outbox path is fixed: run A (worker running) equals run D (worker stopped) on every count, with 0 errors. The root cause is plausible from the code: `billing.recordSheetBuilt` upserts `usage` on `(company_id, period)` (`schema/billing.ts:88`), and the seed then inserts plainly. But the scheduled-sweep path still breaks the seed with a unique violation (run C, finding 1). The card's "no unique-violation (stock_levels **or any other**)" is not met, and the documented cause is incomplete. |
| 2 | Yes | MONITOR evidence above: only this app's `bull:<queue>:*` keys in the configured DB. `rl:`, `ratelimit:`, `rt:` and a lookalike `bullish:` key all survive, and no command ran on another DB apart from the connection `hello`. Uses `obliterate({force:true})` over `QUEUE_NAMES`, per A2. |
| 3 | Yes | Run A and run D: 59/59 artwork, 4/4 sheets, same output shape. Counts depend on the clock (the author disclosed this), so I compared runs from the same session: A = D. In runs B and C, imaging returned 500 on `/sample-art` partway through. The environment was unstable then (OrbStack went down minutes later), and imaging `/health` stayed ok. Run D after the restart was clean. |
| 4 | Yes | `stock_levels where available < 0` = 0 in runs A and D. |

## Blocking findings
1. `src/db/seed/builder.ts:1521` (`tx.insert(alerts)` for `stock_low`) and `builder.ts:~1609` (`tx.insert(alerts)` for `order_at_risk`): AC1 is still violated by the worker's **scheduled** jobs. The outbox hold covers only event-driven jobs. `today.alertsSweep` is registered with `upsertJobScheduler({ every: 5 min })` by both the worker and the API (`modules/today/jobs.ts:40-50`). In BullMQ 6.3 an `every` scheduler runs at once and then on every tick. The sweep fans out `generateAlerts` to every shop, the half-built one included, and `raiseAlert` upserts `stock_low:<variant>`, `order_at_risk:<order>` and `order_overdue:<order>` on `(company_id, dedupe_key)`. When a tick lands between the seed's orders phase and its inventory or final phase, the seed's plain insert fails. Reproduced in run C: `duplicate key value violates unique constraint "alerts_company_id_dedupe_key_index"`, seed exit 1, and all 5188 events stuck in the held state.
   - **Failure scenario:** the owner or the gate runs `db:reset && db:migrate && db:seed` with `dev:all` up. Restarting the API or worker re-registers the scheduler, so a seed of 25–100 s overlaps a 5-minute tick roughly 8–33% of the time. The seed then dies halfway, which is the same class of gate failure this card was meant to close.
   - **Suggested fix, inside owned paths:** make the seed's two `alerts` inserts idempotent (`onConflictDoUpdate`/`DoNothing` on `[alerts.companyId, alerts.dedupeKey]`, or call `raiseAlert`). An alert is the sweep's own output with the same key, so an upsert here hides nothing.
   - **Also check:** the other scheduled fan-outs that write per-company rows (`inventory/jobs.ts:63`, `finance/jobs.ts:135`, `billing/jobs.ts:55-60`, `shipping/jobs.ts:704-714`, `channels/jobs.ts:214-229`, `market/jobs.ts:577-582`, `orders/jobs.ts:118`) against the seed's plain inserts. List in the report which ones you checked, and update the root-cause section to name both paths (outbox and scheduled sweeps).
   - **Test:** add a regression test, for example run `generateAlerts` for the company between two builder phases, or seed a pre-existing `stock_low:` alert and show the builder completes.

## Checks
- [x] Only owned paths changed: `src/db/reset.ts` (+ test), `src/db/seed/**`, plus `README.md` and `src/modules/README.md` (the owner's own docs; the tech lead accepted them per the report and the review brief). No `package.json` change.
- [x] Nothing outside scope. `SEED_OUTPUT_FILE` serves the card's verification rule (never write `seed-output.json`).
- [x] No test weakened; both new test files only add lines. The new tests import new modules, so they fail on the base by construction. No test proves the builder actually calls `holdOutbox`; runs A and D cover that end to end.
- [x] Tenancy: `holdOutbox`/`releaseOutbox` filter by `company_id`. The demo path runs them under `withTenant`, which the test covers. No new tables and no new `withSystem` on a request path. Money, i18n: n/a.
- [x] Idempotency: release touches only rows carrying `HELD_MARKER`. Parked rows (`attempts >= 10`) are never released, and held rows (`attempts 0`) never appear in the DLQ view.
- [x] Nothing can flush other prefixes. `obliterate` deletes by the queue's own key structure (MONITOR shows only `bull:<q>:*` DELs); there is no `FLUSHDB`, `KEYS` or `SCAN` anywhere in the diff. It refuses under `NODE_ENV=production`.
- [x] Decisions: card-local; none needed.

## Optional notes (not blocking)
- **`reset.test.ts` wipes the Redis DB it runs on.** It obliterates all five queues, including job schedulers and delayed jobs. I proved this on Redis 11 with a stand-in "live" scheduler and a delayed ship job: both were gone after the file ran. Under plain `pnpm test`, `REDIS_URL` is `redis://localhost:6379` (DB 0, the dev worker's), so each run clears the dev worker's queues. This is not new: `sweeps.test.ts`, `queues.test.ts`, `internal.test.ts`, `outbox-relay.test.ts` and `fairness.test.ts` already obliterate `reports`, `render` and `ship` there. This file adds `sync` and `ai`. The author's follow-up (default test `REDIS_URL` to its own DB in `env.ts`) should be carded soon.
- If the seed fails after a phase commits, its events stay held forever (`dispatched_at` set, `attempts 0`), and the 7-day purge removes them silently. That is harmless for the seed (the next step is a reset) and for the demo (the company is retired). A one-line comment in `outbox-hold.ts` would save the next reader a trace.
- `[migrate] up to date (…)` prints right after a schema drop even though it applies every migration. The message is misleading but not this card's.
