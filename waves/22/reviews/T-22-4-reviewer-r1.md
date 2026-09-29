# Review of T-22-4 (round 1)

- Reviewer: reviewer on claude-opus-5-5 · Author: backend-engineer on claude-opus-5-5
- Verdict: **changes-required**
- Scope: contracts `0f2f413`; backend `08d1eba`, `1f39aaa` only (T-22-5 commits and uncommitted `finance/fees*` excluded). Ran on a `git archive 1f39aaa` copy, DB `invai_t22_4r`, Redis DB 10.

## Evidence I re-ran
| Command | Result |
|---|---|
| backend `pnpm typecheck && pnpm lint` (shared tree) + `tsc --noEmit`, `biome check .` (archive) | 0 errors; 413 / 411 files clean |
| `vitest run --reporter=dot src/modules/production src/modules/inventory src/db` | 23 files, 128 passed |
| contracts `pnpm test` | 8 files, 88 passed |
| `vitest run src/modules/finance/fees.test.ts` (archive, committed code) | 1 failed `expected 6 to be 8`: contracts `9e8ea0c` TikTok 6 vs committed finance; T-22-4 commits touch 0 finance files → not T-22-4 |
| `drizzle-kit generate` (archive) | "No schema changes"; `station_maintenance_events` RLS on, policy `_tenant`, composite FK `(company_id, station_id)` → stations |
| `scan-test-weakening.sh invai-backend 2466954` | 1 removed assertion, in T-22-5's uncommitted `fees.test.ts`; none in T-22-4 |
| scratch probes (deleted): P1 offline replay, P2 floor-session station, P3 4x concurrent start / 3x end | P1 **ok:true, pressed**; P2 blocked `station_maintenance`, wrong blank also blocked, after end `wrong_style` still blocks; P3 `[true,false,false,false]`, 1 row, 1 audit; ends `[true,false,false]` |
| API :3147 on a copy of dev DB (`/rpc/production/maintenance/*`) | packer@ start → 403 FORBIDDEN `production.maintenance`; office@ start ×2 → started true/false same id; end ×2 → ended true/false; audit started+ended, 2 outbox rows |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | suite "QC fail with under_cure/cracking…" green; `reprintStats`/`reasonsByWeek` group by stored reason |
| 2 | yes | queue/scan age tests green; warning only in extras, computed after the outcome, never blocks. `printedAt` coalesced with `receivedAt` (contract `transferPrintedAt`), not stamped: acceptable |
| 3 | **no** | live-window block, idempotency, audit, concurrency proven; offline replay of a scan made during a window is not blocked (finding 1) |
| 4 | yes | pick test shelf+bin; `getBlankLocations` filters `company_id` + RLS |
| 5 | backend yes; floor e2e at gate (QA) | cross-tenant NOT_FOUND start/end/scan, list empty, FK and WITH CHECK refusals green |

## Blocking findings
1. `invai-backend/src/modules/production/floor.ts:473` (with `maintenance.ts:63`) — the block checks only whether a window is open *now*, ignoring `input.scannedAt`, although the matcher already trusts `scannedAt` for offline replay (`matcher.ts:162`). Scenario (probe P1): Press 1 closed for calibration 10:00–10:30; the tablet is offline at 10:05 and a presser presses a shirt; the outbox syncs at 10:40 → `ok:true`, item `pressed`, blank consumed, no `station_maintenance` record. That is the case the tech lead and AC3 ("offline replay … parks it with that reason") require. Fix: block when a window is open now **or** one covers `scannedAt` (`started_at <= scannedAt and (ended_at is null or ended_at > scannedAt)`), and add a test with a past `scannedAt`.

## Checks
- [x] Only owned paths changed: production/inventory modules, their schema files, 0033 + meta; contracts is the granted cherry-pick
- [x] Scope: the cross-shop `stationId` → NOT_FOUND (was a composite-FK 500) is judged in scope. The new stationId read needs it, it follows the NOT_FOUND-for-foreign-ids rule, and it runs after the stored-result replay
- [x] Tests exercise behavior, none weakened (scan above)
- [x] Tenancy: `withTenant` on all 3 procedures, no new `withSystem` outside tests, `company_id`-leading indexes, partial unique on open window; idempotency proven; no money; strings are wave 23
- [x] Decisions: in report; none cross-cutting

## Optional notes (not blocking)
- `floor.ts:435` uses `nextActionFor(state)`; the contract says `nextAction: "press"`. They match at press. At a closed pick/pack station they differ: document or align.
