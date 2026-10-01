# Review of T-A9 (round 1)

- Reviewer: reviewer on opus. Author: backend-engineer on opus. Commit invai-backend `522433b`.
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` | exit 0 / 446 files clean |
| `REDIS_URL=…/13 vitest run digest today analytics src/db src/api/authz.test.ts` | 29 files, 226 passed, 2 skipped, 1 todo (first try: 3 red from another agent's concurrent full run on invai_test; green on re-run alone) |
| 10 perl mutants on detector edges (D9 ¢/n, D10 %/n, D11 dead/gap/cover, D12, D13 pace/fixed), scratch archive | 10/10 killed by `track-e.test.ts` |
| A1 tie test on the old sort (tiebreak removed) | red (1 failed); green on HEAD |
| Scratch probe (scenario co.) | bridge top mover exists ("Desert Bloom Logo"), so the AC-E1f DB test isn't vacuous; 3 concurrent builds → built/exists/exists, 1 set; concurrent double click → same `clickedAt`; `force` rebuild → prior click gone |
| `scan-test-weakening.sh invai-backend 3ebfbf8` | 0 assertions removed, no skips or mocks; the only hit is `if (!env.isTest)` around scheduler registration (same pattern as the alert scheduler) |
| Live API :3171 (Redis 13) | owner GET `/api/v1/today/actions` → 5 ranked actions, integer cents; office click ×2 → same `clickedAt`; `D99:nope` → 404 ACTION_NOT_FOUND; designer → 403 on both; anon → 401; date 09-29 and 12-31 → `generatedAt:null`, `actions:[]`, `steady:false` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1–5 D9–D13 | Yes | fires / doesn't-fire pairs at each edge; the mutants prove they bite. D9 also requires margin < 0 (disclosed; matches "loss") |
| 6 D2 = bridge mover | Yes | `actions.test.ts` DB test plus my non-vacuity probe; unmapped → no `designId` |
| 7 en/es, no buyer data | Yes | render test for en and es; params parse `DigestActionParams` (product/supplier fields only) |
| 8 ≤5, cents, steady, idempotent click | Yes | tests plus live |
| 9 RLS, isolation, FORBIDDEN | Yes | 3 tables `company_id` + tenant policy + RLS, composite FKs; B reads none, B's click on A's key → 404, FK 23503; 4 roles + vendor 403 |
| 10 AC-G1 digest leg | Yes | `snap.current.net === unitEconomics(order).totals.cm3`, non-zero |
| 11 run twice, purge, NOT_FOUND | Yes | job ×2 → `exists`, same rows; sweep lists until built; purge keeps < 90 d, cascades |
| 12 tie sort | Yes | red on the old sort, green now; the change stays in the granted line |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (digest/**, today/**, schema/digest.ts, drizzle 0038 + journal, finance-service one line + test)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; none were weakened
- [x] Tenancy (`withTenant` on request paths; the 3 `withSystem` calls are sweep/purge with reason comments), idempotency (set row guard, unique click), cents, en/es
- [x] Decisions recorded in the report (third table)

## Deviation from ruling 2 (judged)
- `today_action_sets`: accepted. It is needed as a "built" marker for steady days and to meet the S-26 `(company_id, id)` FK rule. Tenancy is not weakened.
- Clicks lost on `force` rebuild: acceptable **now**, because no production path passes `force` (not the job input, not the router). If a rebuild path is ever wired up, it should keep clicks: upsert on `(company_id, date, key)` and delete only keys that dropped out. Log that as a follow-up for whoever adds it.

## Optional notes (not blocking)
- A build that fails all 3 attempts keeps its jobId in Redis for 7 days, so the hourly sweep and the read can't re-enqueue it. The panel stays hidden that day (safe, but silent).
- Dev DB: my live run added one office click on Desert Bloom's 2026-09-30 set. Redis 13 was flushed (empty at start).
