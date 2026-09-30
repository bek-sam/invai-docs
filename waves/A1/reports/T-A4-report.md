# Report: T-A4 Operations and shipping analytics + `shipments.dest_zone`
Author: backend-engineer (production, shipping) on opus

## Progress
- 2026-09-30 migration `0037_shipping_dest_zone` committed `efdc193` (after T-A3's 0036).
- 2026-09-30 `zone.ts` + label-buy `dest_zone` + tests committed `d256a78` (7/7 on invai_ta4_test).
- 2026-09-30 operations-service + tests (incl. SQL parity) committed `6a5791c`.
- 2026-09-30 router line `operations` committed `2dce8f3` (after T-A3 `1afdfc3`, router.ts was clean); 15/15.
- 2026-09-30 01:00 local Docker/OrbStack hung (Valkey and Postgres stopped answering) during the full suite and the live analytics curl; stopped my processes; see gaps.

## Built
- `shipments.dest_zone smallint` nullable (invai-backend `src/db/schema/shipping.ts`, `drizzle/0037_shipping_dest_zone.sql` = one `ADD COLUMN`).
- Pure ZIP3 -> zone 1-9 (`src/modules/shipping/zone.ts`): regional ZIP3 centroids + USPS distance bands (50/150/300/600/1000/1400/1800 mi), 969 -> 9, APO/FPO/unknown -> null. Estimate (may be one zone off at a band edge): fine for grouping, never for pricing.
- `buyLabel` computes the zone from the from/ship-to ZIPs already in memory and `recordLabel` writes it in Tx 2; `toShipment` maps `destZone` (one line, needed for the contract field). No other shipping change.
- `analytics.operations` (`src/modules/analytics/operations-service.ts`, router line in `router.ts`): reprint cost by reason/station/vendor + rate, film waste and film use by vendor, waits per state (median/p90/still waiting) + bottleneck, press minutes per station vs the labor setting with the >25 % suggestion, late drivers with counts, `hasEnoughHistory`, `PERIOD_INVALID` (400) for reversed or >400-day periods.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC-A4 | yes | `zone.test.ts`: buy twice -> 1 carrier buy, `destZone` 8 (Phoenix->Brooklyn), military -> null, exact `shipments` column list + no zip/addr/street/city/name/phone/email column. Live: owner buy on mock carrier :3141 -> `labeled`, `destZone 7` (850->606), second buy same label, DB `labeled|7|1 label` |
| AC-B1 | yes | `operations-service.test.ts` hand-computed totals (1,200 cents/4 reprints/9.1 %, 13 sheets/10,100/78.8 %) and parity block running `reprint_cost.sql` + `film_waste_cost.sql` on the same data: equal |
| AC-B2 | yes | 120 timed units, median 2.00 vs setting 4 -> suggestion; 9 timed -> all null, no suggestion; setting 2.4 -> no suggestion |
| AC-B3 | yes | etsy 30 orders -> 20 %; amazon 10 -> counts only; labels are group names; test asserts no "caus" anywhere in the response |
| AC-B/C-screen1 | yes | new shop -> `hasEnoughHistory:false` plus per-metric nulls |
| AC-E4/E5 | yes | A vs B identical fixtures: A sees own totals, no B station/vendor id or name; designer/presser/packer/receiver -> FORBIDDEN `finance.read` via `call(router.analytics.operations)`; owner via router -> data |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-backend | `pnpm typecheck && pnpm lint` | tsc clean; biome 434 files, no fixes |
| invai-backend | `vitest run` zone + operations (TEST DB invai_ta4_test, Redis 9) | 7 passed; 15 passed |
| invai-backend | full `pnpm test` (twice) | **FAILED to run**: 00:57 run hung at `RUN v5.0.1` (Valkey `redis timeout`), stopped; 01:03 re-run `pnpm typecheck && pnpm lint && pnpm test` capped at 280 s -> typecheck + lint pass, vitest printed nothing after `RUN`, `EXIT 142` (killed by the cap). Valkey still gives no PONG. Gate must re-run |

## Exercised for real
- `pnpm db:migrate` on dev DB: already up to date (0037 applied), `dest_zone smallint` present.
- API :3141 (Redis DB 10, to not collide with my test run on 9): owner sign-in 200; `shipping.rates` + `shipping.buy` x2 on order #1454 -> above.
- `GET /api/v1/analytics/operations` curl as owner/designer: **not captured** (request hung with the Docker stack; API had also restarted on another agent's edit). Router path proven by the in-process `call()` tests instead.

## Decisions
- Waits: items not yet moved on are counted in `stillWaiting` and left out of median/p90 (contract text), unlike `stage_wait_hours.sql` which measures them to now(). Data-analyst may want the SQL aligned.
- Channel filter applies to reprints, items pressed, waits, press units (later scan of each gap) and late drivers; film waste ignores it (sheets have no channel).
- `hasEnoughHistory` = any metric reaches its minimum sample (no calendar "2 weeks" rule: imported history can be older than the shop).
- Reprint vendor cut: `in_house` (sheet without vendor), `unknown` (no original transfer); station cut `none` for no station.

## Known gaps and follow-ups
- Full suite and the live analytics curl must be re-run once local Docker is healthy (`orb stop && orb start` restarts every agent's services; I did not do it in a shared wave: tech lead's call).
- Cleanup pending for the same reason: drop DB `invai_ta4_test`, flush Redis DBs 9 and 10.
- Zone is an approximation of the USPS chart (documented in `zone.ts`).

## Blocked by other owners
- none (environment only, above)

## Processes and data
- API :3141 tsx watch PID 99229 + node 99238: stopped (port free). Background test run and curl tasks: stopped.
- Shared dev DB: migrated only (additive column); one mock label bought on seed order #1454. Not reset.

## Round 2 (review r1 fix)

Commit: `2e564af63c48cbb95ed407e0fbbd5c788935ac3e` "T-A4: stable tiebreak on sorted operations cuts (review r1)" (`invai-backend`, files `src/modules/analytics/operations-service.ts`, `src/modules/analytics/operations-service.test.ts` only).

- Blocking finding fixed: `operations-service.ts:141` `cut()` sort (drives `byReason`, `byStation`, `byVendor`) now ends with `|| a.key.localeCompare(b.key)`. Also fixed the same missing-tiebreak pattern at two more spots the review flagged checking: film-waste `byVendor` SQL `order by waste desc` -> `order by waste desc, coalesce(g.vendor_connection_id::text, '')` (~line 181), and `pressMinutes` SQL `order by 2` (station name, not unique) -> `order by 2, 1` (station id) (~line 284). Checked late-drivers and waits too: both already end their sort on a full, non-random tiebreak (`value.localeCompare` / fixed `WAIT_STATES` iteration order) — no change needed there.
- Added a new test, "reprint byReason keeps a stable order when two reasons tie (review r1)": two reprints on a fresh company, reasons `ghosting` and `color_off`, engineered to tie on cost (0) and count (1); asserts `color_off` sorts first across 4 repeated calls in the same run.
- Checks: `pnpm typecheck` clean; `pnpm lint` — biome 434 files, no fixes.
- `vitest run src/modules/analytics/operations-service.test.ts` x8 on `invai_ta4b_test` / `REDIS_URL=redis://localhost:6379/10`: **16/16 passed every run** (15 existing + 1 new tie test), no flakes.
- Cleanup: dropped `invai_ta4b_test` and the leftover `invai_ta4_test` (blocked in round 1 by the Docker hang); flushed Redis DBs 10 and 9.
- Not pushed; awaiting tech lead push after the gate.

## Round 2 addendum: full `pnpm test`

Post-commit gate check: `pnpm typecheck` and `pnpm lint` clean (own runs, no pipe, exit 0/0). Full `pnpm test` on `invai_ta4c_test` / Redis DB 11: `1 failed | 161 passed | 2 skipped (164 files)`, `1256 passed | 1 failed | 3 skipped | 1 todo` — the one failure is `src/db/seed/market-demand.test.ts` ("writes mock outside-demand rows and is a no-op on a second call"), timing out at the 30 s test limit under the full suite's 164 parallel workers. That file is in `src/db/seed/**` (backend-foundation's uncommitted WIP area per my task brief — not owned or touched by this card). Re-ran it alone on a fresh DB (`invai_ta4d_test` / Redis 12): passed in 19 s, confirming it's resource-contention under full-suite load, not a regression from this fix. `operations-service.test.ts` is among the 161 passing files (its tests are part of the 1256 passed). Cleanup: dropped `invai_ta4c_test` and `invai_ta4d_test`, flushed Redis DBs 11 and 12.
