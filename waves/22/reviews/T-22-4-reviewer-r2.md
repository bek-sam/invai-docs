# Review of T-22-4 (round 2)

- Reviewer: reviewer on claude-opus-5-5 · Author: backend-engineer on claude-opus-5-5 · Verdict: **approve**
- Scope: only the r1 fix, backend `03d780e` (`production/{maintenance.ts,floor.ts,maintenance.test.ts}`); T-22-5 files ignored. Ran on a `git archive 03d780e` copy, DB `invai_t22_4r2` (dropped after), Redis DB 10 (flushed).

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (backend) | tsc clean; biome 417 files, no fixes |
| `vitest run --reporter=dot src/modules/production` (archive) | 6 files, 47 passed |
| new test against parent `floor.ts`+`maintenance.ts` | FAILS `expected { ok: true … } to match { ok: false … }`; passes with fix |
| scratch probe (deleted): closed window [s,e), then live window | scannedAt=s blocked; =e pressed; live window + `2099-01-01`, -3h, `1970-01-01` all blocked `station_maintenance`, item `transfer_in` |
| `EXPLAIN` of the new query | Index Scan on `(company_id, station_id, started_at)`, cond company+station |
| `scan-test-weakening.sh invai-backend 03d780e~1` | no hits |

## Finding 1 (r1): fixed
`maintenance.ts:82` blocks when `ended_at is null` (independent of `scannedAt`, so a future/garbage time can't dodge a live window; `scannedAt` is `z.iso.datetime` in contracts) or `started_at <= scannedAt < ended_at` (half-open, sensible). Filters `company_id` explicitly under `withTenant`/RLS. Test proves blocked, item not pressed, 0 consume movements; after-window scan presses with 1 consume. AC3 now **met**. No blocking findings.

## Optional notes (not blocking)
- A pre-window `scannedAt` replayed while a later window is open is blocked (conservative; acceptable). r1 note on `nextActionFor` still stands.
