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
